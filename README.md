# MajinKit
ラズパイで作る、受付魔人の作成キットです。ここにある全ファイルを同じディレクトリに置いて、下記のコードでテスト（動画なし）＆本番実行（動画あり）してください。動画を同名で差し替えれば、オリジナルの魔人（魔人でなくてもいいです）を作れます。
```
python MajinTest.py
python Majin.py
```

※PIR（赤外線センサー）とラズパイの繋ぎ方は、機材ごとに違うと思うので、自分の買った機材を元に検索＆AIで調べてください。<br><br>

※AI動画の作り方ノウハウはこちらの記事をご参照ください。<br>
https://zenn.dev/acntechjp/articles/0f53e090b62657<br><br>

※大きい動画ファイル（normal.mp4, sleep.mp4）は載らなかったので、YouTubeにサンプルを上げてあります。
- https://www.youtube.com/watch?v=HvJ0YzQJD6A
- https://www.youtube.com/watch?v=5ToteBW86rs

※動画間の切り替わりに若干タイムラグがあるので、fehというソフトで全画面表示の画像を表示してからプログラム起動すると良いです。<br>

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

# 必要な機材
- Raspberry Pi 4（メモリ4GB以上を推奨。2GBでも動くとChatGPTは言ってましたが、検証したのは4GBモデルです。）
- PIR（赤外線センサー。例：HC-SR501）
- ディスプレイとHDMIケーブル（オスオス）とHDMIメス-mini HDMIオス変換アダプタ（ラズパイに接続する用）
- スピーカー（3.5mmオーディオプラグでラズパイに接続する用）
- 起動・操作用の機材（インターネット経由でラズパイに接続可能な別のパソコン、またはラズパイに直接繋げるマウスとキーボード）
※ラズパイはインターネットに繋がっていさえすれば、Raspberry Pi ConnectというSaaS（無料）で別パソコンから操作できます。

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

    python --version

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

    pip install RPi.GPIO

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

---

# 本番用コード

動画再生付き。

---

# 起動方法

    python MajinTest.py
    python Majin.py

---

# 画像を全画面表示する方法

Raspberry Piで画像を全画面表示するには **feh** を使うのがシンプルで安定している。

## feh のインストール

以下のコマンドでインストールする。

    sudo apt update
    sudo apt install feh

---

# 画像を全画面表示するコマンド

基本形：

    feh -F image.png

---

## よく使うオプション

    feh -F -x -Y image.png

オプションの意味：

| オプション | 説明 |
|---|---|
| -F | フルスクリーン表示 |
| -x | ウィンドウ装飾（タイトルバーなど）を消す |
| -Y | マウスカーソルを非表示 |

展示用途ではこの形がよく使われる。

    feh -F -x -Y image.png

---

# Pythonから画像を表示する場合

Pythonスクリプトから起動する場合：

```python
import subprocess

subprocess.Popen(["feh", "-F", "-x", "-Y", "image.png"])
```

---

# 表示を閉じる方法

`feh` は以下の方法で閉じられる。

    q キー
    ESC キー

またはプロセス終了。

```python
process.terminate()
```

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

MIT License
