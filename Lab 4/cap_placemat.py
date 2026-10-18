
import time
import board
import busio

import adafruit_mpr121

i2c = busio.I2C(board.SCL, board.SDA)

mpr121 = adafruit_mpr121.MPR121(i2c)

item_names = {
    6: "small fork",
    7: "big fork",
    9: "big knife",
    10: "small knife",
    11: "spoon",
}

previous_states = [mpr121[i].value for i in range(12)]

while True:
    for i in range(12):
        current_state = mpr121[i].value
        if i in item_names and current_state != previous_states[i]:
            action = "returned" if current_state else "removed"
            print(f"{item_names[i]} {action}")
        previous_states[i] = current_state
    time.sleep(0.25)  # Small delay to keep from spamming output messages.
