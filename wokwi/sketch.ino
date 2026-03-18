#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

// --- Configuration ---
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

WiFiClientSecure wifiClient;
PubSubClient client(wifiClient);

String deviceId = "meter-001"; // Updated to reflect energy meter

// --- WiFi Connection ---
void connectWifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

// --- MQTT Connection ---
void connectMQTT() {
  // CloudAMQP requires secure connection if using port 8883
  wifiClient.setInsecure(); 
  
  while (!client.connected()) {
    Serial.print("Connecting to CloudAMQP...");
    if (client.connect(deviceId.c_str(), MQTT_USER, MQTT_PASS)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 2s");
      delay(2000);
    }
  }
}

// --- Energy Telemetry Logic ---
void publishEnergyTelemetry() {
  StaticJsonDocument<256> doc;

  float voltage     = 220.0 + ((float)random(-50, 50) / 10.0);  // 215–225 V
  float current     = (float)random(10, 1000) / 100.0;           // 0.1–10.0 A
  float power       = round(voltage * current * 100.0) / 100.0;  // P = V * I
  float energy      = round((float)random(0, 10000)) / 100.0;    // 0–100 kWh
  float powerFactor = 0.80 + ((float)random(0, 20)) / 100.0;    // 0.80–1.00
  float frequency   = 50.0 + ((float)random(-5, 5)) / 10.0;     // 49.5–50.5 Hz

  doc["device_id"]    = deviceId;
  doc["voltage"]      = voltage;
  doc["current"]      = current;
  doc["power"]        = power;
  doc["energy"]       = energy;
  doc["power_factor"] = powerFactor;
  doc["frequency"]    = frequency;
  doc["device_type"]  = "smart-meter";

  char buffer[256];
  serializeJson(doc, buffer);

  bool ok = client.publish(MQTT_TOPIC, buffer);
  if (ok) {
    Serial.print("[PUB] ");
    Serial.println(buffer);
  } else {
    Serial.println("[ERR] Publish failed");
  }
}

void setup() {
  Serial.begin(115200);
  connectWifi();
  client.setServer(MQTT_SERVER, MQTT_PORT);
}

void loop() {
  if (!client.connected()) {
    connectMQTT();
  }
  client.loop();
  
  // Publish every 5 seconds as per telemetry streaming principle
  publishEnergyTelemetry();
  delay(5000);
}