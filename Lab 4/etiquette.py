import time

import board
import flower
import qwiic_button
import qwiic_proximity
import qwiic_tca9548a
from adafruit_apds9960.apds9960 import APDS9960


MUX_ADDRESS = 0x70
sensor_configs = [
	("VCNL4040 sensor 3", 3, "vcnl4040"),
	("VCNL4040 sensor 2", 2, "vcnl4040"),
	("VCNL4040 sensor 1", 1, "vcnl4040"),
	("APDS-9960 sensor 4", 4, "apds9960"),
	("APDS-9960 sensor 5", 5, "apds9960"),
]

TOUCH_RAW_THRESHOLD = {
	1: 10,
	2: 10,
	3: 10,
	4: 5,
	5: 5,
}
STATE_CONFIRMATION_READS = 3

i2c = board.I2C()
mux = qwiic_tca9548a.QwiicTCA9548A(address=MUX_ADDRESS)
if not mux.connected:
	raise SystemExit(f"Qwiic TCA9548A mux not found at 0x{MUX_ADDRESS:02X}.")

sensors = {}

for sensor_name, channel, sensor_type in sensor_configs:
	try:
		mux.disable_all()
		mux.enable_channels(channel)
		if sensor_type == "vcnl4040":
			sensor = qwiic_proximity.QwiicProximity()
			if not sensor.connected or not sensor.begin():
				raise OSError("VCNL4040 not found or failed initialization")
		else:
			sensor = APDS9960(i2c)
			sensor.enable_proximity = True
		slot = int(sensor_name.rsplit(" ", 1)[1])
		sensors[slot] = (sensor_name, channel, sensor_type, sensor)
	except (OSError, RuntimeError, ValueError, TypeError) as error:
		print(f"{sensor_name} on mux channel {channel} unavailable: {error}")

if set(sensors) != set(range(1, 6)):
	raise SystemExit("All five sensors must be online before starting the game.")

mux.disable_all()
mux.enable_channels(6)
button = qwiic_button.QwiicButton()
if not button.begin():
	raise SystemExit("Qwiic button not found on mux channel 6.")

states = {}


def read_sensor_state(slot):
	_, channel, sensor_type, sensor = sensors[slot]
	for attempt in range(3):
		mux.disable_all()
		mux.enable_channels(channel)
		try:
			if sensor_type == "vcnl4040":
				raw_value = sensor.get_proximity()
			else:
				raw_value = sensor.proximity
			return raw_value >= TOUCH_RAW_THRESHOLD[slot]
		except OSError:
			if attempt == 2:
				raise
			time.sleep(0.02)


def read_all_sensor_states():
	return {slot: read_sensor_state(slot) for slot in sensors}


def state_name(game_state):
	return ("soup", "salad", "main")[game_state]


def allowed_slots(game_state):
	return ({1}, {2, 5}, {3, 4})[game_state]


def wrong_order_slots(game_state, sensor_states):
	return {
		slot
		for slot, is_touching in sensor_states.items()
		if slot not in allowed_slots(game_state) and not is_touching
	}


def print_wrong_order(slots):
	for _ in sorted(slots):
		print("wrong order.")


def set_flower_result(wrong_slots):
	flower.set_automatic_result(2 if wrong_slots else 1)


game_state = 0
states = read_all_sensor_states()
print("Initial sensor states:")
for slot in sorted(states):
		print(f"Slot {slot}: {'touching' if states[slot] else 'not touching'}")
print(f"Game state: {state_name(game_state)}")
wrong_slots = wrong_order_slots(game_state, states)
print_wrong_order(wrong_slots)
flower.start_automatic(2 if wrong_slots else 1)

button_was_pressed = False
pending_states = states.copy()
pending_counts = {slot: 0 for slot in states}

try:
	while True:
		try:
			observed_states = read_all_sensor_states()
		except OSError as error:
			print(f"Sensor read error; retrying: {error}")
			time.sleep(0.25)
			continue
		for slot in sorted(observed_states):
			if observed_states[slot] == states[slot]:
				pending_counts[slot] = 0
				pending_states[slot] = observed_states[slot]
				continue

			if observed_states[slot] == pending_states[slot]:
				pending_counts[slot] += 1
			else:
				pending_states[slot] = observed_states[slot]
				pending_counts[slot] = 1

			if pending_counts[slot] >= STATE_CONFIRMATION_READS:
				states[slot] = observed_states[slot]
				pending_counts[slot] = 0
				print(
					f"Slot {slot}: "
					f"{'touching' if states[slot] else 'not touching'}"
				)

		current_wrong_slots = wrong_order_slots(game_state, states)
		print_wrong_order(current_wrong_slots - wrong_slots)
		if current_wrong_slots != wrong_slots:
			set_flower_result(current_wrong_slots)
		wrong_slots = current_wrong_slots

		mux.disable_all()
		mux.enable_channels(6)
		button_is_pressed = button.is_button_pressed()
		if button_is_pressed and not button_was_pressed:
			if game_state < 2:
				game_state += 1
				print(f"Game state: {state_name(game_state)}")
				wrong_slots = wrong_order_slots(game_state, states)
				print_wrong_order(wrong_slots)
				set_flower_result(wrong_slots)
		button_was_pressed = button_is_pressed
		time.sleep(0.25)
except KeyboardInterrupt:
	print("\nGame stopped.")
finally:
	flower.stop_automatic()
	mux.disable_all()