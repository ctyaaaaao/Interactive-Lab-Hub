#!/usr/bin/env python3
"""Synthesize the flower's two sound effects (standard library only).

    correct.wav  music-box rendition of Bach's Minuet in G (public-domain melody)
    wrong.wav    sad-trombone "wah wah wah waaah"

Run:  python3 make_sounds.py
"""
import math
import os
import struct
import wave

SR = 44100


def midi_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


NOTE = {"F#3": 54, "G3": 55, "A3": 57, "B3": 59, "C4": 60, "D3": 50, "D4": 62,
        "F#4": 66, "G4": 67, "A4": 69, "B4": 71, "C5": 72, "D5": 74, "E5": 76,
        "F#5": 78, "G5": 79}


def write_wav(name, samples):
    peak = max(abs(s) for s in samples) or 1.0
    scale = 0.85 / peak
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(s * scale * 32767)) for s in samples))
    print(f"wrote {name}  ({len(samples) / SR:.1f} s)")


def reverb(buf, taps=((0.043, 0.28), (0.071, 0.2), (0.113, 0.12))):
    out = buf[:]
    for delay, gain in taps:
        d = int(delay * SR)
        for i in range(d, len(out)):
            out[i] += gain * out[i - d]
    return out


# ---------- correct: music box minuet ----------

BEAT = 0.40   # seconds per quarter note

# Bach, Minuet in G (BWV Anh. 114): bars 1-6, then the closing bars 15-16
MELODY = [
    ("D5", 1), ("G4", .5), ("A4", .5), ("B4", .5), ("C5", .5),
    ("D5", 1), ("G4", 1), ("G4", 1),
    ("E5", 1), ("C5", .5), ("D5", .5), ("E5", .5), ("F#5", .5),
    ("G5", 1), ("G4", 1), ("G4", 1),
    ("C5", 1), ("D5", .5), ("C5", .5), ("B4", .5), ("A4", .5),
    ("B4", 1), ("C5", .5), ("B4", .5), ("A4", .5), ("G4", .5),
    ("A4", 1), ("B4", .5), ("A4", .5), ("G4", .5), ("F#4", .5),
    ("G4", 3),
]
BASS = ["G3", "B3", "C4", "B3", "A3", "G3", "D3", "G3"]   # one per bar


def music_box_note(buf, start, freq, amp, ring=2.2):
    i0 = int(start * SR)
    for k in range(int(ring * SR)):
        if i0 + k >= len(buf):
            break
        t = k / SR
        env = math.exp(-t / 0.9) * (1 - math.exp(-t / 0.003))
        s = (math.sin(2 * math.pi * freq * t)
             + 0.25 * math.exp(-t / 0.3) * math.sin(2 * math.pi * 2 * freq * t)
             + 0.12 * math.exp(-t / 0.08) * math.sin(2 * math.pi * 3.98 * freq * t))
        buf[i0 + k] += amp * env * s


def correct():
    beats = sum(b for _, b in MELODY)
    buf = [0.0] * int((beats * BEAT + 2.5) * SR)
    t = 0.0
    for name, b in MELODY:
        music_box_note(buf, t, midi_hz(NOTE[name]), 0.6)
        t += b * BEAT
    for bar, name in enumerate(BASS):
        music_box_note(buf, bar * 3 * BEAT, midi_hz(NOTE[name]), 0.32, ring=2.6)
    write_wav("correct.wav", reverb(buf))


# ---------- wrong: sad trombone ----------

def trombone_note(buf, start, dur, freq, wobble=False):
    i0 = int(start * SR)
    phase = 0.0
    n = int(dur * SR)
    for k in range(n):
        t = k / SR
        f = freq
        if wobble:   # slow, wide comic vibrato and a droop at the end
            f *= 1 + 0.025 * math.sin(2 * math.pi * 5.2 * t) * min(1, t / 0.25)
            f *= 1 - 0.04 * max(0.0, (t - dur + 0.4) / 0.4)
        phase += 2 * math.pi * f / SR
        # "wah": brightness rises then falls over each note
        bright = 0.25 + 0.6 * math.sin(math.pi * min(1.0, t / max(dur, 0.45)))
        s = sum(bright ** (h - 1) / h * math.sin(h * phase) for h in range(1, 9))
        env = min(1.0, t / 0.03) * min(1.0, (dur - t) / 0.08)
        buf[i0 + k] += 0.5 * env * s


def wrong():
    notes = [(233.08, 0.42), (220.0, 0.42), (207.65, 0.42), (196.0, 1.35)]  # Bb A Ab G
    buf = [0.0] * int((sum(d for _, d in notes) + 0.3 + 0.6) * SR)
    t = 0.0
    for i, (f, d) in enumerate(notes):
        trombone_note(buf, t, d, f, wobble=(i == len(notes) - 1))
        t += d + 0.06
    write_wav("wrong.wav", reverb(buf, taps=((0.05, 0.18), (0.09, 0.1))))


if __name__ == "__main__":
    correct()
    wrong()
