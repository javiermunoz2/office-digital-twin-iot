import os
import requests
import time
import pandas as pd
from sqlalchemy import create_engine
import json

# --- CONFIGURACIÓN ---
# Todas las credenciales se leen de variables de entorno (ver .env.example)
# 1. Datos de Thingsboard
TB_URL = os.getenv("TB_URL", "http://localhost:8080")  # Ojo: Si ejecutas este script DESDE DOCKER, usa "http://mytb:9090"
USERNAME = os.environ["TB_USERNAME"]
PASSWORD = os.environ["TB_PASSWORD"]
DEVICE_NAME = os.getenv("TB_DEVICE_NAME", "Sensor_Oficina_simulado")
KEYS = "temperature,humidity,co2"

# 2. Datos de la BBDD PostgreSQL
DB_USER = os.environ["ML_DB_USER"]
DB_PASS = os.environ["ML_DB_PASSWORD"]
DB_HOST = os.getenv("ML_DB_HOST", "localhost") # Si ejecutas desde Windows. Si es desde Docker usa "ml_db"
DB_PORT = os.getenv("ML_DB_PORT", "5432")
DB_NAME = os.getenv("ML_DB_NAME", "gemelo_datos")

# Cadena de conexión
DB_CONNECTION_STR = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_token():
    """Autenticación en Thingsboard"""
    url = f"{TB_URL}/api/auth/login"
    try:
        response = requests.post(url, json={"username": USERNAME, "password": PASSWORD})
        response.raise_for_status()
        return response.json()["token"]
    except Exception as e:
        print(f"Error al conectar con Thingsboard: {e}")
        return None

def get_device_id(token, name):
    """Busca el ID del dispositivo directamente por su nombre exacto"""
    headers = {"X-Authorization": f"Bearer {token}"}
    
    # CAMBIO 1: Usamos el parámetro 'deviceName' que es específico para esto.
    # Esto evita problemas de paginación y es más rápido.
    url = f"{TB_URL}/api/tenant/devices?deviceName={name}"
    
    response = requests.get(url, headers=headers)
    
    # Depuración rápida (puedes quitarla luego si quieres)
    print(f"DEBUG - Buscando: {name} | Status: {response.status_code}")

    if response.status_code == 200:
        res = response.json()
        # CAMBIO 2: La respuesta directa NO tiene la clave "data", 
        # devuelve el objeto dispositivo directamente.
        if "id" in res and "id" in res["id"]:
            return res["id"]["id"]
    elif response.status_code == 404:
        print(f"ERROR: El dispositivo '{name}' no existe en ThingsBoard.")
    else:
        print(f"ERROR: Fallo en la petición. Respuesta: {response.text}")
        
    return None

def download_and_store():
    print("--- INICIANDO PROCESO ETL ---")
    
    # 1. Conectar a Thingsboard
    token = get_token()
    if not token: return

    device_id = get_device_id(token, DEVICE_NAME)
    if not device_id:
        print(f"No se encontró el dispositivo: {DEVICE_NAME}")
        return

    print(f"Dispositivo encontrado: {device_id}")

    # 2. Definir rango de tiempo (Últimos 30 días)
    end_ts = int(time.time() * 1000)
    start_ts = end_ts - (30 * 24 * 60 * 60 * 1000)

    # 3. Descargar datos
    print("Descargando datos históricos...")
    headers = {"X-Authorization": f"Bearer {token}"}
    url = f"{TB_URL}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
    params = {"keys": KEYS, "startTs": start_ts, "endTs": end_ts, "limit": 50000}
    
    res = requests.get(url, headers=headers, params=params).json()

    # 4. Procesar JSON a Tabla (DataFrame)
    # Thingsboard devuelve: {'temp': [{'ts':1, 'value':20}], 'co2': [{'ts':1, 'value':400}]}
    # Hay que unirlo todo por la fecha (ts)
    
    data_frames = []
    for key, values in res.items():
        df_temp = pd.DataFrame(values)
        df_temp['ts'] = pd.to_datetime(df_temp['ts'], unit='ms') # Convertir fecha
        df_temp = df_temp.rename(columns={'value': key}) # Renombrar columna 'value' a 'temperature'
        df_temp = df_temp.set_index('ts')
        data_frames.append(df_temp)

    if not data_frames:
        print("No hay datos para exportar.")
        return

    # Unir todas las variables en una sola tabla
    df_final = pd.concat(data_frames, axis=1)
    df_final = df_final.reset_index() # Recuperar la fecha como columna
    
    print(f"¡Datos procesados! Filas obtenidas: {len(df_final)}")
    print(df_final.head()) # Mostrar las primeras filas

    # 5. Guardar en PostgreSQL
    print("Guardando en Base de Datos PostgreSQL...")
    try:
        engine = create_engine(DB_CONNECTION_STR)
        # 'if_exists="replace"' borra la tabla y la crea de nuevo. 
        # Usa "append" si quieres ir añadiendo datos nuevos cada día.
        df_final.to_sql('historico_sensores', engine, if_exists='replace', index=False)
        print("¡ÉXITO! Datos guardados en la tabla 'historico_sensores'")
    except Exception as e:
        print(f"Error al guardar en BBDD: {e}")

if __name__ == "__main__":
    download_and_store()

# CODIGO PARA AUTOMATIZAR LA EJECUCIÓN CADA X TIEMPO

'''import time
import schedule # Puedes instalarlo con: pip install schedule

# ... (todo tu código anterior de funciones get_token, save_to_db, etc.) ...

def job():
    """Esta función envuelve tu proceso principal"""
    print(f" Iniciando descarga programada: {datetime.now()}")
    download_and_store()

if __name__ == "__main__":
    # Configuración de la automatización
    print("--- SERVICIO DE EXPORTACIÓN INICIADO ---")
    
    # Opción 1: Ejecutar inmediatamente al arrancar
    job()
    
    # Opción 2: Programar para que se repita cada X tiempo
    # Ejemplo: Ejecutar cada 1 hora
    schedule.every(1).hours.do(job)
    
    # O si prefieres cada 5 minutos para probar:
    # schedule.every(5).minutes.do(job)

    # Bucle infinito que mantiene el script "vivo"
    while True:
        schedule.run_pending()
        time.sleep(60) # Revisa si toca trabajar cada minuto'''