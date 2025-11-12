
// f9p datasheet https://docs.holybro.com/gps-and-rtk-system/f9p-h-rtk-series/standard-f9p-uart/pinout
// IST8310 datasheet https://tw.isentek.com/userfiles/files/IST8310Datasheet_3DMagneticSensors.pdf

// // HEADING
// #include "IST8310.h"  // Include IST8310 library for I2C comms https://github.com/Srijal97/IST8310/tree/main
// IST8310 ist8310; // Instantiate IST8310 reader library

// // GPS Setup
// #include <SparkFun_u-blox_GNSS_v3.h> //http://librarymanager/All#SparkFun_u-blox_GNSS_v3
// SFE_UBLOX_GNSS_SERIAL myGNSS;
// #define mySerial Serial2 // Use Serial1 to connect to the GNSS module. Change this if required

//ESPNOW
#include <esp_now.h>
#include <WiFi.h>

// MAC address of the receiver
uint8_t broadcastAddress[] = {0xF8, 0xB3, 0xB7, 0x29, 0xFB, 0x3C};

// Variable to add info about peer
esp_now_peer_info_t peerInfo;

// Data structure for the transmission
#pragma pack(push, 1)
typedef struct struct_message {
  int32_t latitude;     // degrees * 1e-7
  int32_t longitude;    // degrees * 1e-7
  uint32_t altitude;    // millimeters
  float heading;        // degrees
} struct_message;
#pragma pack(pop)

struct_message data_packet;

// callback when data is sent
// void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
//   Serial.print("\r\nLast Packet Send Status:\t");
//   Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
// }
// Works on both ESP32 Arduino Core 2.x and 3.x
#if ESP_IDF_VERSION_MAJOR >= 5
// For ESP-IDF v5.x / Arduino-ESP32 v3.x
void OnDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
  Serial.print("\r\nLast Packet Send Status:\t");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");

  // Optional: print destination MAC for debugging
  // char macStr[18];
  // snprintf(macStr, sizeof(macStr),
  //          "%02X:%02X:%02X:%02X:%02X:%02X",
  //          info->des_addr[0], info->des_addr[1], info->des_addr[2],
  //          info->des_addr[3], info->des_addr[4], info->des_addr[5]);
  // Serial.print("Sent to: ");
  // Serial.println(macStr);
}
#else
// For ESP-IDF v4.x / Arduino-ESP32 v2.x
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  Serial.print("\r\nLast Packet Send Status:\t");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
}
#endif


void setup() {
  // Start Serial Comms
  Serial.begin(115200); 
  delay(250);
  Serial.println("ESPnow sender");
  Serial.println("Debug Serial Started");

  // mySerial.begin(115200, SERIAL_8N1, 16, 17);     // F9P default baud rate (can be 38400 or 115200 too)
  
  //ESPNOW / Comms setup
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);

  // Init ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Once ESPNow is successfully Init, we will register for Send CB to
  // get the status of Trasnmitted packet
  esp_now_register_send_cb(OnDataSent);

  // Register peer
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  // Add peer
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    return;
  }

}

void loop() {

  // LOCATION
  // checkGPS();
  // HEADING
  // getHeading();
  data_packet.latitude = random(50000,60000);
  data_packet.longitude = random(0,4000);
  data_packet.altitude = random(4000,5000);
  data_packet.heading = random(0,360);
  //COMMUNICATION
  // Send message via ESP-NOW
  esp_err_t result = esp_now_send(broadcastAddress, (uint8_t *)&data_packet, sizeof(data_packet));
  // esp_now_send(broadcastAddress, (uint8_t *)&data_packet, sizeof(data_packet));
    //-------- for debug
  // Serial.print("Struct size: ");
  // Serial.println(sizeof(struct_message));
  Serial.print("Free heap: ");
  Serial.println(ESP.getFreeHeap());

  if (result == ESP_OK) {
    Serial.println("Sent with success");
  }
  else {
    Serial.println("Error sending the data");
  }
  // get about 20-50 messages out then everything stops..... lets try
  delay(5);           // Let Wi-Fi/ESP-NOW process
  yield();             // Prevent watchdog resets
}
