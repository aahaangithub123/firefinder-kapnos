# firefinder-kapnos
Python based program to visualize origin of fires. Uses thermal falloff, virtual temperature and GPS sensors in a sandbox environment.

This README provides a comprehensive overview of the **IoT Fire Monitoring & Heatmap System**. This project simulates a network of temperature sensors that detect a heat source (fire), communicate data through a central server, and visualize the threat in real-time using a heatmap.

---

# Fire Predicting System

This system is a distributed application consisting of a **Thermal Falloff Simulator**, a **Server**, and a **Visualization Dashboard**. It demonstrates how IoT sensor data can be aggregated to predict the location of an emergency.

## 📂 System Components

| File | Role | Description |
| --- | --- | --- |
| **`server.py`** | **The Hub** | A multi-threaded TCP server that receives data from sensors and broadcasts it to all connected dashboards. |
| **`virtual_sensor.py`** | **The Producer** | A GUI tool to place virtual sensors and a "fire" source. It calculates temperatures based on proximity. |
| **`heatmap_demo.py`** | **The Consumer** | A real-time dashboard that renders a heatmap, predicts the fire's center, and sounds an alarm. |
| **`image.jpg`** | **Asset** | Used as the floor plan background for the Virtual Sensor tool. |

---

##  System Architecture

The project follows a **Client-Server** architecture using Python Sockets.

1. **Data Generation:** `virtual_sensor.py` calculates heat values.
2. **Transmission:** Data is sent via TCP sockets as a CSV string: `ID, X, Y, Temperature\n`.
3. **Relay:** `server.py` receives the string and immediately sends it to any connected `heatmap_demo.py` instances.
4. **Visualization:** The heatmap interpolates these points to create a smooth gradient.

---

##  Installation & Setup

### 1. Prerequisites

Ensure you have Python 3.x installed along with the following libraries:

```bash
pip install numpy matplotlib pillow

```

### 2. Execution Order

To ensure the sockets connect correctly, launch the files in this specific order, or run start.bat:

1. **`python server.py`** (Must be running first to accept connections).
2. **`python heatmap_demo.py`** (Connects to the server to wait for data).
3. **`python virtual_sensor.py`** (Starts sending simulated data).

---

##  User Guide

### Virtual Sensor Controller

* **Add Sensor:** Click the button to spawn a sensor in the center.
* **Move Sensor:** Left-click and drag the blue dots to position them around your "building."
* **Place Fire:** **Right-click** anywhere on the canvas to move the fire source.
* **Adjust Physics:** Use the sliders to change the fire's temperature or the **Sigma (Falloff)**, which controls how far the heat spreads.

### Heatmap Dashboard

* **Heatmap:** High temperatures appear white/yellow, while ambient temperatures appear red/black.
* **Fire Prediction:** The **Red "X"** is the system's best guess of where the fire is based on sensor weighting.
* **Alarm:** If any sensor exceeds **100°C**, the screen will flash "Fire Alarm!" and a beep will sound (Windows only).

---

##  Technical Logic

### 1. Heat Falloff (Virtual Sensor)

The temperature  at any sensor is calculated using a Gaussian falloff formula based on the distance from the fire:

$$T_{sensor} = T_{ambient} + (T_{fire} - T_{ambient}) \cdot e^{-\frac{d^2}{2\sigma^2}}$$

### 2. Fire Localization (Heatmap)

The dashboard predicts the fire location using a **Weighted Centroid**. Sensors with higher temperatures pull the predicted coordinates closer to them:

$$\bar{x} = \frac{\sum (x_i \cdot T_i)}{\sum T_i}, \quad \bar{y} = \frac{\sum (y_i \cdot T_i)}{\sum T_i}$$

---

## ⚠️ Common Troubleshooting

* **Instant Crash:** Ensure the `image.jpg` is in the same folder and you have used `from_` (with an underscore) for Tkinter sliders.
* **No Data on Heatmap:** Check the server console to ensure both the sensor and the heatmap are listed as "Connected."
* **Sound Issues:** The `winsound` library is Windows-specific. On Mac or Linux, the alarm text will show, but the beep will be skipped.

**Would you like me to help you extend this code to log the temperature data into a CSV file for later analysis?**
