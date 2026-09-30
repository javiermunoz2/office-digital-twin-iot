#include "red.h"
#include "config.h"
#include <WiFi.h>
#include <HTTPClient.h>

void iniciarWiFi() {
  Serial.print("[INFO] Conectando a WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA); // Modo Estación explícito
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  int retryCount = 0;
  while (WiFi.status() != WL_CONNECTED && retryCount < 20) {
    delay(500);
    Serial.print(".");
    retryCount++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[INFO] WiFi Conectado.");
    Serial.print("[INFO] IP Asignada: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WARN] Fallo WiFi inicial. Se reintentará en el loop.");
  }
}

// Solo intenta reconectar si REALMENTE se ha perdido, sin forzar desconexión
void mantenerWiFi() {
    if (WiFi.status() != WL_CONNECTED) {
       Serial.println("[ERROR] WiFi perdido. Intentando reconectar...");
       WiFi.reconnect();
       // Damos un pequeño margen para que negocie
       delay(500); 
    }
}

void enviarDatos(float temp, float hum, int co2, int gas, float ruido, bool sensorListo) {
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      String url = String(TB_SERVER_URL) + String(TB_TOKEN) + "/telemetry";
      
      http.begin(url);
      http.addHeader("Content-Type", "application/json");
      http.setTimeout(3000); // Timeout de 3s para no bloquear si el servidor cae

      // --- CREACIÓN DE JSON EFICIENTE (Sin Strings) ---
      char jsonBuffer[200]; // Buffer estático suficiente para tus datos

      if (sensorListo) {
        // Formato con todos los datos
        snprintf(jsonBuffer, sizeof(jsonBuffer), 
          "{\"gas\":%d, \"ruido\":%.2f, \"temperature\":%.2f, \"humidity\":%.2f, \"co2\":%d}", 
          gas, ruido, temp, hum, co2);
      } else {
        // Formato si el SCD41 falla (solo gas y ruido)
        snprintf(jsonBuffer, sizeof(jsonBuffer), 
          "{\"gas\":%d, \"ruido\":%.2f}", 
          gas, ruido);
      }
      
      // Enviamos el buffer char directamente
      int httpResponseCode = http.POST(jsonBuffer);
      
      if(httpResponseCode > 0){
        Serial.printf("[NET] Envio Exitoso (%d). Payload: %s\n", httpResponseCode, jsonBuffer);
      } else {
        Serial.printf("[ERROR] Fallo envio HTTP: %s\n", http.errorToString(httpResponseCode).c_str());
      }
      http.end();
    } else {
        Serial.println("[ERROR] No hay internet para enviar datos.");
    }
}
