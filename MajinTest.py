import RPi.GPIO as GPIO
import time
from collections import deque

GPIO.setmode(GPIO.BCM)

PIR_PIN = 7
GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# ---- 設定 ----
ENTRY_INTERVAL = 0.5
ENTRY_WINDOW = 20      # 10秒 / 0.5秒
ENTRY_THRESHOLD = 4    # HIGHが4回以上

CHECK_INTERVAL = 2
NO_MOTION_LIMIT = 14   # 14回LOWで離脱

state = 0

entry_samples = deque(maxlen=ENTRY_WINDOW)
no_motion_count = 0

last_entry_check = time.time()
last_check = time.time()

print("PIR warming up (10 seconds)")
time.sleep(10)
print("Ready")

try:
    while True:

        now = time.time()
        pir = GPIO.input(PIR_PIN)

        # -----------------------
        # STATE 0 : 待機
        # -----------------------
        if state == 0:

            if now - last_entry_check >= ENTRY_INTERVAL:

                last_entry_check = now

                entry_samples.append(pir)

                high_count = sum(entry_samples)

                print(f"STATE0 HIGH count = {high_count}/4")

                if high_count >= ENTRY_THRESHOLD:
                    print("Entry confirmed → STATE1")
                    entry_samples.clear()
                    state = 1

        # -----------------------
        # STATE 1 : normal開始
        # -----------------------
        elif state == 1:

            print("STATE1 normal start → STATE2")

            no_motion_count = 0
            last_check = time.time()

            state = 2

        # -----------------------
        # STATE 2 : normal中
        # -----------------------
        elif state == 2:

            if now - last_check >= CHECK_INTERVAL:

                last_check = now

                if pir:
                    no_motion_count = 0
                    print("STATE2 motion detected → reset counter")
                else:
                    no_motion_count += 1
                    print(f"STATE2 no motion ({no_motion_count}/14)")

                if no_motion_count >= NO_MOTION_LIMIT:
                    print("No motion 14 times → STATE3")
                    state = 3

        # -----------------------
        # STATE 3 : shift
        # -----------------------
        elif state == 3:

            print("STATE3 shift → STATE0")

            entry_samples.clear()
            no_motion_count = 0

            time.sleep(2)

            state = 0

        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("Quit")