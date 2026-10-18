"""
	Reading distance from the laser based VL53L1X
	This example prints the distance to an object. If you are getting weird
	readings, be sure the vacuum tape has been removed from the sensor.
"""

import qwiic
import time

print("VL53L1X Qwiic Test\n")
sensor_configs = [
	(1, 0x29),
	(2, 0x2A),
]
sensors = []

for sensor_number, address in sensor_configs:
	sensor = qwiic.QwiicVL53L1X(address=address)
	try:
		if sensor.sensor_init() == 0:
			sensors.append((sensor_number, sensor))
			print(f"Sensor {sensor_number} online at 0x{address:02X}")
	except OSError as error:
		print(f"Sensor {sensor_number} at 0x{address:02X} unavailable: {error}")

if len(sensors) != len(sensor_configs):
	raise SystemExit("Connect both sensors and assign them the addresses shown above.")

while True:
	try:
		for _, sensor in sensors:
			sensor.start_ranging()
		time.sleep(.005)

		for sensor_number, sensor in sensors:
			distance = sensor.get_distance()
			distanceInches = distance / 25.4
			distanceFeet = distanceInches / 12.0
			print("Sensor %d - Distance(mm): %s Distance(ft): %s" %
				(sensor_number, distance, distanceFeet))

		for _, sensor in sensors:
			sensor.stop_ranging()
		time.sleep(.005)

	except Exception as e:
		print(e)