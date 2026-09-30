#include <Arduino.h>
#include "config.h"
#include "sensores.h"
#include "red.h"

// Variables Globales
float g_currentTemp = 0.0;
float g_currentHum = 0.0;
uint16_t g_currentCO2 = 0;
bool g_scdDataReady = false;

unsigned long g_lastSendTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("[INFO] Sistema Iniciado (Optimizado)");

  // 1. Iniciamos Hardware
  iniciarHardware();

  // 2. Iniciamos Red
  iniciarWiFi();
}

void loop() {
  // --- TAREA A: Leer SCD41 (No bloqueante) ---
  // El sensor se actualiza cada 5s internamente. Solo guardamos si hay dato nuevo.
  if (leerSCD4x(g_currentTemp, g_currentHum, g_currentCO2)) {
      g_scdDataReady = true;
  }

  // --- TAREA B: Telemetría ---
  if (millis() - g_lastSendTime > INTERVALO_ENVIO) {
    g_lastSendTime = millis();

    // Verificamos WiFi antes de leer nada para asegurar
    mantenerWiFi();

    // Lecturas instantáneas
    int valGas = leerGasFiltrado();
    float valRuido = leerRuidoDB();

    // Log por puerto serie
    Serial.println("\n[REPORT] --- Ciclo Telemetria ---");
    Serial.printf("Gas: %d\n", valGas);
    Serial.printf("Ruido: %.2f dB\n", valRuido);
    
    if (g_scdDataReady) {
       Serial.printf("SCD41 -> T: %.2f C, H: %.2f %%, CO2: %d ppm\n", g_currentTemp, g_currentHum, g_currentCO2);
    } else {
       Serial.println("[WARN] SCD41 sin datos nuevos aun.");
    }

    // Enviar (Función optimizada sin Strings)
    enviarDatos(g_currentTemp, g_currentHum, g_currentCO2, valGas, valRuido, g_scdDataReady);
  }
}
