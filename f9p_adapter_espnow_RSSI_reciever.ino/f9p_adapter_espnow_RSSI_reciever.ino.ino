#include <esp_now.h>
#include <WiFi.h>

// Data structure (must match sender)
#pragma pack(push, 1)
typedef struct struct_message {
  int32_t latitude;     // degrees * 1e-7
  int32_t longitude;    // degrees * 1e-7
  uint32_t altitude;    // millimeters
  float heading;        // degrees
} struct_message;
#pragma pack(pop)

struct_message data_packet;

// Receiver callback (new ESP-IDF v5.x / Arduino 3.x style)
#if ESP_IDF_VERSION_MAJOR >= 5
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  // Copy bytes into struct
  memcpy(&data_packet, incomingData, sizeof(data_packet));

  // Get RSSI from packet metadata
  int8_t rssi = recv_info->rx_ctrl->rssi;

  // Serial.println("------ ESP-NOW Packet Received ------");
  // Serial.printf("From MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
  //               recv_info->src_addr[0], recv_info->src_addr[1], recv_info->src_addr[2],
  //               recv_info->src_addr[3], recv_info->src_addr[4], recv_info->src_addr[5]);
  // Serial.printf("RSSI: %d dBm\n", rssi);
  // Serial.printf("Latitude: %lu\n", data_packet.latitude);
  // Serial.printf("Longitude: %lu\n", data_packet.longitude);
  // Serial.printf("Altitude: %lu\n", data_packet.altitude);
  // Serial.printf("Heading: %lu\n", data_packet.heading);
  // Serial.println("------------------------------------");
  Serial.print(rssi);
  Serial.print(", ");
  Serial.print(data_packet.latitude);
  Serial.print(", ");
  Serial.print(data_packet.longitude);
  Serial.print(", ");
  Serial.print(data_packet.altitude);
  Serial.print(", ");
  Serial.println(data_packet.heading);
  //-------- for debug
  // Serial.print("Struct size: ");
  // Serial.println(sizeof(struct_message));
  Serial.print("Free heap: ");
  Serial.println(ESP.getFreeHeap());
}
#else
// Legacy style for Arduino-ESP32 2.x
void OnDataRecv(const uint8_t * mac, const uint8_t *incomingData, int len) {
  memcpy(&data_packet, incomingData, sizeof(data_packet));

  Serial.println("------ ESP-NOW Packet Received ------");
  Serial.printf("From MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.printf("Latitude: %lu\n", data_packet.latitude);
  Serial.printf("Longitude: %lu\n", data_packet.longitude);
  Serial.printf("Altitude: %lu\n", data_packet.altitude);
  Serial.printf("Heading: %lu\n", data_packet.heading);
  Serial.println("------------------------------------");
}
#endif


void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);

  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Register callback
  esp_now_register_recv_cb(OnDataRecv);
}

void loop() {
  // Nothing to do — callback handles packets
}
