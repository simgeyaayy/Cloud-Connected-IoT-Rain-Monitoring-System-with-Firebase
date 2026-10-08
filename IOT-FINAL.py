from machine import Pin, ADC
import time
import network, urequests
import json

# Wi-Fi & Firebase bilgileri
SSID = 'YAY'
PASSWORD = '2020SY1991'
FB_URL = 'https://iot-final-c04b5-default-rtdb.europe-west1.firebasedatabase.app/' 
FB_AUTH = 'LJrU4LZ4GCQLzuzDXYf75CMqIHvv5dmob9P3pZNp'
DEV = 'device1'

# Donanım
rainSensor = ADC(26)
ir_pin = Pin(2, Pin.IN)
redLED = Pin(15, Pin.OUT)
greenLED = Pin(14, Pin.OUT)
blueLED = Pin(13, Pin.OUT)
step_pins = [Pin(16, Pin.OUT), Pin(17, Pin.OUT), Pin(18, Pin.OUT), Pin(19, Pin.OUT)]
halfstep_seq = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1],
]

# Sistem değişkenleri
systemUnlocked = False
systemEnabled = False
manualMode = False
manualLED = 0
motorPosition = 0
cycleReady = False
modeSource = "firebase"
last_remote_time = 0
REMOTE_TIMEOUT_MS = 30000  # 30 saniye

# Şifre tanımı
password = [0x00FFA25D, 0x00FF629D, 0x00FFE21D, 0x00FF22DD]
inputCode = []
passwordLength = 4

# IR Kodları
IR_ON = 0x00FFA25D
IR_OFF = 0x00FF629D
IR_MANUAL_RED = 0x00FFE21D
IR_MANUAL_BLUE = 0x00FF22DD
IR_MANUAL_GREEN = 0x00FF02FD
IR_MOTOR_ON = 0x00FFE01F
IR_MOTOR_OFF = 0x00FFA857
IR_OK = 0x00FF38C7 

# Yardımcılar
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    for _ in range(10):
        if wlan.isconnected():
            print("Wi-Fi bağlandı:", wlan.ifconfig()[0])
            return True
        time.sleep(1)
    return False

def firebase_get(path):
    try:
        url = "{}{}.json?auth={}".format(FB_URL, path, FB_AUTH)
        r = urequests.get(url)
        data = r.json()
        r.close()
        return data
    except:
        return {}

def firebase_patch(path, data):
    try:
        url = "{}{}.json?auth={}".format(FB_URL, path, FB_AUTH)
        r = urequests.patch(url, data=json.dumps(data))
        r.close()
    except:
        pass

def step_motor(steps, delay=0.002):
    direction = 1 if steps > 0 else -1
    steps = abs(steps)
    for i in range(steps):
        pattern = halfstep_seq[i % 8] if direction == 1 else halfstep_seq[(7 - i % 8) % 8]
        for pin, val in zip(step_pins, pattern):
            pin.value(val)
        time.sleep(delay)

def read_ir_once():
    timeout = time.ticks_ms()
    while ir_pin.value() == 1:
        if time.ticks_diff(time.ticks_ms(), timeout) > 200:
            return None
    durations = []
    t0 = time.ticks_us()
    while ir_pin.value() == 0: pass
    t1 = time.ticks_us()
    while ir_pin.value() == 1: pass
    t2 = time.ticks_us()
    durations.append((time.ticks_diff(t1, t0), time.ticks_diff(t2, t1)))
    t0 = t2
    while len(durations) < 100:
        while ir_pin.value() == 0: pass
        t1 = time.ticks_us()
        while ir_pin.value() == 1: pass
        t2 = time.ticks_us()
        durations.append((time.ticks_diff(t1, t0), time.ticks_diff(t2, t1)))
        t0 = t2
    bits = []
    for low, high in durations:
        if 400 < high < 700: bits.append(0)
        elif 1300 < high < 1800: bits.append(1)
    if len(bits) < 32: return None
    code = 0
    for b in bits[:32]:
        code = (code << 1) | b
    time.sleep_ms(200)
    return code

def clear_leds():
    redLED.value(0)
    greenLED.value(0)
    blueLED.value(0)

def wait_for_password():
    global inputCode, systemUnlocked, systemEnabled
    print("Şifre girin (IR kumanda):")
    while not systemUnlocked:
        ir_code = read_ir_once()
        if ir_code and ir_code != 0xFFFFFFFF:
            print("IR Code Received: 0x{:08X}".format(ir_code))
            inputCode.append(ir_code)
            if len(inputCode) == passwordLength:
                if inputCode == password:
                    systemUnlocked = True
                    systemEnabled = True
                    print("Şifre doğru → Sistem açıldı.")
                else:
                    print("Şifre yanlış.")
                inputCode = []

def set_manual_led(code):
    global manualMode, manualLED, modeSource, last_remote_time
    manualMode = True
    modeSource = "remote"
    last_remote_time = time.ticks_ms()
    if code == IR_MANUAL_RED: manualLED = 1
    elif code == IR_MANUAL_BLUE: manualLED = 2
    elif code == IR_MANUAL_GREEN: manualLED = 3

def main():
    global systemEnabled, manualMode, manualLED, motorPosition, cycleReady
    global modeSource, last_remote_time

    if not wifi_connect():
        print("Wi-Fi bağlantısı başarısız.")
        return

    wait_for_password()
    print("System active and ready.")

    loop_ts = time.ticks_ms()
    beat_ts = time.ticks_ms()

    while True:
        ir_code = read_ir_once()
        if ir_code and ir_code != 0xFFFFFFFF:
            print("IR Code: 0x{:08X}".format(ir_code))
            modeSource = "remote"
            last_remote_time = time.ticks_ms()

            if ir_code == IR_OFF:
                systemEnabled = False
                manualMode = False
                clear_leds()
            elif ir_code == IR_ON:
                systemEnabled = True
            elif ir_code in [IR_MANUAL_RED, IR_MANUAL_BLUE, IR_MANUAL_GREEN]:
                set_manual_led(ir_code)
            elif ir_code == IR_OK:
                modeSource = "firebase"
                manualMode = False
                manualLED = 0
                print("OK tuşu → kontrol Firebase'e geçti")
            elif ir_code == IR_MOTOR_ON and motorPosition == 0:
                step_motor(1024)
                motorPosition = 1
            elif ir_code == IR_MOTOR_OFF and motorPosition != 0:
                step_motor(-1024 if motorPosition == 1 else 1024)
                motorPosition = 0

        # Firebase sorgusu
        if time.ticks_diff(time.ticks_ms(), loop_ts) > 2000:
            loop_ts = time.ticks_ms()
            cmd = firebase_get(DEV + "/cmd")
            if cmd:
                systemEnabled = cmd.get("enable", systemEnabled)
                if modeSource == "firebase":
                    modeCmd = cmd.get("mode")
                    if modeCmd == "manual":
                        manualMode = True
                    elif modeCmd == "auto":
                        manualMode = False
                    led = cmd.get("led", {})
                    if led.get("red"): manualLED = 1
                    elif led.get("green"): manualLED = 3
                    elif led.get("blue"): manualLED = 2
                motorCmd = cmd.get("motor")
                if motorCmd == "left" and motorPosition != -1:
                    step_motor(-1024)
                    motorPosition = -1
                elif motorCmd == "right" and motorPosition != 1:
                    step_motor(1024)
                    motorPosition = 1
                elif motorCmd == "central" and motorPosition != 0:
                    step_motor(-1024 if motorPosition == 1 else 1024)
                    motorPosition = 0

            rain = rainSensor.read_u16() >> 4
            led_color = ("off", "red", "blue", "green")[manualLED] if manualMode else \
                ("red" if redLED.value() else "green" if greenLED.value()
                 else "blue" if blueLED.value() else "off")

            firebase_patch(DEV + "/status", {
                "enabled": systemEnabled,
                "led": led_color,
                "motorPos": motorPosition,
                "rain": rain,
                "modeSource": modeSource
            })

        # Timeout → kontrolü Firebase'e geri ver
        if modeSource == "remote":
            if time.ticks_diff(time.ticks_ms(), last_remote_time) > REMOTE_TIMEOUT_MS:
                modeSource = "firebase"
                manualMode = False
                manualLED = 0
                print("Timeout → kontrol Firebase'e döndü")

        # Heartbeat
        if time.ticks_diff(time.ticks_ms(), beat_ts) > 2000:
            beat_ts = time.ticks_ms()
            print("ALIVE | Mode:", modeSource, "| Rain:", rainSensor.read_u16() >> 4)

        # LED kontrol
        if not systemEnabled:
            clear_leds()
        elif manualMode:
            clear_leds()
            if manualLED == 1: redLED.value(1)
            elif manualLED == 2: blueLED.value(1)
            elif manualLED == 3: greenLED.value(1)
        else:
            rain = rainSensor.read_u16() >> 4
            clear_leds()
            if rain <= 800:
                greenLED.value(1)
                if motorPosition == 1 and cycleReady:
                    step_motor(-1024)
                    motorPosition = 0
                    cycleReady = False
            elif 800 < rain <= 1800:
                blueLED.value(1)
                if motorPosition == 0:
                    step_motor(1024)
                    motorPosition = 1
                    cycleReady = True
            elif rain > 1800:
                redLED.value(1)

        time.sleep(0.05)

main()
