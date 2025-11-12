# F9P Adapter ESPNO RSSI

This repo is concerned with the following:

Holybro H-RTK -> ESP32 Rover -> ((( ESPNOW ))) -> ESP32 Base Station

The whole point of this is:

- Receive the GPS location of the Rover, 
- Measure the received signal strength and 
- Log data so that we can make a heat map of ESPnow signal propagation 

It is hoped that ESPnow signals strength can be used as an analog for wifi signal propagation.

## Rover Hardware

The H-RTK is connected to the ESP32 via a custom wiring harness. This harness connects:

- ESP32 power (Vin and GND), 
- Serial (RX2 and TX2) and 
- I2C (D21 and D22), 

to the GPIO of the H-RTK.

### Rover Power

Powering both ESP32 and H-RTK from a single USB port causes transmission issues due to lack of suitable current. This can be overcome by powering the H-RTK from its USB port and disconnecting the 5V supply. However, this means the loss of the magnetometer data as the i2c connection requires the disconnected 5V. 

This must be fixed in the future.

## Base Station Hardware

The base station is simply a bare ESP32.

## Tools

Convert decimal to dms coordinates.

https://www.latlong.net/lat-long-dms.html



