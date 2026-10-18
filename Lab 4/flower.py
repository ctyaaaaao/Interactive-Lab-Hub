"""Flower output for Feast Automata (servo drives the flower directly).

    import flower
    flower.correct()   # right utensil -> elegant twirl + minuet
    flower.wrong()     # wrong utensil -> head shake + sad trombone

Run `python flower.py` to test with the keyboard.
Set FLOWER_FAKE=1 to print actions instead of moving the servo.
"""
import math
import os
import shutil
import subprocess
import threading
import time

SERVO_CH = 0
FACE = 90           # servo angle where the flower faces the user
TWIRL_LEFT = 10     # how far the twirl turns each way; keep inside the servo's range
TWIRL_RIGHT = 170
TWIRL_SPEED = 140   # degrees per second during the twirl
TWIRLS = 3          # left-right twirls per correct pick
SHAKE_DEG = 20      # head-shake size to each side
SHAKES = 3

SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
CORRECT_SOUND = "Claude Debussy - Clair de lune (From Twilight).mp3"
WRONG_SOUND = "wrong.wav"
AUDIO_DEVICE = "plughw:UACDemoV10,0"  # USB speaker (by name, so the card number can change)
DEBUSSY_VOLUME = "4.0"

FAKE = os.environ.get("FLOWER_FAKE") == "1"

if not FAKE:
    import pi_servo_hat
    # 0.5–2.5 ms covers the MS18's full ~180°; narrow to 0.6/2.4 if it buzzes at the ends
    _servo = pi_servo_hat.PiServoHat(min_pt=0.5, max_pt=2.5)
    _servo.restart()

_angle = FACE
_player = None
_playing_sound = None
_auto_thread = None
_auto_stop = threading.Event()
_auto_wake = threading.Event()
_auto_result = 1
_auto_lock = threading.Lock()


def stop_sound():
    """Stop the active player and wait until the audio device is released."""
    global _player, _playing_sound
    if _player and _player.poll() is None:
        _player.terminate()
        try:
            _player.wait(timeout=1)
        except subprocess.TimeoutExpired:
            _player.kill()
            _player.wait()
    _player = None
    _playing_sound = None


def play(name, wait=False):
    """Play a sound, preventing overlapping processes on the audio device."""
    global _player, _playing_sound
    if _player and _player.poll() is None and _playing_sound == name:
        if wait:
            _player.wait()
        return

    stop_sound()
    path = os.path.join(SOUND_DIR, name)
    if FAKE or not os.path.exists(path):
        print(f"[flower] (sound) {name}")
        return
    if shutil.which("ffplay"):
        cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
        if name == CORRECT_SOUND:
            cmd[1:1] = ["-af", f"volume={DEBUSSY_VOLUME}"]
    elif path.endswith(".mp3") and shutil.which("cvlc"):
        cmd = ["cvlc", "--intf", "dummy", "--play-and-exit", path]
    else:
        cmd = ["aplay", "-q", path]
        if AUDIO_DEVICE:
            cmd[1:1] = ["-D", AUDIO_DEVICE]
    try:
        _player = subprocess.Popen(cmd, stderr=subprocess.DEVNULL)
    except OSError as error:
        print(f"[flower] audio unavailable: {error}")
        _player = None
        _playing_sound = None
        return
    _playing_sound = name
    if wait:
        _player.wait()
        _player = None
        _playing_sound = None


def start_error_sound():
    """Start wrong.wav and return its process so the motor can move immediately."""
    stop_sound()
    path = os.path.join(SOUND_DIR, WRONG_SOUND)
    if FAKE or not os.path.exists(path):
        print(f"[flower] (sound) {WRONG_SOUND}")
        return None

    if shutil.which("ffplay"):
        cmd = [
            "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
            "-volume", "100", path,
        ]
    else:
        cmd = ["aplay", "-q", path]

    try:
        return subprocess.Popen(cmd, stderr=subprocess.DEVNULL)
    except OSError as error:
        print(f"[flower] error sound unavailable: {error}")
        return None


def _write(angle):
    if not FAKE:
        _servo.move_servo_position(SERVO_CH, angle, 180)  # 180 = angles are real degrees


def move_to(target, duration):
    """Ease to target servo angle: slow start, slow stop."""
    global _angle
    start = _angle
    steps = max(1, int(duration / 0.02))
    for i in range(1, steps + 1):
        t = (1 - math.cos(math.pi * i / steps)) / 2
        _angle = start + (target - start) * t
        _write(_angle)
        time.sleep(0.02)


def _sweep(target):
    move_to(target, abs(target - _angle) / TWIRL_SPEED)


def home():
    move_to(FACE, 0.6)


def correct():
    print("[flower] correct -> twirl")
    play(CORRECT_SOUND)
    home()
    for _ in range(TWIRLS):
        _sweep(TWIRL_RIGHT)
        _sweep(TWIRL_LEFT)
    _sweep(FACE)


def wrong():
    print("[flower] wrong -> shake")
    error_player = start_error_sound()
    home()
    for _ in range(SHAKES):
        move_to(FACE - SHAKE_DEG, 0.15)
        move_to(FACE + SHAKE_DEG, 0.15)
    move_to(FACE, 0.15)
    if error_player:
        error_player.wait()
    play(CORRECT_SOUND)


def _automatic_loop():
    while not _auto_stop.is_set():
        with _auto_lock:
            result = _auto_result

        if result == 1:
            correct()
        else:
            wrong()
            _auto_wake.wait()
            _auto_wake.clear()


def start_automatic(result=1):
    """Start repeating correct reactions until the result changes to 2."""
    global _auto_thread, _auto_result
    with _auto_lock:
        _auto_result = result
    _auto_stop.clear()
    _auto_wake.clear()
    _auto_thread = threading.Thread(target=_automatic_loop, daemon=True)
    _auto_thread.start()


def set_automatic_result(result):
    """Set 1 for correct looping or 2 for a wrong reaction."""
    global _auto_result
    if result not in (1, 2):
        raise ValueError("automatic result must be 1 or 2")
    with _auto_lock:
        _auto_result = result
    _auto_wake.set()


def stop_automatic():
    """Stop the automatic reaction worker."""
    _auto_stop.set()
    _auto_wake.set()
    if _auto_thread and _auto_thread.is_alive():
        _auto_thread.join()
    stop_sound()


_write(_angle)

if __name__ == "__main__":
    print("1 = correct (twirl)  2 = wrong (shake)  0 = home  <number> = servo angle  q = quit")
    try:
        while (cmd := input("> ").strip()) != "q":
            if cmd == "1":
                correct()
            elif cmd == "2":
                wrong()
            elif cmd == "0":
                home()
            else:
                try:
                    move_to(float(cmd), 0.5)
                    print(f"servo at {_angle:.0f}")
                except ValueError:
                    pass
    except KeyboardInterrupt:
        pass
    stop_sound()
    home()