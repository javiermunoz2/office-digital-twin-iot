#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// Copia este fichero como config.h y rellena tus datos.
// config.h esta en .gitignore: nunca subas credenciales al repositorio.

// ================= RED Y SERVIDOR =================
#define WIFI_SSID       "TU_WIFI"
#define WIFI_PASS       "TU_PASSWORD"
#define TB_TOKEN        "TOKEN_DEL_DISPOSITIVO_THINGSBOARD"

// Endpoint HTTP de ThingsBoard (IP o hostname mDNS del servidor)
#define TB_SERVER_URL   "http://thingsboard.local:8080/api/v1/"

static const unsigned long INTERVALO_ENVIO = 30000;

// ================= HARDWARE =================
static const int PIN_GAS = 34;

// Configuración I2S (Micrófono)
#define I2S_WS 15
#define I2S_SD 32
#define I2S_SCK 14
#define I2S_PORT I2S_NUM_0
#define BUFFER_LEN 64

#endif
