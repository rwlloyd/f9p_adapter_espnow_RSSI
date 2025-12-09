/*
 * pin 1 - not used          |  Micro SD card     |
 * pin 2 - CS (SS)           |                   /
 * pin 3 - DI (MOSI)         |                  |__
 * pin 4 - VDD (3.3V)        |                    |
 * pin 5 - SCK (SCLK)        | 8 7 6 5 4 3 2 1   /
 * pin 6 - VSS (GND)         | ▄ ▄ ▄ ▄ ▄ ▄ ▄ ▄  /
 * pin 7 - DO (MISO)         | ▀ ▀ █ ▀ █ ▀ ▀ ▀ |
 * pin 8 - not used          |_________________|
 *                             ║ ║ ║ ║ ║ ║ ║ ║
 *                     ╔═══════╝ ║ ║ ║ ║ ║ ║ ╚═════════╗
 *                     ║         ║ ║ ║ ║ ║ ╚══════╗    ║
 *                     ║   ╔═════╝ ║ ║ ║ ╚═════╗  ║    ║
 * Connections for     ║   ║   ╔═══╩═║═║═══╗   ║  ║    ║
 * full-sized          ║   ║   ║   ╔═╝ ║   ║   ║  ║    ║
 * SD card             ║   ║   ║   ║   ║   ║   ║  ║    ║
 * Pin name         |  -  DO  VSS SCK VDD VSS DI CS    -  |
 * SD pin number    |  8   7   6   5   4   3   2   1   9 /
 *                  |                                  █/
 *                  |__▍___▊___█___█___█___█___█___█___/
 *
 * Note:  The SPI pins can be manually configured by using `SPI.begin(sck, miso, mosi, cs).`
 *        Alternatively, you can change the CS pin and use the other default settings by using `SD.begin(cs)`.
 *
 * +--------------+---------+-------+----------+----------+----------+----------+----------+
 * | SPI Pin Name | ESP8266 | ESP32 | ESP32‑S2 | ESP32‑S3 | ESP32‑C3 | ESP32‑C6 | ESP32‑H2 |
 * +==============+=========+=======+==========+==========+==========+==========+==========+
 * | CS (SS)      | GPIO15  | GPIO5 | GPIO34   | GPIO10   | GPIO7    | GPIO18   | GPIO0    |
 * +--------------+---------+-------+----------+----------+----------+----------+----------+
 * | DI (MOSI)    | GPIO13  | GPIO23| GPIO35   | GPIO11   | GPIO6    | GPIO19   | GPIO25   |
 * +--------------+---------+-------+----------+----------+----------+----------+----------+
 * | DO (MISO)    | GPIO12  | GPIO19| GPIO37   | GPIO13   | GPIO5    | GPIO20   | GPIO11   |
 * +--------------+---------+-------+----------+----------+----------+----------+----------+
 * | SCK (SCLK)   | GPIO14  | GPIO18| GPIO36   | GPIO12   | GPIO4    | GPIO21   | GPIO10   |
 * +--------------+---------+-------+----------+----------+----------+----------+----------+
 *
 * For more info see file README.md in this library or on URL:
 * https://github.com/espressif/arduino-esp32/tree/master/libraries/SD
 */

// For Esp and Wifi
#include <esp_now.h>
#include <WiFi.h>
// For SD card logging (if needed)
#include <FS.h>
#include <SPI.h>
#include <SD.h>

// Define SD card connection
#define SD_MOSI     23
#define SD_MISO     19
#define SD_SCLK     18
#define SD_CS       5   // Chip Select pin
File myFile;


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
  // Serial.print("Free heap: ");
  // Serial.println(ESP.getFreeHeap());
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

void sdStart(){
  Serial.println("Setup start");
  SPI.begin(SD_SCLK, SD_MISO, SD_MOSI, SD_CS);
  if (!SD.begin(SD_CS)) 
  {
    Serial.println("SD Card MOUNT FAIL");
  } 
  else 
  {
    Serial.println("SD Card MOUNT SUCCESS");
    Serial.println("");
    uint32_t cardSize = SD.cardSize() / (1024 * 1024);
    String str = "SDCard Size: " + String(cardSize) + "MB";
    Serial.println(str);
    uint8_t cardType = SD.cardType();
    if(cardType == CARD_NONE)
    {
      Serial.println("No SD card attached");
    }
    Serial.print("SD Card Type: ");
    if(cardType == CARD_MMC)
    {
        Serial.println("MMC");
    } 
    else if(cardType == CARD_SD)
    {
        Serial.println("SDSC");
    } 
    else if(cardType == CARD_SDHC)
    {
        Serial.println("SDHC");
    } 
    else 
    {
        Serial.println("UNKNOWN");
    }
    myFile = SD.open("/");
    printDirectory(myFile, 0);
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(); // ensure we’re not connected to anything
  WiFi.channel(13);   // <-- set desired channel (1–13, usually 1, 6, or 11)

  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Initialize SD card
  sdStart();
  // Register callback
  esp_now_register_recv_cb(OnDataRecv);
  }

void loop() {
  // Nothing to do — callback handles packets
}
