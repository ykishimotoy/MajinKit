import RPi.GPIO as GPIO
import time
import subprocess
import os
from collections import deque

GPIO.setmode(GPIO.BCM)

PIR_PIN = 7
GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

BASE = os.path.dirname(os.path.abspath(__file__))

SLEEP_VIDEO = os.path.join(BASE, "sleep.mp4")
NORMAL_VIDEO = os.path.join(BASE, "normal.mp4")
SHIFT_VIDEO = os.path.join(BASE, "shift.mp4")

MPV_CMD = [
    "mpv",
    "--fs",
    "--no-osd-bar",
    "--really-quiet",
    "--hwdec=auto-safe",
    "--vo=gpu",
    "--gpu-context=x11egl"
]

# ---- PIR設定 ----
ENTRY_INTERVAL = 0.5
ENTRY_WINDOW = 20
ENTRY_THRESHOLD = 4

CHECK_INTERVAL = 2
NO_MOTION_LIMIT = 14

state = 0

entry_samples = deque(maxlen=ENTRY_WINDOW)
no_motion_count = 0

last_entry_check = time.time()
last_check = time.time()

player = None


def play(video, loop=False):
    global player

    stop()

    cmd = MPV_CMD.copy()

    if loop:
        cmd.append("--loop")

    cmd.append(video)

    env = os.environ.copy()
    env["DISPLAY"] = ":0"

    player = subprocess.Popen(cmd, env=env)


def stop():
    global player

    if player and player.poll() is None:
        player.terminate()
        player.wait()

    player = None


print("PIR warming up (10 seconds)")
time.sleep(10)
print("Ready")

play(SLEEP_VIDEO, loop=True)

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

                if high_count >= ENTRY_THRESHOLD:
                    print("Entry confirmed → STATE1")

                    entry_samples.clear()

                    play(NORMAL_VIDEO)

                    state = 1

        # -----------------------
        # STATE 1
        # -----------------------
        elif state == 1:

            print("STATE1 → STATE2")

            no_motion_count = 0
            last_check = time.time()

            state = 2

        # -----------------------
        # STATE 2
        # -----------------------
        elif state == 2:

            # normal動画終了
            if player and player.poll() is not None:
                print("Normal finished → STATE3")
                state = 3

            elif now - last_check >= CHECK_INTERVAL:

                last_check = now

                if pir:
                    no_motion_count = 0
                else:
                    no_motion_count += 1
                    print(f"No motion ({no_motion_count}/14)")

                if no_motion_count >= NO_MOTION_LIMIT:
                    print("No motion 14 times → STATE3")
                    stop()
                    state = 3

        # -----------------------
        # STATE 3
        # -----------------------
        elif state == 3:

            print("Playing shift video")

            play(SHIFT_VIDEO)

            player.wait()

            play(SLEEP_VIDEO, loop=True)

            entry_samples.clear()
            no_motion_count = 0

            state = 0

        time.sleep(0.05)

except KeyboardInterrupt:

    stop()
    GPIO.cleanup()

    print("Quit")