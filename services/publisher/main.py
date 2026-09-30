import os
import csv
import time
import json
import paho.mqtt.client as mqtt

# --- CONFIGURACIÓN ---
MQTT_HOST = os.getenv("MQTT_HOST", "mytb") # Apunta al nombre del servicio en docker
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = "v1/devices/me/telemetry" # ESTO ES FIJO EN THINGSBOARD
MQTT_TOKEN = os.getenv("MQTT_ACCESS_TOKEN", "") # Leemos el token de la variable de entorno
CSV_PATH = os.getenv("CSV_PATH", "/app/data/dataset.csv")
PUBLISH_INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "60")) 

def load_rows(path: str):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            print("El CSV está vacío.")
            return []
        print(f"Cargadas {len(rows)} filas desde {path}")
        return rows
    except FileNotFoundError:
        print(f"ERROR: No se encuentra el archivo en {path}")
        return []

'''def make_payload(row: dict) -> str:
    # ... (parte anterior del código igual) ...
    norm = {k.lower(): v for k, v in row.items()}

    def to_float(value):
        try:
            val_clean = str(value).replace(',', '.')
            return float(val_clean) if value not in (None, "") else None
        except ValueError:
            return None
            
    # --- TRAMPA PARA PROBAR ALARMAS ---
    # Leemos el valor real
    co2_real = to_float(norm.get("co2"))
    
    # Si la temperatura es > 22 (que es común), forzamos un pico de CO2
    # Esto es solo para ver si Thingsboard se pone rojo
    temp_val = to_float(norm.get("temperature"))
    
    if temp_val and temp_val > 22.0:
        co2_final = 1500.0  # ¡Peligro simulado!
    else:
        co2_final = co2_real
    # ----------------------------------

    final_payload = {
        "temperature": temp_val,
        "humidity": to_float(norm.get("humidity")),
        "co2": co2_final, # Usamos nuestro valor trucado
        "ruido": to_float(norm.get("ruido"))
    }
    
    # Limpieza de nulos
    final_payload = {k: v for k, v in final_payload.items() if v is not None}
    
    return json.dumps(final_payload)'''
def make_payload(row: dict) -> str:
    # Normalizar claves a minúsculas
    norm = {k.lower(): v for k, v in row.items()}

    def to_float(value):
        try:
            val_clean = str(value).replace(',', '.')
            return float(val_clean) if value not in (None, "") else None
        except ValueError:
            return None

    # 1. Intentamos leer todo lo posible
    raw_payload = {
        "temperature": to_float(norm.get("temperature")),
        "humidity": to_float(norm.get("humidity")),
        "co2": to_float(norm.get("co2")),
        "ruido": to_float(norm.get("ruido")), 
        "voc": to_float(norm.get("voc"))
    }

    # 2. LIMPIEZA: Filtramos y quitamos las claves que sean None (vacías)
    # Así, si "ruido" no está en el CSV, esa clave desaparece del JSON
    final_payload = {k: v for k, v in raw_payload.items() if v is not None}
    
    return json.dumps(final_payload)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("--- CONECTADO EXITOSAMENTE A THINGSBOARD ---")
    else:
        print(f"--- ERROR DE CONEXIÓN: Código {rc} ---")
        print("Revisa que el TOKEN sea correcto y el servidor accesible.")

def main():
    if not MQTT_TOKEN:
        print("ERROR: No se ha configurado el MQTT_ACCESS_TOKEN en el docker-compose")
        return

    rows = load_rows(CSV_PATH)
    if not rows: return

    # Configuración del cliente MQTT
    client = mqtt.Client(client_id="Python_Simulator_Client")
    
    # --- AQUÍ ESTÁ LA CLAVE: EL TOKEN ES EL USUARIO ---
    client.username_pw_set(username=MQTT_TOKEN) 
    
    client.on_connect = on_connect
    
    print(f"Conectando a {MQTT_HOST}:{MQTT_PORT}...")
    
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    except Exception as e:
        print(f"No se pudo conectar al servidor: {e}")
        return

    client.loop_start()

    try:
        while True:
            for row in rows:
                payload = make_payload(row)
                print(f"Enviando datos: {payload}")
                
                info = client.publish(MQTT_TOPIC, payload, qos=1)
                info.wait_for_publish()
                
                # Esperamos X segundos antes del siguiente dato
                time.sleep(PUBLISH_INTERVAL)
                
    except KeyboardInterrupt:
        print("Deteniendo simulador...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()