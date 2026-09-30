#include "sensores.h"
#include "config.h"
#include <Wire.h>
#include <SparkFun_SCD4x_Arduino_Library.h> 
#include <driver/i2s.h>
#include <math.h>

SCD4x airSensor;

// --- Funciones internas I2S ---
void i2s_install() {
  const i2s_config_t i2s_config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 44100,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT, 
    .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_I2S | I2S_COMM_FORMAT_I2S_MSB),
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = BUFFER_LEN,
    .use_apll = false
  };
  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
}

void i2s_setpin() {
  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = -1,
    .data_in_num = I2S_SD
  };
  i2s_set_pin(I2S_PORT, &pin_config);
}

// --- Implementación Pública ---

void iniciarHardware() {

  // 1. SCD41
  Wire.begin(); 
  if (airSensor.begin() == false) {
    Serial.println("[ERROR] Sensor SCD41 no detectado.");
  } else {
    Serial.println("[INFO] Sensor SCD41 inicializado.");
    airSensor.stopPeriodicMeasurement(); 
    delay(500);
    airSensor.startPeriodicMeasurement(); 
  }
  
  // 2. I2S Audio
  i2s_install();
  i2s_setpin();
  i2s_start(I2S_PORT);
  Serial.println("[INFO] Audio I2S iniciado.");
}

int leerGasFiltrado() {
  long sum = 0;
  int samples = 50;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(PIN_GAS);
    delay(2);
  }
  return (int)(sum / samples);
}

float leerRuidoDB() {
    int16_t sBuffer[BUFFER_LEN];
    size_t bytesIn = 0;
    float maxMean = 0;
    for(int j=0; j<10; j++) { 
        esp_err_t result = i2s_read(I2S_PORT, &sBuffer, BUFFER_LEN * sizeof(int16_t), &bytesIn, portMAX_DELAY);
        if (result == ESP_OK) {
            float mean = 0;
            for (int i = 0; i < BUFFER_LEN; i++) { mean += abs(sBuffer[i]); }
            mean /= BUFFER_LEN;
            if (mean > maxMean) maxMean = mean;
        }
    }
    float db = 0;
    if(maxMean > 0) {
        db = 20 * log10(maxMean);
        if(db > 0) db += 0;
    }
    return db;
}

bool leerSCD4x(float &temp, float &hum, uint16_t &co2) {
    if (airSensor.readMeasurement()) {
        uint16_t tempCO2 = airSensor.getCO2();
        if (tempCO2 > 0) {
            co2 = tempCO2;
            temp = airSensor.getTemperature();
            hum = airSensor.getHumidity();
            return true;
        }
    }
    return false;
}
