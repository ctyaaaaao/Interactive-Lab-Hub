import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
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

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for full color.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Button A for toggling fast-time mode
buttonA = digitalio.DigitalInOut(board.D23)
buttonA.switch_to_input(pull=digitalio.Pull.UP)

# Fast-time state
fast_mode = False
fast_start_real = 0
fast_start_hour = 0

def get_sky_color(hour):
    """
    Return a background color based on the current hour.
    """

    hour = hour % 24

    if 5 <= hour < 7:
        # Sunrise
        return (255, 170, 100)

    elif 7 <= hour < 17:
        # Day
        return (80, 170, 255)

    elif 17 <= hour < 19:
        # Sunset
        return (255, 120, 80)

    else:
        # Night
        return (20, 30, 80)


def get_real_hour():
    """
    Return the real current time as a decimal hour.
    Example: 13:30 -> 13.5
    """

    now = time.localtime()

    return (
        now.tm_hour
        + now.tm_min / 60
        + now.tm_sec / 3600
    )


def get_display_hour():

    if not fast_mode:
        return get_real_hour()

    elapsed = time.monotonic() - fast_start_real

    # Fast mode:
    # 1 real second = 5 simulated hours
    simulated_hour = (
        fast_start_hour
        + elapsed * 5
    )

    return simulated_hour % 24

def draw_centered_time(hour):
    """
    Display hour in 12-hour format at the center of the screen.
    """

    hour_int = int(hour) % 24

    hour_12 = hour_int % 12

    if hour_12 == 0:
        hour_12 = 12

    hour_text = str(hour_12)

    # Measure text size
    bbox = draw.textbbox(
        (0, 0),
        hour_text,
        font=font
    )

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center text
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2 - bbox[1]

    draw.text(
        (text_x, text_y),
        hour_text,
        font=font,
        fill=(255, 255, 255)
    )

previous_button = True

while True:

    # Get the current display hour
    display_hour = get_display_hour()

    # Get sky background color
    sky_color = get_sky_color(display_hour)

    # Draw background
    draw.rectangle(
        (0, 0, width, height),
        outline=0,
        fill=sky_color
    )

    # Draw numerical hour in the center
    draw_centered_time(display_hour)

    # Display image
    disp.image(image, rotation)


    # Read button
    current_button = buttonA.value


    # Detect new button press
    if previous_button and not current_button:

        if not fast_mode:

            # Start fast mode
            fast_start_hour = get_real_hour()
            fast_start_real = time.monotonic()

            fast_mode = True

            print("FAST MODE ON")

        else:

            # Return to real time
            fast_mode = False

            print("FAST MODE OFF")


    previous_button = current_button

    time.sleep(0.03)