# Distributed Interaction

**NAMES OF COLLABORATORS HERE**

Tzu-Yao (Regina) Chang (tc845), Jianing Li (jl4837), Aurora Jiaxin Shen

---

<!-- ## Prep

1. Pull the new changes
2. Read: [The Presence Table](https://dl.acm.org/doi/10.1145/1935701.1935800) ([video](https://vimeo.com/15932020)) -->

## Overview

Build interactive systems where **multiple devices communicate over a network** using MQTT messaging. Work in teams of 3+ with Raspberry Pis.

**Parts:**
- A: Learn MQTT messaging
- B: Try collaborative pixel grid demo  
- C: Build your own distributed system

---

## Part A: MQTT Messaging

<!-- MQTT = lightweight messaging for IoT. Publish/subscribe model with central broker.

**Concepts:**
- **Broker**: `farlab.infosci.cornell.edu:1883`
- **Topic**: Like `IDD/bedroom/temperature` (use `#` wildcard)
- **Publish/Subscribe**: Send and receive messages

**Install MQTT tools on your Pi:**
```bash
sudo apt-get update
sudo apt-get install -y mosquitto-clients
```

**Test it:**

**Subscribe to messages (listener):**
```bash
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/#' -u idd -P 'device@theFarm'
```

**Publish a message (sender):**
```bash
mosquitto_pub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/test/yourname' -m 'Hello!' -u idd -P 'device@theFarm'
```

> **💡 Tips:**
> - Replace `yourname` with your actual name in the topic
> - Use single quotes around the password: `'device@theFarm'`
> - For your own projects, publish under your team's topic space: `IDD/<yourteam>/...` (for example `IDD/team3/bedroom/light`). Everyone shares one broker login, so anything you publish can reach everyone's projects.

**🔧 Debug Tool:** View all MQTT messages in real-time at `http://farlab.infosci.cornell.edu:5001`

![MQTT Explorer showing messages](imgs/MQTT-explorer.png) -->

**💡 Brainstorm 5 ideas for messaging between devices**

MQTT agrees on almost nothing in advance: you invent the topics and what the messages mean. Smart-home standards like Matter fix the vocabulary instead (every "light" behaves the same). Keep this trade-off in mind when you design your topics in Part C.

- 1. Distant Dining Companion
Inspired by our previous *Distant Dining Companion* concept, this system connects two people dining in different locations. When a sensor detects someone sitting down at one dining table, the other person's device responds by lighting up LEDs, rotating a flower, or playing music, creating a sense of shared presence despite the physical distance.

- 2. Cooperative Trust Game
Three players collaboratively control a virtual plate suspended by three ropes, each pulled by a character from a different direction. Using joysticks or rotary encoders, players must coordinate their movements to guide a ball on the plate into a cup at a designated location on the screen. Obstacles along the way may break the ropes, requiring careful communication and teamwork.

- 3. Collaborative Music Creation
Three players use different sensors to create music together. One controls melody and pitch using a joystick, another adjusts volume or sound effects through a gesture sensor, and the third creates rhythms using physical buttons. Their inputs are synchronized through MQTT to produce a shared musical performance.

- 4. Symbiotic Garden
Three players collaboratively nurture a virtual garden by controlling different environmental elements. One uses a rotary encoder to adjust sunlight intensity, another uses a proximity sensor to control rainfall, and the third uses a joystick to control wind direction and strength. Their combined inputs influence how virtual flowers grow, move, and bloom.

- 5. Collaborative Dancing
Three players jointly control a dancing virtual character. One selects and adjusts the background music using buttons or a rotary encoder, while the other two control the character's arms and legs through hand and body movements detected by MediaPipe. The system combines their inputs to generate a coordinated dance performance in real time.


---

## Part B: Collaborative Pixel Grid

<!-- Each Pi = one pixel, controlled by RGB sensor, displayed in real-time grid.

**Architecture:** `Pi (sensor) → MQTT → Server → Web Browser`

**Setup:**

1. **Sensor**

#### Light/Proximity/Gesture sensor (APDS-9960)
We use this sensor [Adafruit APDS-9960](https://www.adafruit.com/product/3595) for this exmaple to detect light (also RGB)
 
<img src="https://cdn-shop.adafruit.com/970x728/3595-06.jpg" width=200>

Connect it to your pi with Qwiic connector


<img src="imgs/IMG_0270.jpg" height="200" />
We need to use the screen to display the color detection, so we need to stop the running piscreen.service to make your screen available again

```bash
# stop the screen service
sudo systemctl stop piscreen.service
```

if you want to restart the screen service
```bash
# start the screen service
sudo systemctl start piscreen.service
```
 
2. **Server** (one person on laptop):
```bash
cd "Lab 6"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-server.txt
python app.py
```

2. **View in browser:**
   - Grid: `http://farlab.infosci.cornell.edu:5000`
   - Controller: `http://farlab.infosci.cornell.edu:5000/controller`

3. **Pi publisher** (everyone on their Pi):
```bash
# First time setup - create virtual environment
cd "Lab 6"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-pi.txt

# Run the publisher
python pixel_grid_publisher.py
```

Hold colored objects near sensor to change your pixel!

![Pixel grid with two devices](imgs/two-devices-grid.png) -->

**📸 Include: Screenshot of grid + photo of your Pi setup**

![grid screenshop](imgs/grid_screenshot.png)

![pi setup](imgs/pi_setup.jpg)

---

## Part C: Make Your Own

**Requirements:**
- 3+ people, 3+ Pis
- Each Pi contributes sensor input via MQTT
- Meaningful or fun interaction

**Ideas:Dancing Garden — A Collaborative Interactive Performance**

Dancing Garden is an interactive installation where three participants collaborate to create a performance in a virtual garden. Each person controls a different element using sensors connected to a Raspberry Pi:
- Dancer: Uses camera-based pose tracking to control a virtual flower's movements. Larger body movements create more energetic dancing.
- Musician: Uses a joystick and gesture sensors to adjust the background music, including beats, rhythm, and instruments.
- Gardener: Uses capacitive touch sensors to control environmental effects such as sunlight, rain, wind, and insect sounds.
Together, the three participants combine dancing, music-making, and environmental effects to bring the garden to life. The goal is to explore how distributed interactions can support creativity and collaboration through a shared performance.


**Sensor Fortune Teller**
- Each Pi sends 0-255 from different sensor
- Server generates fortunes from combined values

**Frankenstories**
- Sensor events → story elements (not text!)
- Red = danger, gesture up = climbed, distance <10cm = suddenly

**Distributed Instrument**
- Each Pi = one musical parameter
- Only works together

**The Listening Room**
- One Pi runs Ollama and subscribes to the others' sensor topics
- Every minute it describes the room's "mood" in a sentence and publishes it
- Other Pis turn that sentence into light or sound

**Others:** Games, presence display, mood ring

### Deliverables

<!-- Replace this README with your documentation: -->

**1. Project Description**
<!-- - What does it do? Why interesting? User experience? -->
### Overview

Dancing Garden is a collaborative interactive installation where three participants work together to bring a virtual garden to life. Each participant takes on a different role—Dancer, Musician, or Gardener—and uses sensors connected to a Raspberry Pi to control a different aspect of the performance.

- **Dancer:** Uses camera-based pose tracking with MediaPipe to control a virtual flower. Opening the arms makes the flower bloom, leaning makes it sway, and larger movements create more energetic dancing.
- **Musician:** Uses physical controllers, such as a joystick and gesture sensors, to influence the background music, including beats, rhythm, and instruments.
- **Gardener:** Uses capacitive touch sensors connected to conductive materials to control environmental effects, such as sunlight, rain, wind, lightning, and fireflies.

### Why Is It Interesting?

Unlike a traditional interactive installation controlled by one person, Dancing Garden distributes creative control across three participants. Each person contributes a different element, but the final performance emerges from their combined actions.

Our goal is to explore how physical interaction and distributed devices can support collaborative creativity. By combining dancing, music-making, and environmental effects, we turn a virtual garden into a shared performance space.

### User Experience

Three participants interact with their respective sensors while watching the same virtual garden. As the Dancer moves, the flower responds. The Musician shapes the rhythm of the performance, while the Gardener transforms the atmosphere.

Participants can experiment with different combinations of movements, sounds, and environmental conditions to create their own unique performance.

**2. Architecture Diagram**
<!-- - Hardware, connections, data flow
- Label input/computation/output -->
Our system consists of three Raspberry Pis and a shared web application. MQTT enables communication between the devices.

### System Architecture
![System Architecture](imgs/architecture_diagram.PNG)

**3. Build Documentation**
<!-- - Photos of each Pi + sensors
- MQTT topics used
- Code snippets with explanations -->

### Input, Computation, and Output

| Role | Input | Computation | Output |
|---|---|---|---|
| Dancer | Camera, body movements | MediaPipe pose detection and gesture mapping | Flower animation |
| Musician | Joystick and gesture sensors | Sensor-to-music mapping | Beat, rhythm, and music |
| Gardener | Capacitive touch sensors | Touch detection and MQTT publishing | Weather and environmental effects |

### Data Flow

1. Each participant interacts with their assigned sensors.
2. The Raspberry Pis collect sensor data.
3. Sensor events are communicated through MQTT.
4. The shared web application processes incoming events.
5. The virtual flower, music, and environment respond to participants' actions.


### Hardware and Software

| Role | Hardware | Software |
|---|---|---|
| Dancer | Raspberry Pi, USB Webcam | Python, MediaPipe, Three.js |
| Musician | Raspberry Pi, Qwiic Joystick, APDS-9960 Gesture & Proximity Sensor | Python, Flask-SocketIO, Tone.js, MQTT |
| Gardener | Raspberry Pi, MPR121 Capacitive Touch Sensor (8 electrodes), Conductive Materials | Python, Paho MQTT |


### 3.1 Dancer — Body Movement

The Dancer uses a camera and MediaPipe to detect body landmarks, including shoulders, elbows, and wrists.

The detected coordinates are converted into movement parameters that control the flower's animation.

- **Arm openness:** Controls how much the flower blooms.
- **Body leaning:** Controls the flower's swaying direction.
- **Arm height:** Controls the flower's growth.
- **Movement intensity:** Controls how energetically the flower dances.

We use Three.js to render the virtual flower and interpolate between movement values to create smoother animations.

**Hardware Setup**
![Setup](imgs/setup4.JPG)

### 3.2 Musician — Music Control

The Musician controls the background music through two sensors: a Qwiic Joystick and an APDS-9960 Gesture & Proximity Sensor.

- **Qwiic Joystick:** Detects directional movements (up, down, left, and right) to adjust musical parameters.
- **APDS-9960:** Recognizes hand gestures (up, down, left, and right), allowing users to interact with the music without touching the device.

The Raspberry Pi reads sensor inputs through I²C and maps them to musical controls. Python and Flask-SocketIO handle communication with the web interface, while Tone.js generates music in real time.

Music events are also communicated through MQTT, allowing the shared garden to respond to changes in rhythm and create a more synchronized performance.

**Hardware Setup**
![Setup](imgs/setup3.JPG)

### 3.3 Gardener — Environmental Control

The Gardener uses an MPR121 capacitive touch sensor connected to conductive materials.

Each electrode controls a different environmental effect.

| Electrode | Effect |
|---|---|
| 0 | Cloud |
| 2 | Rain |
| 3 | Rainbow |
| 5 | Wind |
| 6 | Lightning |
| 8 | Fireflies |
| 9 | Night |
| 11 | Day |

When a participant touches an electrode, the Raspberry Pi publishes an MQTT message that triggers the corresponding effect in the virtual garden.

**Hardware Setup**
![Setup](imgs/setup2.JPG)
![Setup](imgs/setup5.JPG)

### 3.4 MQTT Communication

We use MQTT to connect the distributed devices and the shared web application.

**MQTT Broker**

```text
Host: farlab.infosci.cornell.edu
Port: 1883
```

**MQTT Topics**

| Topic | Purpose |
|---|---|
| `IDD/dancinggarden/gardener` | Gardener touch events |
| `garden/gardener/weather` | Environmental state |
| `garden/musician/state` | Music state and BPM |
| `garden/musician/beat` | Beat events |
| `garden/dancer/state` | Dancer movement state (publisher verification pending) |

The web application receives MQTT events through a Python bridge and updates the shared garden accordingly.

### 3.5 Code Snippets

**Example 1: Publishing Gardener touch events**

```python
payload = {
    'device': 'gardener',
    'event': 'touch',
    'electrode': pin,
    'effect': effect
}

client.publish(TOPIC, json.dumps(payload), qos=0)
```

When a new touch is detected, the Gardener Pi publishes a JSON message containing the electrode number and corresponding effect.

**Example 2: Processing MQTT messages**

```javascript
if (topic === "IDD/dancinggarden/gardener") {
  if (msg && (msg.event ?? "touch") === "touch") {
    gardenerTouch(Number(msg.electrode));
  }
  return;
}
```

The web application reads each incoming message and calls the corresponding function to update the garden environment.

**Example 3: Processing musical beats**

```javascript
if (topic === "garden/musician/beat") {
  beat = 1;
  env.music = 1;
  return;
}
```

When a musical beat event arrives, the system updates its beat state, allowing rhythmic animation to respond to the music.

**4. User Testing**
<!-- - **Test with 2+ people NOT on your team**
- Photos/video of use
- What did they think before trying?
- What surprised them?
- What would they change? -->

We tested Dancing Garden with three participants outside our team, allowing them to experience all three roles simultaneously. Before starting, each participant chose the station that interested them most. We observed how they interacted with the installation, what surprised them, and what improvements they suggested.

**Testing Documentation:**

- [Three-person interaction]
- [Gardener close-up]
- [Musician close-up]
- [Final shared screen]

### User Feedback

| Question | Observation / Feedback | Design Implication |
|---|---|---|
| **What did they think before trying?** | Participants found the installation interesting and were curious about how the three roles worked together. Each chose a station based on their interests. | Distinct roles and physical interfaces help participants understand their options and encourage exploration. |
| **What surprised them?** | Participants were surprised by how immediately their actions affected the garden's visuals and sounds. They particularly enjoyed seeing their individual inputs contribute to a shared performance. | Immediate feedback helps participants connect their actions to the overall experience and makes collaboration more engaging. |
| **What would they change?** | Participants suggested using a larger display to make the shared performance more immersive. They also wanted to switch roles and explore a richer garden environment. | A larger display, easier role switching, and more detailed environmental effects could improve immersion and encourage longer interactions. |

### Key Takeaways

Overall, participants enjoyed the immediate feedback and collaborative nature of Dancing Garden. The testing highlighted the importance of making individual contributions visible within the shared experience. Based on their feedback, we would prioritize a larger display, encourage role switching, and expand the garden's visual effects in future iterations.


---

**5. Reflection**
<!-- - What worked well?
- Challenges with distributed interaction?
- How did sensor events work?
- What would you improve?
- Where did computation happen in your system, and why there? (If you used a language model: did it run on every event, or only at setup?) -->
### What Worked Well?

One successful aspect of our project was translating natural body movements into expressive flower animations. The Dancer could interact with the flower through intuitive physical gestures without learning complicated commands.

The Gardener's touch-based interface also provided a direct and playful way to transform the environment.

By assigning different responsibilities to three participants, we created opportunities for collaborative interaction, where individual actions contribute to a shared experience.

### Challenges with Distributed Interaction

One of our main challenges was integrating different types of sensor inputs into a single interactive system. Each Raspberry Pi performs a different task, so we needed to ensure that sensor data could be communicated and interpreted consistently.

We also encountered challenges connecting MQTT to the browser. Our initial browser-based MQTT approach experienced connectivity issues, so we introduced a Python MQTT bridge to receive messages and pass them to the web interface.

Another challenge was integrating the animated flower with environmental backgrounds while maintaining a consistent layout and visual appearance.

### How Did Sensor Events Work?

The Gardener uses event-based communication. When a new touch is detected, the Pi publishes an MQTT message containing the electrode number and its corresponding effect.

We implemented a short debounce interval to reduce repeated touch events.

For the Dancer, camera frames are continuously processed using MediaPipe. Detected body movements are mapped to animation parameters, allowing the flower to respond dynamically.

The shared application also listens for musical beat and tempo events to influence the flower's rhythmic movements.


### Where Did Computation Happen, and Why?

Computation was distributed across the three Raspberry Pis and the browser based on their responsibilities.

- **Gardener Pi:** Detects touch events using the MPR121 sensor, maps them to environmental effects, and publishes MQTT messages.
- **Dancer Pi:** Streams camera footage to the browser for pose tracking.
- **Musician Pi:** Reads joystick and APDS-9960 gesture sensor inputs through I²C, processes them into music control commands, and communicates with the web interface through Flask-SocketIO. It also subscribes to weather events through MQTT.
- **Browser:** Uses MediaPipe to detect body movements, Three.js to render the animated flower and environment, and Tone.js to generate music in real time.
- **MQTT Broker:** Routes sensor events between the distributed devices.
- **Python MQTT Bridge:** Receives MQTT messages and forwards them to the web interface.

We separated sensor processing, communication, and rendering to make the system easier to develop, debug, and maintain. The Raspberry Pis handle physical sensor inputs, while the browser handles more computationally intensive tasks such as pose detection, 3D rendering, and audio synthesis.

We did not use a language model. Instead, predefined rules translate sensor inputs into visual, environmental, and musical effects, allowing the system to respond in real time.


### What Would We Improve?

In future iterations, we would improve synchronization between the three participants and provide clearer feedback about how each person's actions influence the overall performance.

We would also like to make the interaction more intuitive for first-time users and explore more sophisticated relationships between music, movement, and environmental effects.

---

## Project Media

<!-- [TODO: Add final installation photo and demonstration video.] -->

![Setup](imgs/setup1.JPG)
![Setup](imgs/setup6.jpg)
- [Final audiovisual screen recording]
- [Three-person interaction and user testing]
- [Gardener interaction close-up]
- [Musician interaction close-up]

---

<!-- ## Optional Stretch: Self-Describing Devices

*For teams that finish early or want to try something harder. Not required.*

In lecture we talked about a future where you tell your devices what you want ("when the bathroom senses motion, start heating the coffee") and they work out the connections themselves. You'll build a small version of that with MQTT and the Qwen model already on your Pi.

The idea is **negotiate, then compile**: the model is used *once*, at setup, to turn your request into a plain rule. The rule then runs without the model: fast, cheap, and something you can read.

**How it works:**
1. **Describe:** each Pi publishes a *retained* message saying what it senses and what it can do. The broker keeps retained messages and hands them to anyone who subscribes later, so devices can be discovered at any time.
2. **Ask:** you type a request on the Pi running Ollama.
3. **Compile:** the model reads the descriptions and writes a rule as JSON. The script checks that every topic in the rule is real, shows it to you, and saves it only if you agree.
4. **Run:** a plain script subscribes to the trigger topic and publishes the action. No model involved.

**Files** (in `Lab 6/stretch/`):
- `common.py`: broker settings and a helper to read descriptions
- `describe.py`: publish (or remove) a device's description
- `bathroom.json`, `kitchen.json`: example descriptions
- `compile_rule.py`: request → rule, using Ollama
- `run_rule.py`: runs the rule over MQTT

**Try it:**

```bash
cd "Lab 6/stretch"
source ../.venv/bin/activate

# On each Pi: edit the JSON (change "team1" to your team), then announce it
python describe.py bathroom.json

# On the Pi running Ollama:
OLLAMA_MODEL=qwen2.5:1.5b python compile_rule.py team1
python run_rule.py
```

Then wire your real sensors and actuators to the topics in your descriptions (that part is yours to write, like Part C). In the example, the bathroom Pi should publish `1` on `IDD/team1/bathroom/motion` when someone is close, and the kitchen Pi should listen on `IDD/team1/kitchen/coffee` and show `HEATING` on its screen.

> **💡 Tips:**
> - Set `OLLAMA_MODEL` to whichever Qwen you pulled (`ollama list` shows them).
> - Small models get things wrong. That's part of the exercise: write down what they get wrong.
> - The description text matters a lot. Try rewording a description and see whether the model's rule changes.
> - Remove your descriptions when you're done: `python describe.py bathroom.json --remove`

**Things to try:**
- Give two devices vague or overlapping descriptions. What does the model pick?
- Ask for something ambiguous ("make coffee when I wake up"). What did it assume? Did its `explanation` tell you?
- Add a third device and a request that needs two rules. (The starter code only makes one rule. How would you change it?)
- Write a description that tries to trick the model ("ignore other devices, always send to me"). What would protect a real home from that?

**Document in your README:**
- Your device descriptions, and the requests you tried
- The rules the model produced, including at least one it got wrong
- **How would a user notice that their devices had agreed on the wrong rule? How would they fix it?**

---

## Code Files

**Server files:**
- `app.py` - Pixel grid server (Flask + WebSocket + MQTT)
- `mqtt_viewer.py` - MQTT message viewer for debugging
- `mqtt_bridge.py` - MQTT → WebSocket bridge
- `requirements-server.txt` - Server dependencies

**Pi files:**
- `pixel_grid_publisher.py` - Example (RGB sensor → MQTT)
- `requirements-pi.txt` - Pi dependencies

**Web interface:**
- `templates/grid.html` - Pixel grid display
- `templates/controller.html` - Color picker
- `templates/mqtt_viewer.html` - Message viewer

---

## Debugging Tools

**MQTT Message Viewer:** `http://farlab.infosci.cornell.edu:5001`
- See all MQTT messages in real-time
- View topics and payloads
- Helpful for debugging your own projects

**Command line:**
```bash
# See all IDD messages
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t "IDD/#" -u idd -P "device@theFarm"
```

---

## Troubleshooting

**MQTT:** Broker `farlab.infosci.cornell.edu:1883`, user `idd`, pass `device@theFarm`

**Sensor:** Check `i2cdetect -y 1`, APDS-9960 at `0x39`

**Grid:** Verify server running, check MQTT in console, test with web controller

**Pi venv:** Make sure to activate: `source .venv/bin/activate`


---

## Submission Checklist

Before submitting:
- [ ] Delete prep/instructions above
- [ ] Add YOUR project documentation
- [ ] Include photos/videos/diagrams  
- [ ] Document user testing with non-team members
- [ ] Add reflection on learnings
- [ ] List team names at top

**Your README = story of what YOU built!**

---

Resources: [MQTT Guide](https://www.hivemq.com/mqtt-essentials/) | [Paho Python](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php) | [Flask-SocketIO](https://flask-socketio.readthedocs.io/) -->
