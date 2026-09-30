import os
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC_FILTER = os.getenv("MQTT_TOPIC_FILTER", "oficina/#")


def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker MQTT con código rc={rc}")
    print(f"Suscribiéndose a: {MQTT_TOPIC_FILTER}")
    client.subscribe(MQTT_TOPIC_FILTER)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
    except UnicodeDecodeError:
        payload = str(msg.payload)
    print(f"[{msg.topic}] {payload}")


def main():
    client = mqtt.Client(client_id="ingestor")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    print(f"Conectando a MQTT en {MQTT_HOST}:{MQTT_PORT}...")
    client.loop_forever()


if __name__ == "__main__":
    main()
