import tkinter as tk
import numpy as np
import socket
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import winsound  # For fire alarm sound on Windows

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 100
HOST = '127.0.0.1'
PORT = 65432
sensors = {}
FIRE_TEMP_THRESHOLD = 100  # Fire temperature threshold
ALARM_INTERVAL = 500  # milliseconds between alarm blinks
BLINK_INTERVAL = 500  # milliseconds between blink of fire location

# Variables for alarm state and blinking
alarm_state = False
fire_location = None
last_fire_time = 0

def connect_to_server():
    """Continuously receive data from the server."""
    global sensors
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print("Connected to server...")

        buffer = ""
        while True:
            data = sock.recv(1024).decode('utf-8')
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                try:
                    sensor_id, x, y, temp = map(float, line.split(','))
                    sensors[int(sensor_id)] = {"location": (x, y), "temperature": temp}
                except ValueError:
                    print(f"Invalid data received: {line}")
    except ConnectionRefusedError:
        print("Failed to connect to server. Is `server.py` running?")
    finally:
        sock.close()

def generate_heatmap():
    """Generate heatmap based on sensor data."""
    if not sensors:
        return np.zeros((GRID_SIZE, GRID_SIZE))

    heatmap = np.zeros((GRID_SIZE, GRID_SIZE))
    sensor_positions = [(s["location"][0], s["location"][1]) for s in sensors.values()]
    sensor_temps = [s["temperature"] for s in sensors.values()]

    x_vals = np.linspace(0, WIDTH, GRID_SIZE)
    y_vals = np.linspace(0, HEIGHT, GRID_SIZE)
    X, Y = np.meshgrid(x_vals, y_vals)

    for (sx, sy), temp in zip(sensor_positions, sensor_temps):
        distances = np.sqrt((X - sx) ** 2 + (Y - sy) ** 2)
        falloff = np.exp(-distances / 100)
        heatmap += temp * falloff

    return heatmap

def locate_fire():
    """Estimate the fire's location using the weighted centroid method."""
    global fire_location, sensors

    if not sensors:
        return

    total_weight = sum(s["temperature"] for s in sensors.values())
    if total_weight == 0:
        return None  # Avoid division by zero

    weighted_x = sum(s["location"][0] * s["temperature"] for s in sensors.values()) / total_weight
    weighted_y = sum(s["location"][1] * s["temperature"] for s in sensors.values()) / total_weight

    fire_location = (weighted_x, weighted_y)
    return fire_location

def trigger_alarm():
    """Trigger the fire alarm with flashing text and sound."""
    global alarm_state, last_fire_time
    current_time = time.time()

    if fire_location and any(s["temperature"] >= FIRE_TEMP_THRESHOLD for s in sensors.values()):
        # Flash alarm every half second
        if current_time - last_fire_time > 1:
            alarm_state = not alarm_state
            last_fire_time = current_time

            # Sound alarm if temperature is above threshold
            winsound.Beep(1000, 500)  # Frequency: 1000 Hz, Duration: 500 ms

def update_heatmap():
    """Update the heatmap visualization."""
    global alarm_state

    heatmap = generate_heatmap()

    ax.clear()
    ax.imshow(heatmap, cmap="hot", origin="lower", extent=[0, WIDTH, 0, HEIGHT])
    
    # Draw sensors
    for sensor in sensors.values():
        x, y = sensor["location"]
        ax.scatter(x, y, c="blue", edgecolors="white", s=50)  # Sensor positions
    
    # Locate the fire using centroid approximation
    fire_pos = locate_fire()

    if fire_pos:
        fx, fy = fire_pos
        if alarm_state:
            ax.scatter(fx, fy, c="red", edgecolors="black", s=100, alpha=0.6)  # Blinking fire location
        ax.scatter(fx, fy, c="red", marker="X", s=100, label="Predicted Fire")  # Red cross for fire

    # Display fire alarm if necessary
    if any(s["temperature"] >= FIRE_TEMP_THRESHOLD for s in sensors.values()):
        if alarm_state:
            ax.text(WIDTH//2, HEIGHT-40, "Fire Alarm!", color="red", fontsize=20, ha="center", fontweight="bold")

    ax.set_title("Temperature Heatmap")
    canvas.draw()

    # Update the heatmap and fire alarm every 100ms
    root.after(100, update_heatmap)  # Faster updates every 100ms

# GUI setup
root = tk.Tk()
root.title("Heatmap")

fig, ax = plt.subplots(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Start server connection in background
threading.Thread(target=connect_to_server, daemon=True).start()

# Start heatmap updates and fire detection
update_heatmap()  # Start heatmap updates
root.mainloop()
