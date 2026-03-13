import os
import requests
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. CONFIGURACIÓN DE VARIABLES (Vienen de los Secrets de GitHub)
servidor = "http://reportes.uan.edu.co/jasperserver"
usuario = os.getenv("UAN_USER")
clave = os.getenv("UAN_PASS")
webhook_chat = os.getenv("GOOGLE_CHAT_WEBHOOK")
gdrive_creds_json = os.getenv("GDRIVE_CREDENTIALS")

# ID de la carpeta que me pasaste
ID_CARPETA_DESTINO = '1bF_FvqB3bELltO5pkAxc4i9hGy31Gytl'

ruta_reporte = "REPORTES_UAN/DATOS_POBLACIONALES/DOCENTES/LISTADOS/Materias_y_actividades_de_docentes_detallado"
formato = "xlsx"
parametros = {
    'ano': '2026',
    'periodo': '1'
}

def enviar_notificacion_chat(mensaje):
    if webhook_chat:
        requests.post(webhook_chat, json={"text": mensaje})

def subir_a_drive_y_obtener_link(nombre_archivo):
    try:
        # Autenticación con el JSON de la cuenta de servicio
        creds_dict = json.loads(gdrive_creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        service = build('drive', 'v3', credentials=creds)

        # Metadatos: Aquí le decimos que el "padre" es tu carpeta para evitar el Error 403
        file_metadata = {
            'name': nombre_archivo,
            'parents': [ID_CARPETA_DESTINO]
        }
        
        media = MediaFileUpload(
            nombre_archivo, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            resumable=True
        )
        
        # Subir el archivo
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        # Cambiar permisos para que puedas ver el archivo con el link
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        return f"Error al subir a Drive: {str(e)}"

def descargar_reporte_uan():
    if not usuario or not clave or not gdrive_creds_json:
        print("❌ Error: Faltan variables de entorno (Secrets).")
        return

    sesion = requests.Session()
    # El "disfraz" para que la UAN no nos bloquee
    sesion.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    })

    try:
        print(f"Iniciando sesión en UAN para {usuario}...")
        res_login = sesion.post(f"{servidor}/rest/login", data={'j_username': usuario, 'j_password': clave})
        
        if res_login.status_code == 200:
            print("✅ Conexión UAN exitosa.")
            
            url_descarga = f"{servidor}/rest_v2/reports/{ruta_reporte}.{formato}"
            print("Descargando reporte...")
            res_rep = sesion.get(url_descarga, params=parametros)
            
            if res_rep.status_code == 200:
                nombre_local = f"reporte_docentes_{parametros['ano']}_{parametros['periodo']}.xlsx"
                
                with open(nombre_local, "wb") as f:
                    f.write(res_rep.content)
                
                print("Subiendo a Google Drive...")
                link_final = subir_a_drive_y_obtener_link(nombre_local)
                
                if "http" in link_final:
                    enviar_notificacion_chat(f"⭐ ¡Reporte generado! Accede aquí: {link_final}")
                else:
                    enviar_notificacion_chat(f"❌ Reporte descargado pero falló la subida a Drive: {link_final}")
            else:
                enviar_notificacion_chat(f"❌ Error UAN al generar reporte (Código {res_rep.status_code})")
        else:
            enviar_notificacion_chat("❌ Error de acceso a UAN: Revisa credenciales.")
            
    except Exception as e:
        enviar_notificacion_chat(f"⚠️ Error crítico en el script: {str(e)}")

if __name__ == "__main__":
    descargar_reporte_uan()
