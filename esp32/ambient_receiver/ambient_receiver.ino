// ESP32 Arduino core. Serial-only by default; no guessed wiring.
#include <WiFi.h>
#include <WiFiUdp.h>
#define ENABLE_LEDS 0
#if ENABLE_LEDS
#include <FastLED.h>
// Set only AFTER confirming strip type, pin and power. Example is WS2812B only.
#define LED_PIN 4
#define LED_COUNT 60
CRGB leds[LED_COUNT];
#endif
const char* WIFI_SSID = "CHANGE_ME";
const char* WIFI_PASSWORD = "CHANGE_ME";
const uint16_t UDP_PORT = 7799;
const uint32_t TOKEN = 324508639; // Match config.json; change both together.
WiFiUDP udp;
uint32_t lastRx = 0, lastSeq = 0, lastRetry = 0;
uint8_t flags = 0;
bool havePacket = false, udpReady = false;
uint32_t be32(const uint8_t* p) {
  return (uint32_t(p[0])<<24)|(uint32_t(p[1])<<16)|(uint32_t(p[2])<<8)|p[3];
}
void setup() {
  Serial.begin(115200);
#if ENABLE_LEDS
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, LED_COUNT);
  FastLED.setBrightness(32);
#endif
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}
void loop() {
  uint32_t now = millis();
  if (WiFi.status() == WL_CONNECTED && !udpReady) {
    udpReady = udp.begin(UDP_PORT) == 1;
    Serial.print("ESP32 IP: "); Serial.println(WiFi.localIP());
  }
  if (WiFi.status() != WL_CONNECTED) {
    if (udpReady) udp.stop();
    udpReady = false;
    flags = 0;
    if (now - lastRetry > 10000) { lastRetry = now; WiFi.reconnect(); }
  }
  // Bound network work so malformed traffic cannot starve timeout/render logic.
  for (int i=0; udpReady && i<8; ++i) {
    int len = udp.parsePacket();
    if (!len) break;
    uint8_t p[16];
    if (len != 16) { while (udp.available()) udp.read(); continue; }
    if (udp.read(p, 16) != 16) continue;
    if (memcmp(p, "AL01", 4) || p[4]!=1 || p[6] || p[7] || (p[5]&0x60) || be32(p+12)!=TOKEN) continue;
    uint32_t seq = be32(p+8);
    // Accept sequence restart only after receiver timeout.
    if (havePacket && now-lastRx <= 500 && int32_t(seq-lastSeq)<=0) continue;
    havePacket = true; lastRx = now; lastSeq = seq;
    flags = (p[5]&128) ? p[5] : 0;
  }
  if (!havePacket || now-lastRx > 500) flags = 0;
  static int previous = -1;
  if (previous != flags) {
    previous = flags;
    Serial.printf("valid=%d left=%d right=%d brake=%d blindL=%d blindR=%d\n",
      !!(flags&128),!!(flags&1),!!(flags&2),!!(flags&4),!!(flags&8),!!(flags&16));
  }
#if ENABLE_LEDS
  bool flash = (now % 800) < 400;
  for (int i=0; i<LED_COUNT; ++i) {
    bool left = i < LED_COUNT/2;
    bool turn = flags & (left ? 1 : 2);
    bool blind = flags & (left ? 8 : 16);
    CRGB color(0, 8, 20); // Ordinary ambient fallback.
    if (flags&4) color = CRGB(32, 0, 0);
    if (blind) color = CRGB(32, 12, 0);
    if (turn) color = flash ? CRGB(48, 20, 0) : CRGB::Black;
    if (turn && blind) color = flash ? CRGB(48, 0, 0) : CRGB::Black;
    leds[i] = color;
  }
  FastLED.show();
#endif
  delay(10);
}
