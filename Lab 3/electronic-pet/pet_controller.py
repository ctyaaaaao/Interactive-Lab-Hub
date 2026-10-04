import time
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789


# ============================================================
# SETTINGS
# ============================================================

SAMPLE_RATE = 16000

# We read microphone audio in 0.1-second chunks
CHUNK_SECONDS = 0.1
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_SECONDS)
CHUNK_BYTES = CHUNK_SAMPLES * 2  # 16-bit audio = 2 bytes/sample

# From Part C: consider the user's turn finished
# after 0.8 seconds of silence
MIN_SILENCE = 0.8

# Maximum length of one spoken turn
MAX_UTTERANCE_SECONDS = 10

# How loud audio must be before we consider it speech.
# If the pet starts listening to room noise, increase this.
# If it cannot hear you, decrease this.
SPEECH_RMS_THRESHOLD = 350

AUDIO_FILE = "/tmp/pet_command.wav"


# ============================================================
# DISPLAY SETUP
# ============================================================

cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

BAUDRATE = 64000000

spi = board.SPI()

disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Landscape orientation
height = disp.width
width = disp.height

image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)

rotation = 90


# ============================================================
# BACKLIGHT
# ============================================================

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


# ============================================================
# FONTS
# ============================================================

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

title_font = ImageFont.truetype(font_path, 24)
state_font = ImageFont.truetype(font_path, 18)
small_font = ImageFont.truetype(font_path, 14)


# ============================================================
# PATHS
# ============================================================

LAB3_DIR = Path(__file__).resolve().parent.parent

possible_voice_dirs = [
    LAB3_DIR / "voices",
    LAB3_DIR / "speech-scripts",
]

VOICE_DIR = None

for folder in possible_voice_dirs:
    if (folder / "en_US-lessac-medium.onnx").exists():
        VOICE_DIR = folder
        break

if VOICE_DIR is None:
    raise FileNotFoundError(
        "Could not find en_US-lessac-medium.onnx "
        "in Lab 3/voices or Lab 3/speech-scripts."
    )


# ============================================================
# WHISPER SETUP
# ============================================================

print("Loading Whisper model...")

whisper_model = WhisperModel(
    "tiny.en",
    device="cpu",
    compute_type="int8",
)

print("Whisper model loaded.")


# ============================================================
# TEXT HELPER
# ============================================================

def centered_text(text, y, font, color):
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    text_width = bbox[2] - bbox[0]

    x = (width - text_width) // 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=color,
    )


# ============================================================
# DRAW DOG
# ============================================================

def draw_dog(state):

    # ========================================================
    # BACKGROUND
    # ========================================================

    draw.rectangle(
        (0, 0, width, height),
        fill=(248, 247, 244)
    )

    # ========================================================
    # COLORS
    # ========================================================

    dog_color = (232, 199, 143)
    outline = (20, 20, 20)
    collar = (255, 105, 105)
    tongue = (220, 80, 105)

    # Dog center
    cx = width // 2
    cy = 67

    # ========================================================
    # BODY
    # ========================================================

    # Rounded body
    draw.rounded_rectangle(
        (
            cx - 45,
            cy - 42,
            cx + 45,
            cy + 48
        ),
        radius=35,
        fill=dog_color,
        outline=outline,
        width=4
    )

    # ========================================================
    # FLOPPY EARS
    # ========================================================

    # Left ear
    draw.ellipse(
        (
            cx - 68,
            cy - 25,
            cx - 25,
            cy + 18
        ),
        fill=dog_color,
        outline=outline,
        width=4
    )

    # Cover inner line to blend ear into head
    draw.rectangle(
        (
            cx - 42,
            cy - 17,
            cx - 28,
            cy + 10
        ),
        fill=dog_color
    )

    # Right ear
    draw.ellipse(
        (
            cx + 25,
            cy - 25,
            cx + 68,
            cy + 18
        ),
        fill=dog_color,
        outline=outline,
        width=4
    )

    draw.rectangle(
        (
            cx + 28,
            cy - 17,
            cx + 42,
            cy + 10
        ),
        fill=dog_color
    )

    # ========================================================
    # LEGS
    # ========================================================

    draw.line(
        (
            cx - 20,
            cy + 25,
            cx - 17,
            cy + 47
        ),
        fill=outline,
        width=4
    )

    draw.line(
        (
            cx + 20,
            cy + 25,
            cx + 17,
            cy + 47
        ),
        fill=outline,
        width=4
    )

    # ========================================================
    # COLLAR
    # ========================================================

    draw.arc(
        (
            cx - 38,
            cy - 5,
            cx + 38,
            cy + 27
        ),
        10,
        170,
        fill=collar,
        width=5
    )

    # ========================================================
    # FACE
    # ========================================================

    if state == "sleeping":

        # Closed eyes
        draw.arc(
            (cx - 29, cy - 24, cx - 13, cy - 13),
            0,
            180,
            fill=outline,
            width=3
        )

        draw.arc(
            (cx + 13, cy - 24, cx + 29, cy - 13),
            0,
            180,
            fill=outline,
            width=3
        )

    elif state == "confused":

        # One normal eye
        draw.ellipse(
            (cx - 24, cy - 21, cx - 17, cy - 14),
            fill=outline
        )

        # Slightly raised eye
        draw.ellipse(
            (cx + 16, cy - 25, cx + 23, cy - 18),
            fill=outline
        )

    else:

        # Cute dot eyes
        draw.ellipse(
            (cx - 24, cy - 22, cx - 17, cy - 15),
            fill=outline
        )

        draw.ellipse(
            (cx + 17, cy - 22, cx + 24, cy - 15),
            fill=outline
        )

    # Nose
    draw.ellipse(
        (
            cx - 5,
            cy - 10,
            cx + 5,
            cy
        ),
        fill=outline
    )

    # ========================================================
    # MOUTH
    # ========================================================

    if state != "sleeping":

        # Smile
        draw.arc(
            (
                cx - 14,
                cy - 4,
                cx + 2,
                cy + 15
            ),
            0,
            110,
            fill=outline,
            width=3
        )

        draw.arc(
            (
                cx - 2,
                cy - 4,
                cx + 14,
                cy + 15
            ),
            70,
            180,
            fill=outline,
            width=3
        )

        # Tongue
        if state in ["awake", "playing", "listening"]:

            draw.ellipse(
                (
                    cx - 7,
                    cy + 7,
                    cx + 7,
                    cy + 22
                ),
                fill=tongue,
                outline=outline,
                width=2
            )

    # ========================================================
    # STATE-SPECIFIC DETAILS
    # ========================================================

    if state == "sleeping":

        draw.text(
            (cx + 48, 22),
            "Zzz",
            font=small_font,
            fill=(100, 100, 150)
        )

        centered_text(
            "SLEEPING",
            112,
            state_font,
            (90, 90, 140)
        )

    elif state == "awake":

        # Raised paw like your reference image
        draw.line(
            (
                cx + 38,
                cy - 4,
                cx + 45,
                cy - 39
            ),
            fill=outline,
            width=4
        )

        # Paw
        draw.ellipse(
            (
                cx + 37,
                cy - 46,
                cx + 53,
                cy - 30
            ),
            fill=dog_color,
            outline=outline,
            width=3
        )

        # Paw pads
        draw.ellipse(
            (cx + 42, cy - 42, cx + 46, cy - 38),
            fill=outline
        )

        draw.ellipse(
            (cx + 47, cy - 39, cx + 51, cy - 35),
            fill=outline
        )

        centered_text(
            "AWAKE",
            112,
            state_font,
            (70, 135, 80)
        )

    elif state == "eating":

        # Bowl
        draw.rounded_rectangle(
            (
                cx - 30,
                94,
                cx + 30,
                111
            ),
            radius=5,
            fill=(230, 100, 80),
            outline=outline,
            width=2
        )

        centered_text(
            "YUM!",
            113,
            state_font,
            (180, 75, 55)
        )

    elif state == "playing":

        # Ball
        draw.ellipse(
            (
                width - 43,
                77,
                width - 20,
                100
            ),
            fill=(90, 150, 230),
            outline=outline,
            width=2
        )

        centered_text(
            "LET'S PLAY!",
            112,
            state_font,
            (60, 100, 180)
        )

    elif state == "listening":

        # Small sound marks near ear
        draw.arc(
            (
                cx + 48,
                cy - 30,
                cx + 65,
                cy - 5
            ),
            260,
            100,
            fill=(70, 120, 200),
            width=3
        )

        centered_text(
            "LISTENING...",
            112,
            state_font,
            (60, 100, 180)
        )

    elif state == "thinking":

        draw.text(
            (cx + 45, 25),
            "...",
            font=title_font,
            fill=(130, 90, 40)
        )

        centered_text(
            "THINKING...",
            112,
            state_font,
            (130, 90, 40)
        )

    elif state == "confused":

        draw.text(
            (cx + 48, 24),
            "?",
            font=title_font,
            fill=(160, 80, 80)
        )

        centered_text(
            "CONFUSED",
            112,
            state_font,
            (160, 80, 80)
        )

    # ========================================================
    # SEND TO MINIPITFT
    # ========================================================

    disp.image(
        image,
        rotation
    )

# ============================================================
# PIPER SPEECH OUTPUT
# ============================================================

def speak(text):

    print(f'Pet: "{text}"')

    piper = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "piper",
            "--model",
            "en_US-lessac-medium",
            "--data-dir",
            str(VOICE_DIR),

            # Piper voice volume
            "--volume",
            "0.8",

            "--output-raw",
            "--",
            text,
        ],
        stdout=subprocess.PIPE,
    )

    aplay = subprocess.Popen(
        [
            "aplay",
            "-q",
            "-r",
            "22050",
            "-f",
            "S16_LE",
            "-t",
            "raw",
            "-",
        ],
        stdin=piper.stdout,
    )

    piper.stdout.close()

    aplay.communicate()
    piper.wait()

    # Avoid immediately hearing the tail end of its own voice
    time.sleep(0.3)


# ============================================================
# AUDIO HELPER
# ============================================================

def calculate_rms(audio_bytes):

    samples = np.frombuffer(
        audio_bytes,
        dtype=np.int16,
    )

    if len(samples) == 0:
        return 0

    samples = samples.astype(np.float32)

    rms = np.sqrt(
        np.mean(samples ** 2)
    )

    return rms


# ============================================================
# SAVE RECORDED AUDIO
# ============================================================

def save_wav(frames, filename):

    with wave.open(filename, "wb") as wav_file:

        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)

        wav_file.writeframes(
            b"".join(frames)
        )


# ============================================================
# AUTOMATIC LISTENING / ENDPOINTING
# ============================================================

def record_utterance():

    print()
    print("Listening...")

    draw_dog("listening")

    process = subprocess.Popen(
        [
            "arecord",
            "-q",
            "-t",
            "raw",
            "-f",
            "S16_LE",
            "-c",
            "1",
            "-r",
            str(SAMPLE_RATE),
        ],
        stdout=subprocess.PIPE,
    )

    frames = []

    speech_started = False

    silence_duration = 0.0
    utterance_duration = 0.0

    try:

        while True:

            audio_chunk = process.stdout.read(
                CHUNK_BYTES
            )

            if not audio_chunk:
                break

            rms = calculate_rms(
                audio_chunk
            )

            # ------------------------------------------------
            # Waiting for speech to begin
            # ------------------------------------------------

            if not speech_started:

                if rms > SPEECH_RMS_THRESHOLD:

                    speech_started = True

                    print("Speech detected.")

                    frames.append(
                        audio_chunk
                    )

            # ------------------------------------------------
            # Speech has started
            # ------------------------------------------------

            else:

                frames.append(
                    audio_chunk
                )

                utterance_duration += CHUNK_SECONDS

                if rms < SPEECH_RMS_THRESHOLD:

                    silence_duration += CHUNK_SECONDS

                else:

                    silence_duration = 0.0

                # Part C design decision:
                # 0.8 seconds of silence = end of turn
                if silence_duration >= MIN_SILENCE:

                    print(
                        f"End of turn detected "
                        f"after {MIN_SILENCE:.1f}s silence."
                    )

                    break

                if utterance_duration >= MAX_UTTERANCE_SECONDS:

                    print(
                        "Maximum utterance length reached."
                    )

                    break

    finally:

        process.terminate()

        try:
            process.wait(timeout=1)

        except subprocess.TimeoutExpired:
            process.kill()

    if not speech_started:

        return None

    save_wav(
        frames,
        AUDIO_FILE,
    )

    return AUDIO_FILE


# ============================================================
# SPEECH TO TEXT
# ============================================================

def transcribe_audio(filename):

    draw_dog("thinking")

    print("Thinking / transcribing...")

    segments, info = whisper_model.transcribe(
        filename,
        beam_size=1,
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    ).strip()

    print(f'You said: "{text}"')

    return text.lower()


# ============================================================
# INTENT RECOGNITION
# ============================================================

def detect_intent(text):

    # --------------------------------------------------------
    # WAKE
    # --------------------------------------------------------

    wake_phrases = [
        "wake up",
        "good morning",
        "morning",
        "are you awake",
        "get up",
        "hello",
        "hi",
    ]

    # --------------------------------------------------------
    # FEED
    # --------------------------------------------------------

    feed_phrases = [
        "feed",
        "feed you",
        "time to eat",
        "are you hungry",
        "have some food",
        "eat",
        "want some food",
        "do you want food",
        "do you want to eat",
    ]

    # --------------------------------------------------------
    # PLAY
    # --------------------------------------------------------

    play_phrases = [
        "play",
        "let's play",
        "lets play",
        "do you wanna play",
        "do you want to play",
        "can we play",
        "wanna play",
        "want to play",
        "play with me",
    ]

    # --------------------------------------------------------
    # SLEEP
    # --------------------------------------------------------

    sleep_phrases = [
        "go to sleep",
        "good night",
        "goodnight",
        "time for bed",
        "go to bed",
        "sleep",
        "bedtime",
    ]

    # --------------------------------------------------------
    # QUIT
    # --------------------------------------------------------

    quit_phrases = [
        "stop program",
        "stop listening",
        "quit program",
        "exit program",
    ]

    for phrase in quit_phrases:
        if phrase in text:
            return "quit"

    for phrase in wake_phrases:
        if phrase in text:
            return "wake"

    for phrase in feed_phrases:
        if phrase in text:
            return "feed"

    for phrase in play_phrases:
        if phrase in text:
            return "play"

    for phrase in sleep_phrases:
        if phrase in text:
            return "sleep"

    return "unknown"


# ============================================================
# PET ACTIONS
# ============================================================

def wake_up():

    draw_dog("awake")

    speak(
        "Good morning! I'm awake!"
    )


def feed():

    draw_dog("eating")

    speak(
        "Yum! Thank you!"
    )

    time.sleep(1)

    draw_dog("awake")


def play():

    draw_dog("playing")

    speak(
        "Yay! Let's play!"
    )

    time.sleep(1)

    draw_dog("awake")


def sleep_pet():

    draw_dog("sleeping")

    speak(
        "Good night!"
    )


def unknown():

    draw_dog("confused")

    speak(
        "Sorry, I didn't understand."
    )

    time.sleep(1)

    draw_dog("awake")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("Voice-Controlled Electronic Pet")
    print("===============================")
    print()
    print("Example things you can say:")
    print('- "Good morning!"')
    print('- "Are you hungry?"')
    print('- "Do you wanna play?"')
    print('- "Good night!"')
    print()
    print(
        f"Turn ends after "
        f"{MIN_SILENCE:.1f} seconds of silence."
    )
    print()
    print(
        'Say "stop program" to quit.'
    )

    # Pet starts asleep
    draw_dog("sleeping")

    try:

        while True:

            # ------------------------------------------------
            # Listen until user speaks and then pauses
            # ------------------------------------------------

            audio_file = record_utterance()

            if audio_file is None:
                continue

            # ------------------------------------------------
            # Speech → text
            # ------------------------------------------------

            text = transcribe_audio(
                audio_file
            )

            if not text:

                print(
                    "No speech was recognized."
                )

                unknown()

                continue

            # ------------------------------------------------
            # Text → intent
            # ------------------------------------------------

            intent = detect_intent(
                text
            )

            print(
                f"Detected intent: {intent}"
            )

            # ------------------------------------------------
            # Intent → pet action
            # ------------------------------------------------

            if intent == "wake":

                wake_up()

            elif intent == "feed":

                feed()

            elif intent == "play":

                play()

            elif intent == "sleep":

                sleep_pet()

            elif intent == "quit":

                speak(
                    "Bye bye!"
                )

                print(
                    "Electronic pet stopped."
                )

                break

            else:

                unknown()

    except KeyboardInterrupt:

        print()
        print(
            "Electronic pet stopped."
        )


if __name__ == "__main__":
    main()