
import json
import threading
from collections import deque
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.request import urlopen
from urllib.error import URLError
from urllib.parse import urlsplit

import paho.mqtt.client as mqtt

CAMERA = "http://127.0.0.1:8080/snapshot"

MQTT_HOST = "farlab.infosci.cornell.edu"
MQTT_PORT = 1883
MQTT_USERNAME = "idd"
MQTT_PASSWORD = "device@theFarm"

TOPICS = [
    "IDD/dancinggarden/gardener",
    "garden/gardener/weather",
    "garden/musician/state",
    "garden/musician/beat",
]

events = deque(maxlen=500)
event_lock = threading.Lock()
next_event_id = 0
mqtt_connected = False


def on_connect(client, userdata, flags, rc):
    global mqtt_connected

    mqtt_connected = (rc == 0)

    if rc == 0:
        print("MQTT connected!", flush=True)
        for topic in TOPICS:
            client.subscribe(topic)
            print("Subscribed:", topic, flush=True)
    else:
        print("MQTT connection failed:", rc, flush=True)


def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    print("MQTT disconnected:", rc, flush=True)


def on_message(client, userdata, msg):
    global next_event_id

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        print("Ignored invalid JSON:", msg.topic, flush=True)
        return

    with event_lock:
        next_event_id += 1
        events.append({
            "id": next_event_id,
            "topic": msg.topic,
            "payload": payload,
        })

    print("MQTT received:", msg.topic, payload, flush=True)


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path

        if path == "/snapshot":
            try:
                with urlopen(CAMERA, timeout=5) as response:
                    data = response.read()

                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            except (URLError, TimeoutError) as error:
                self.send_error(502, str(error))

        elif path == "/mqtt-events":
            from urllib.parse import parse_qs

            query = parse_qs(urlsplit(self.path).query)

            try:
                since = max(0, int(query.get("since", ["0"])[0]))
            except ValueError:
                since = 0

            with event_lock:
                latest_id = next_event_id
                new_events = [
                    event for event in events
                    if event["id"] > since
                ]

            result = json.dumps({
                "connected": mqtt_connected,
                "latest_id": latest_id,
                "events": new_events,
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(result)))
            self.end_headers()
            self.wfile.write(result)

        else:
            super().do_GET()


client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

try:
    client.connect_async(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    print("MQTT connection started...", flush=True)
except Exception as error:
    print("MQTT startup error:", error, flush=True)

server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)

print("Dancing Garden: http://localhost:8000", flush=True)

try:
    server.serve_forever()
finally:
    client.loop_stop()
    client.disconnect()
    server.server_close()
