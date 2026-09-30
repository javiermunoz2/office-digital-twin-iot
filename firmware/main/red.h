#ifndef RED_H
#define RED_H

#include <Arduino.h>

void iniciarWiFi();
void mantenerWiFi(); 
// Quitamos el parámetro de presencia
void enviarDatos(float temp, float hum, int co2, int gas, float ruido, bool sensorListo);

#endif
