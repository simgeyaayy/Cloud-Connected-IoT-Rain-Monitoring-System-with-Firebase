# Cloud-Connected IoT Rain Automation System (Firebase RTDB + MicroPython)

An end-to-end IoT monitoring and control solution connecting a MicroPython microcontroller to Google Firebase Realtime Database with dual control modes (Cloud vs. Infrared Remote)[cite: 4].

## Features
- **Cloud Synchronization:** Communicates with Firebase Realtime Database via REST API (`urequests`) over Wi-Fi[cite: 4].
- **Dual-Mode Arbitration:**
  - **Remote Priority & Auto-Fallback:** IR actions take temporary precedence with an automatic 30-second timeout returning control back to the Cloud[cite: 4].
  - **Firebase Mode:** Direct web dashboard / app remote control of stepper position, LED colors, and system power[cite: 4].
- **Telemetry Reporting:** Periodically patches system status, active LED color, stepper position, and sensor readings to `/device1/status`[cite: 4].
- **Automated Weather Response:** Stepper motor triggers physical actuation based on rain thresholds and status cycles[cite: 4].

## Hardware & Connections
| Device / Module | Board Pin |
|---|---|
| Wi-Fi | Built-in (e.g., Raspberry Pi Pico W / ESP32)[cite: 4] |
| Rain Sensor | GP26 (ADC)[cite: 4] |
| IR Receiver | GP2[cite: 4] |
| RGB / Status LEDs | Red: GP15, Green: GP14, Blue: GP13[cite: 4] |
| Stepper Driver (ULN2003) | GP16, GP17, GP18, GP19[cite: 4] |

## Configuration
Before deploying, edit the credentials in `IOT-FINAL.py`:
```python
SSID = 'YOUR_WIFI_SSID'
PASSWORD = 'YOUR_WIFI_PASSWORD'
FB_URL = '[https://YOUR-DATABASE.firebasedatabase.app/](https://YOUR-DATABASE.firebasedatabase.app/)' 
FB_AUTH = 'YOUR_FIREBASE_SECRET_OR_KEY'
DEV = 'device1'
