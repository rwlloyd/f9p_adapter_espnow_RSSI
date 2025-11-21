
// f9p datasheet https://docs.holybro.com/gps-and-rtk-system/f9p-h-rtk-series/standard-f9p-uart/pinout
// IST8310 datasheet https://tw.isentek.com/userfiles/files/IST8310Datasheet_3DMagneticSensors.pdf

// NEOPIXEL - for a little feedback
#include <Adafruit_NeoPixel.h>
#define NEOPIXEL_PIN 5
#define NUM_PIXELS 1

Adafruit_NeoPixel pixel(NUM_PIXELS, NEOPIXEL_PIN, NEO_RGB + NEO_KHZ800); //<- not sure about last argument

// HEADING
#include "IST8310.h"  // Include IST8310 library for I2C comms https://github.com/Srijal97/IST8310/tree/main
IST8310 ist8310; // Instantiate IST8310 reader library

// GPS Setup
#include <SparkFun_u-blox_GNSS_v3.h> //http://librarymanager/All#SparkFun_u-blox_GNSS_v3
SFE_UBLOX_GNSS_SERIAL myGNSS;
#define mySerial Serial2 // Use Serial1 to connect to the GNSS module. Change this if required

//ESPNOW
#include <esp_now.h>
#include <WiFi.h>

// MAC address of the receiver
uint8_t broadcastAddress[] = {0x68, 0x25, 0xDD, 0xEF, 0x49, 0x80};

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
  // Initialise the Neopixel
  pixel.begin();
  pixel.clear(); // turns everything off
  pixel.show();

  // Start Serial Comms
  Serial.begin(115200); 
  delay(250);
  Serial.println("F9P-Rover");
  Serial.println("Debug Serial Started");

  mySerial.begin(115200, SERIAL_8N1, 16, 17);     // F9P default baud rate (can be 38400 or 115200 too)
  
  //myGNSS.enableDebugging(); // Uncomment this line to enable helpful debug messages on Serial

  myGNSS.connectedToUART2(); // This tells the library we are connecting to UART2 so it uses the correct configuration keys

  while (myGNSS.begin(mySerial) == false) //Connect to the u-blox module using mySerial (defined above)
  {
    Serial.println(F("u-blox GNSS not detected"));
    Serial.println(F("Attempting to enable the UBX protocol for output"));
    myGNSS.setUART2Output(COM_TYPE_UBX); // Enable UBX output. Disable NMEA output
    Serial.println(F("Retrying..."));
    delay (1000);
  }
  //myGNSS.saveConfigSelective(VAL_CFG_SUBSEC_IOPORT); //Optional: save (only) the communications port settings to flash and BBR
  Serial.println("GPS setup complete");

  // while (!Serial); 

  // Start i2c Comms
  Wire.begin(21,22);
  Serial.println("Trying to setup IST8310");
  bool success = ist8310.setup(&Wire, &Serial);
  if (!success) {
      Serial.println("Failed to setup IST8310");
  } else {
    Serial.println("IST8310 Setup Successful");
  }
  ist8310.set_flip_x_y(false);

  // -0.1887865056 at College Park, MD, USA. This value gets added to the magnetic heading to report the true heading;
  // See http://www.magnetic-declination.com/
  ist8310.set_declination_offset_radians(0.0); 

  //ESPNOW / Comms setup
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);
  // WiFi.disconnect(); // ensure we’re not connected to anything
  // WiFi.channel(13);   // <-- set desired channel (1–13, usually 1, 6, or 11)

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

void checkGPS()
{
    // Request (poll) the position, velocity and time (PVT) information.
  // The module only responds when a new position is available. Default is once per second.
  // getPVT() returns true when new data is received.
  if (myGNSS.getPVT() == true)
  {
    int32_t latitude = myGNSS.getLatitude();
    data_packet.latitude = latitude;
    Serial.print(F("Lat: "));
    Serial.print(latitude);

    int32_t longitude = myGNSS.getLongitude();
    data_packet.longitude = longitude;
    Serial.print(F(" Long: "));
    Serial.print(longitude);
    Serial.print(F(" (degrees * 10^-7)"));

    int32_t altitude = myGNSS.getAltitudeMSL(); // Altitude above Mean Sea Level
    data_packet.altitude = altitude;
    Serial.print(F(" Alt: "));
    Serial.print(altitude);
    Serial.print(F(" (mm)"));
  }
}

void getHeading()
{
  bool success = ist8310.update();
  if (!success)
  {
      Serial.println("Failed to update IST8310");
  } else {
      uint32_t heading = ist8310.get_heading_degrees();
      data_packet.heading = heading;
      // Serial.println("IST8310 Started Successfully");
      Serial.print(" Heading: ");
      Serial.println(ist8310.get_heading_degrees());
      // Serial.println(" degrees"); //\n", ist8310.get_heading_degrees());  // 0 degrees at true north (or magnetic north if declination is 0)
  }
}

//helper function to set the Neopixel colour
void setColour(uint8_t r,uint8_t g,uint8_t b){
  pixel.setPixelColor(0,pixel.Color(r,g,b));
  pixel.show();
}

void loop() {

  // LOCATION
  checkGPS();
  // HEADING
  getHeading();
  //COMMUNICATION
  // Send message via ESP-NOW
  esp_err_t result = esp_now_send(broadcastAddress, (uint8_t *)&data_packet, sizeof(data_packet));
  // esp_now_send(broadcastAddress, (uint8_t *)&data_packet, sizeof(data_packet));
    
  //-------- for debug
  // Serial.print("Struct size: ");
  // Serial.println(sizeof(struct_message));
  // Serial.print("Free heap: ");
  // Serial.println(ESP.getFreeHeap());

  if (result == ESP_OK) {
    Serial.println("Sent with success");
    setColour(0,255,0);
  }
  else {
    Serial.println("Error sending the data");
    setColour(255,0,0);
  }
  // get about 20-50 messages out then everything stops..... lets try
  delay(5);           // Let Wi-Fi/ESP-NOW process
  yield();             // Prevent watchdog resets
}
