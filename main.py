import os
import requests

# 1. Configuración de datos desde Secrets de GitHub
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
        try:
            requests.post(webhook_chat, json={"text": mensaje}, timeout=10)
        except Exception as e:
            print(f"Error enviando al chat: {e}")

def descargar_reporte_uan():
    if not usuario or not clave:
        print("❌ Error: No se encontraron las credenciales en los Secrets.")
        return

    # Creamos la sesión y le ponemos el "disfraz" de navegador
    sesion = requests.Session()
    sesion.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webkit,p-quality=8'
    })

    url_login = f"{servidor}/rest/login"
    datos_login = {
        'j_username': usuario,
        'j_password': clave
    }

    try:
        print(f"Iniciando sesión en UAN para {usuario}...")
        # Enviamos el login
        respuesta_login = sesion.post(url_login, data=datos_login, timeout=15)
        
        # Verificamos si la respuesta es 200 OK
        if respuesta_login.status_code == 200:
            print("✅ Conexión exitosa.")
            
            url_descarga = f"{servidor}/rest_v2/reports/{ruta_reporte}.{formato}"
            print("Generando Excel detallado... (esto puede tardar)")
            
            # Pedimos el reporte usando la sesión autenticada
            respuesta_reporte = sesion.get(url_descarga, params=parametros, timeout=60)
            
            if respuesta_reporte.status_code == 200:
                nombre_archivo = f"reporte_docentes_{parametros['ano']}_{parametros['periodo']}.xlsx"
                
                with open(nombre_archivo, "wb") as archivo:
                    archivo.write(respuesta_reporte.content)
                
                print(f"⭐ ¡Logrado! Archivo guardado como: {nombre_archivo}")
                enviar_notificacion_chat(f"✅ Reporte UAN generado con éxito para el año {parametros['ano']}-{parametros['periodo']}")
            else:
                msg = f"❌ Error al descargar reporte: Código {respuesta_reporte.status_code}"
                print(msg)
                enviar_notificacion_chat(msg)
        else:
            print(f"❌ Error de acceso (Status {respuesta_login.status_code}). Revisa que los Secrets no tengan espacios.")
            enviar_notificacion_chat(f"❌ Fallo de autenticación en UAN (Status {respuesta_login.status_code})")
            
    except Exception as e:
        error_msg = f"⚠️ Error inesperado: {str(e)}"
        print(error_msg)
        enviar_notificacion_chat(error_msg)

if __name__ == "__main__":
    descargar_reporte_uan()
