# MajinKit
ラズパイで作る、受付魔人の作成キットです。

※AI動画の作り方ノウハウはこちらの記事を参照<br>
https://zenn.dev/acntechjp/articles/0f53e090b62657<br>
※大きい動画ファイル（normal.mp4, sleep.mp4）は載らなかったので、YouTubeにサンプルを上げてあります。
- https://www.youtube.com/watch?v=HvJ0YzQJD6A
- https://www.youtube.com/watch?v=5ToteBW86rs

# Majin PIR Interactive Player (Raspberry Pi)

ラズパイ + PIRセンサー + mpv を使った  
**インタラクティブ動画再生システム**。

人が来ると動画が始まり、人がいなくなると演出動画を再生して待機状態に戻る。

用途例：

- 展示
- インタラクティブアート
- AIキャラクター装置
- デモ装置

---

# システム概要

このシステムは **PIRセンサー（人感センサー）** を使って  
人の動きを検知し、動画を制御する。

状態遷移は以下。

    STATE0 (待機)
    ↓ 人検出
    STATE1 (再生開始)
    ↓
    STATE2 (再生継続)
    ↓ 人がいない
    STATE3 (終了演出)
    ↓
    STATE0

---

# 状態遷移ロジック

## 入場検知

    0.5秒ごとにPIR確認
    10秒以内にHIGHが4回以上
    → 人が来たと判断

理由：

- PIRは誤検知がある
- 一瞬のHIGHでは開始しない
- 人が近づいて動けば自然に条件を満たす

---

## 在席判定

    2秒ごとにPIR確認
    LOWが14回連続
    → 人が去ったと判断

つまり

    2秒 × 14 = 約28秒

人が座って静止しても体験が途中で止まらないよう  
**出口は甘めの設計**にしている。

---

# 動画構成

    sleep.mp4   : 待機状態（ループ）
    normal.mp4  : メイン動画
    shift.mp4   : 終了演出

---

# 必要なハードウェア

- Raspberry Pi
- PIRセンサー（HC-SR501等）
- HDMIディスプレイ
- スピーカー

---

# GPIO接続

    PIR VCC → 5V
    PIR GND → GND
    PIR OUT → GPIO7

コードでは

    GPIO.BCM
    PIR_PIN = 7

---

# 必要ソフトウェア

## Python

Raspberry Pi OSには通常入っている。

    python3 --version

---

## mpv

動画再生に使用。

インストール：

    sudo apt update
    sudo apt install mpv

---

## RPi.GPIO

GPIO操作ライブラリ。

通常Raspberry Pi OSには入っているが  
なければ以下。

    pip3 install RPi.GPIO

---

# 使用ライブラリ

本プログラムで使用しているPython標準ライブラリ：

| ライブラリ | 用途 |
|---|---|
| time | タイマー |
| subprocess | mpv起動 |
| os | パス取得 |
| collections.deque | センサー履歴管理 |

外部ライブラリ：

| ライブラリ | 用途 |
|---|---|
| RPi.GPIO | GPIO操作 |

---

# テスト用コード

PIRセンサーの挙動確認用。  
動画再生なし。

```python
import RPi.GPIO as GPIO
import time
from collections import deque

GPIO.setmode(GPIO.BCM)

PIR_PIN = 7
GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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

print("PIR warming up (10 seconds)")
time.sleep(10)
print("Ready")

try:

    while True:

        now = time.time()
        pir = GPIO.input(PIR_PIN)

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

        elif state == 1:

            print("STATE1 normal start → STATE2")

            no_motion_count = 0
            last_check = time.time()
            state = 2

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
```

---

# 本番用コード

動画再生付き。

```python
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

        if state == 0:

            if now - last_entry_check >= ENTRY_INTERVAL:

                last_entry_check = now
                entry_samples.append(pir)

                if sum(entry_samples) >= ENTRY_THRESHOLD:

                    entry_samples.clear()
                    play(NORMAL_VIDEO)
                    state = 1

        elif state == 1:

            no_motion_count = 0
            last_check = time.time()
            state = 2

        elif state == 2:

            if player and player.poll() is not None:
                state = 3

            elif now - last_check >= CHECK_INTERVAL:

                last_check = now

                if pir:
                    no_motion_count = 0
                else:
                    no_motion_count += 1

                if no_motion_count >= NO_MOTION_LIMIT:
                    stop()
                    state = 3

        elif state == 3:

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
```

---

# 起動方法

    python MajinTest.py
    python Majin.py

---

# 補足

PIRセンサーは **人の存在ではなく赤外線の変化**を検出する。

そのため

- 静止した人は検出されないことがある
- 温風・日光でも反応する

本プログラムではそれを吸収するため  
**履歴ベースの判定ロジック**を採用している。

---

# License

MIT
