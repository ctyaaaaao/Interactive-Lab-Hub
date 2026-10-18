import time

import board
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

# These are the raw readings measured when an object is about 0.5 inches away.
# Calibrate these two values with the actual sensor boards and object.
TOUCH_DISTANCE_INCHES = 0.5
TOUCH_RAW_REFERENCE = {
	"vcnl4040": 1000,
	"apds9960": 200,
}


def normalize_distance(raw_value, sensor_type):
	"""Estimate distance in inches from each sensor's calibrated raw scale."""
	if raw_value <= 0:
		return float("inf")

	reference = TOUCH_RAW_REFERENCE[sensor_type]
	distance = TOUCH_DISTANCE_INCHES * reference / raw_value
	return max(0.0, distance)


def proximity_label(distance_inches):
	return "touching" if distance_inches <= TOUCH_DISTANCE_INCHES else "not touching"

mux = qwiic_tca9548a.QwiicTCA9548A(address=MUX_ADDRESS)
if not mux.connected:
	raise SystemExit(f"Qwiic TCA9548A mux not found at 0x{MUX_ADDRESS:02X}.")

sensors = []
print("Qwiic distance sensor test\n")

for sensor_name, channel, sensor_type in sensor_configs:
	try:
		mux.disable_all()
		mux.enable_channels(channel)
		if sensor_type == "vcnl4040":
			sensor = qwiic_proximity.QwiicProximity()
			if not sensor.connected or not sensor.begin():
				raise OSError("VCNL4040 not found or failed initialization")
		else:
			sensor = APDS9960(board.I2C())
			sensor.enable_proximity = True
		sensors.append((sensor_name, channel, sensor_type, sensor))
		print(f"{sensor_name} online on mux channel {channel}")
	except (OSError, RuntimeError, ValueError, TypeError) as error:
		print(f"{sensor_name} on mux channel {channel} unavailable: {error}")

if not sensors:
	raise SystemExit("No distance sensors were found on mux channels 0, 1, or 2.")

try:
	while True:
		readings = []
		for sensor_name, channel, sensor_type, sensor in sensors:
			try:
				mux.disable_all()
				mux.enable_channels(channel)
				if sensor_type == "vcnl4040":
					raw_value = sensor.get_proximity()
				else:
					raw_value = sensor.proximity

				distance_inches = normalize_distance(raw_value, sensor_type)
				if distance_inches == float("inf"):
					distance_text = "far"
				else:
					distance_text = f"{distance_inches:.2f} in"
				readings.append(
					f"{sensor_name}: raw={raw_value}, "
					f"distance={distance_text}, {proximity_label(distance_inches)}"
				)
			except (OSError, RuntimeError, ValueError, TypeError) as error:
				readings.append(f"{sensor_name}: unavailable ({error})")

		print(" | ".join(readings))
		time.sleep(0.25)
except KeyboardInterrupt:
	print("\nTest stopped.")
finally:
	mux.disable_all()