import os
import requests

# 1. Configuración de datos (Usando Variables de Entorno)
# Estas variables NO se escriben aquí, se configuran en GitHub
servidor = "http://reportes.uan.edu.co/jasperserver"
usuario = os.getenv("UAN_USER")
clave = os.getenv("UAN_PASS")
webhook_chat = os.getenv("GOOGLE_CHAT_WEBHOOK")

ruta_reporte = "REPORTES_UAN/DATOS_POBLACIONALES/DOCENTES/LISTADOS/Materias_y_actividades_de_docentes_detallado"
formato = "xlsx" 
parametros = {
    'ano': '2026',    
    'periodo': '1'    
}

def enviar_notificacion_chat(mensaje):
    if webhook_chat:
        requests.post(webhook_chat, json={"text": mensaje})

def descargar_reporte_uan():
    if not usuario or not clave:
        print("❌ Error: No se encontraron las credenciales en el entorno.")
        return

    sesion = requests.Session()
    url_login = f"{servidor}/rest/login"
    datos_login = {
        'j_username': usuario,
        'j_password': clave
    }

    try:
        print(f"Iniciando sesión para el año {parametros['ano']}...")
        respuesta_login = sesion.post(url_login, data=datos_login)
        
        if respuesta_login.status_code == 200:
            print("✅ Conexión exitosa.")
            url_descarga = f"{servidor}/rest_v2/reports/{ruta_reporte}.{formato}"
            
            print("Generando Excel detallado...")
            respuesta_reporte = sesion.get(url_descarga, params=parametros)
            
            if respuesta_reporte.status_code == 200:
                nombre_archivo = f"reporte_docentes_{parametros['ano']}_{parametros['periodo']}.xlsx"
                
                with open(nombre_archivo, "wb") as archivo:
                    archivo.write(respuesta_reporte.content)
                
                print(f"⭐ ¡Logrado! Archivo guardado como: {nombre_archivo}")
                enviar_notificacion_chat(f"✅ Reporte UAN generado con éxito: {nombre_archivo}")
            else:
                msg = f"❌ Error en el reporte (Código {respuesta_reporte.status_code})"
                print(msg)
                enviar_notificacion_chat(msg)
        else:
            print(f"❌ Error de acceso: Revisa usuario o clave.")
            enviar_notificacion_chat("❌ Error de acceso a UAN: Revisa credenciales.")
            
    except Exception as e:
        print(f"⚠️ Error de red: {e}")
        enviar_notificacion_chat(f"⚠️ Error de red en el script: {e}")

if __name__ == "__main__":
    descargar_reporte_uan()