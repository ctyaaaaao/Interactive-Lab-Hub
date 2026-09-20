import time
import math
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789


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
# FONT
# ============================================================

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Large font for hour number
hour_font = ImageFont.truetype(font_path, 26)


# ============================================================
# BACKLIGHT
# ============================================================

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


# ============================================================
# BUTTONS
# ============================================================

# Button A: sun/moon trajectory
buttonA = digitalio.DigitalInOut(board.D23)
buttonA.switch_to_input(pull=digitalio.Pull.UP)

# Button B: toggle fast-time mode
buttonB = digitalio.DigitalInOut(board.D24)
buttonB.switch_to_input(pull=digitalio.Pull.UP)


# ============================================================
# FAST TIME SETTINGS
# ============================================================

# 1 real second = 1 simulated hour
FAST_HOURS_PER_REAL_SECOND = 1.0

fast_mode = False
fast_start_real_time = 0
fast_start_hour = 0


# ============================================================
# SKY COLORS
# ============================================================

sky_keyframes = [
    (0.0,  (10, 18, 50)),       # Midnight
    (5.0,  (20, 30, 70)),       # Before sunrise
    (6.5,  (255, 160, 100)),    # Sunrise
    (9.0,  (80, 170, 255)),     # Morning
    (16.0, (80, 170, 255)),     # Afternoon
    (18.5, (255, 120, 80)),     # Sunset
    (20.0, (40, 40, 100)),      # Evening
    (24.0, (10, 18, 50)),       # Midnight
]


def interpolate_color(color1, color2, amount):
    r = int(color1[0] + (color2[0] - color1[0]) * amount)
    g = int(color1[1] + (color2[1] - color1[1]) * amount)
    b = int(color1[2] + (color2[2] - color1[2]) * amount)

    return (r, g, b)


def get_sky_color(hour):
    """
    Smoothly transition the sky color throughout the day.
    """

    hour = hour % 24

    for i in range(len(sky_keyframes) - 1):

        start_hour, start_color = sky_keyframes[i]
        end_hour, end_color = sky_keyframes[i + 1]

        if start_hour <= hour <= end_hour:

            amount = (
                (hour - start_hour)
                / (end_hour - start_hour)
            )

            return interpolate_color(
                start_color,
                end_color,
                amount
            )

    return sky_keyframes[0][1]


# ============================================================
# SUN
# ============================================================

def draw_sun(x, y):
    radius = 11

    draw.ellipse(
        (
            x - radius,
            y - radius,
            x + radius,
            y + radius
        ),
        fill=(255, 225, 60)
    )


# ============================================================
# MOON
# ============================================================

def draw_moon(x, y, background_color):
    radius = 11

    # Full moon circle
    draw.ellipse(
        (
            x - radius,
            y - radius,
            x + radius,
            y + radius
        ),
        fill=(245, 245, 220)
    )

    # Cover part to create crescent
    draw.ellipse(
        (
            x - 3,
            y - radius,
            x + radius + 6,
            y + radius
        ),
        fill=background_color
    )


# ============================================================
# SUN / MOON TRAJECTORY POSITION
# ============================================================

def get_arc_position(progress):

    start_x = 15
    end_x = width - 15

    horizon_y = height - 15
    arc_height = 80

    x = start_x + progress * (end_x - start_x)

    y = (
        horizon_y
        - math.sin(progress * math.pi) * arc_height
    )

    return int(x), int(y)


def draw_trajectory():

    for i in range(31):

        progress = i / 30

        x, y = get_arc_position(progress)

        draw.ellipse(
            (
                x - 1,
                y - 1,
                x + 1,
                y + 1
            ),
            fill=(230, 230, 230)
        )


# ============================================================
# CONVERT 24-HOUR TIME TO 12-HOUR NUMBER
# ============================================================

def get_hour_number(hour):

    hour_int = int(hour) % 24

    hour_12 = hour_int % 12

    if hour_12 == 0:
        hour_12 = 12

    return str(hour_12)


# ============================================================
# CENTER TEXT
# ============================================================

def draw_centered_hour(hour_text, color):

    bbox = draw.textbbox(
        (0, 0),
        hour_text,
        font=hour_font
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2

    # Actual middle of screen
    y = (height - text_height) // 2 - bbox[1]

    draw.text(
        (x, y),
        hour_text,
        font=hour_font,
        fill=color
    )


# ============================================================
# DRAW NORMAL CLOCK FRAME
# ============================================================

def draw_clock(hour):

    sky_color = get_sky_color(hour)

    # Background
    draw.rectangle(
        (0, 0, width, height),
        fill=sky_color
    )

    # Convert to 12-hour number
    hour_text = get_hour_number(hour)

    # Choose readable text color
    brightness = (
        sky_color[0]
        + sky_color[1]
        + sky_color[2]
    ) / 3

    if brightness > 150:
        text_color = (25, 35, 55)
    else:
        text_color = (255, 255, 255)

    # Time number exactly in center
    draw_centered_hour(
        hour_text,
        text_color
    )

    # Sun / moon directly above time
    body_x = width // 2
    body_y = 27

    if 6 <= hour % 24 < 18:

        draw_sun(
            body_x,
            body_y
        )

    else:

        draw_moon(
            body_x,
            body_y,
            sky_color
        )

    disp.image(
        image,
        rotation
    )


# ============================================================
# GET REAL CURRENT TIME
# ============================================================

def get_real_hour():

    now = time.localtime()

    return (
        now.tm_hour
        + now.tm_min / 60
        + now.tm_sec / 3600
    )


# ============================================================
# GET DISPLAY TIME
# ============================================================

def get_display_hour():

    if not fast_mode:

        return get_real_hour()

    elapsed = (
        time.monotonic()
        - fast_start_real_time
    )

    simulated_hour = (
        fast_start_hour
        + elapsed * FAST_HOURS_PER_REAL_SECOND
    )

    return simulated_hour % 24


# ============================================================
# SUN TRAJECTORY ANIMATION
# ============================================================

def animate_sun():

    steps = 60

    for i in range(steps + 1):

        progress = i / steps

        fake_hour = 6 + progress * 12

        sky_color = get_sky_color(fake_hour)

        draw.rectangle(
            (0, 0, width, height),
            fill=sky_color
        )

        draw_trajectory()

        x, y = get_arc_position(progress)

        draw_sun(x, y)

        disp.image(
            image,
            rotation
        )

        time.sleep(0.04)


# ============================================================
# MOON TRAJECTORY ANIMATION
# ============================================================

def animate_moon():

    steps = 60

    for i in range(steps + 1):

        progress = i / steps

        # 18 -> 30 means 6 PM -> 6 AM
        fake_hour = 18 + progress * 12

        display_hour = fake_hour % 24

        sky_color = get_sky_color(display_hour)

        draw.rectangle(
            (0, 0, width, height),
            fill=sky_color
        )

        draw_trajectory()

        x, y = get_arc_position(progress)

        draw_moon(
            x,
            y,
            sky_color
        )

        disp.image(
            image,
            rotation
        )

        time.sleep(0.04)


# ============================================================
# MAIN LOOP
# ============================================================

print("Sky Clock started")
print("GPIO23: show sun/moon trajectory")
print("GPIO24: toggle fast-time mode")

previous_A = True
previous_B = True


while True:

    # Current displayed time
    display_hour = get_display_hour()

    # Draw clock
    draw_clock(display_hour)


    # --------------------------------------------------------
    # READ BUTTONS
    # --------------------------------------------------------

    current_A = buttonA.value
    current_B = buttonB.value


    # ========================================================
    # BUTTON A
    # Show sun / moon trajectory
    # ========================================================

    if previous_A and not current_A:

        print("GPIO23 pressed")

        if 6 <= display_hour < 18:

            print("Sun trajectory")
            animate_sun()

        else:

            print("Moon trajectory")
            animate_moon()


    # ========================================================
    # BUTTON B
    # Toggle fast-time mode
    # ========================================================

    if previous_B and not current_B:

        print("GPIO24 pressed")

        if not fast_mode:

            # Start accelerated time from current real time
            fast_start_hour = get_real_hour()
            fast_start_real_time = time.monotonic()

            fast_mode = True

            print("FAST MODE ON")

        else:

            fast_mode = False

            print("FAST MODE OFF - back to real time")


    previous_A = current_A
    previous_B = current_B

    time.sleep(0.03)