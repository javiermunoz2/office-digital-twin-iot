#ifndef SENSORES_H
#define SENSORES_H

#include <Arduino.h>

void iniciarHardware();
int leerGasFiltrado();
float leerRuidoDB();
bool leerSCD4x(float &temp, float &hum, uint16_t &co2);

#endif
