import os
import requests

# 1. Configuración de datos desde Secrets
servidor = "http://reportes.uan.edu.co/jasperserver"
usuario = os.getenv("UAN_USER")
clave = os.getenv("UAN_PASS")
webhook_chat = os.getenv("GOOGLE_CHAT_WEBHOOK")

# Ruta exacta de tu Jupyter
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
        print("❌ Error: Faltan credenciales.")
        return

    sesion = requests.Session()
    # Mantenemos el disfraz de navegador (indispensable en GitHub)
    sesion.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    })

    # 1. Autenticación (Tal cual tu Jupyter)
    url_login = f"{servidor}/rest/login"
    datos_login = {
        'j_username': usuario,
        'j_password': clave
    }

    try:
        print(f"Iniciando sesión para {usuario}...")
        respuesta_login = sesion.post(url_login, data=datos_login)
        
        if respuesta_login.status_code == 200:
            print("✅ Conexión exitosa.")
            
            # 2. Descarga (Limpiamos posibles espacios en la ruta)
            ruta_limpia = ruta_reporte.strip()
            url_descarga = f"{servidor}/rest_v2/reports/{ruta_limpia}.{formato}"
            
            print("Generando Excel... esto puede tardar.")
            # IMPORTANTE: params=parametros construye el ?ano=2026&periodo=1 automáticamente
            respuesta_reporte = sesion.get(url_descarga, params=parametros)
            
            if respuesta_reporte.status_code == 200:
                nombre_archivo = f"reporte_docentes_{parametros['ano']}_{parametros['periodo']}.xlsx"
                with open(nombre_archivo, "wb") as archivo:
                    archivo.write(respuesta_reporte.content)
                
                print(f"⭐ ¡Logrado! Archivo guardado.")
                enviar_notificacion_chat(f"✅ Reporte UAN 2026-1 generado con éxito.")
            else:
                # Si vuelve a dar 400, este mensaje en el chat nos dirá POR QUÉ
                detalle = respuesta_reporte.text[:100]
                msg = f"❌ Error {respuesta_reporte.status_code} al descargar reporte.\nDetalle: {detalle}"
                print(msg)
                enviar_notificacion_chat(msg)
        else:
            print(f"❌ Error de acceso: Status {respuesta_login.status_code}")
            enviar_notificacion_chat("❌ Error de acceso: Revisa credenciales en los Secrets.")
            
    except Exception as e:
        print(f"⚠️ Error: {e}")
        enviar_notificacion_chat(f"⚠️ Error de red: {e}")

if __name__ == "__main__":
    descargar_reporte_uan()
