import os
import requests
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuración
servidor = "http://reportes.uan.edu.co/jasperserver"
usuario = os.getenv("UAN_USER")
clave = os.getenv("UAN_PASS")
webhook_chat = os.getenv("GOOGLE_CHAT_WEBHOOK")
gdrive_creds_json = os.getenv("GDRIVE_CREDENTIALS")

ruta_reporte = "REPORTES_UAN/DATOS_POBLACIONALES/DOCENTES/LISTADOS/Materias_y_actividades_de_docentes_detallado"
formato = "xlsx"

def subir_a_drive_y_obtener_link(nombre_archivo):
    # Autenticación con Google Drive
    creds_dict = json.loads(gdrive_creds_json)
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    service = build('drive', 'v3', credentials=creds)

    # Subir archivo
    metadata = {'name': nombre_archivo}
    media = MediaFileUpload(nombre_archivo, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file = service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
    
    # Dar permiso para que cualquiera con el link lo vea (puedes ajustarlo)
    service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'viewer'}).execute()
    
    return file.get('webViewLink')

def descargar_reporte_uan():
    sesion = requests.Session()
    sesion.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    try:
        # 1. Login
        res_login = sesion.post(f"{servidor}/rest/login", data={'j_username': usuario, 'j_password': clave})
        if res_login.status_code == 200:
            # 2. Descarga
            url_desc = f"{servidor}/rest_v2/reports/{ruta_reporte}.{formato}"
            res_rep = sesion.get(url_desc, params={'ano': '2026', 'periodo': '1'})
            
            if res_rep.status_code == 200:
                nombre = "reporte_uan.xlsx"
                with open(nombre, "wb") as f:
                    f.write(res_rep.content)
                
                # 3. Subir a Drive y enviar Link al Chat
                link = subir_a_drive_y_obtener_link(nombre)
                requests.post(webhook_chat, json={"text": f"✅ Reporte listo! Descárgalo aquí: {link}"})
                print("Proceso completo.")
    except Exception as e:
        requests.post(webhook_chat, json={"text": f"⚠️ Error: {e}"})

if __name__ == "__main__":
    descargar_reporte_uan()
