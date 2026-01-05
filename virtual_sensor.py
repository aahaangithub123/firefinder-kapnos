import tkinter as tk
from PIL import Image, ImageTk  # Importing Pillow for image handling
import numpy as np
import socket
import threading
import time

# Constants
WIDTH, HEIGHT = 800, 600
FIRE_TEMP = 404           # Default fire temperature
SENSOR_TEMP = 25          # Default sensor temperature
FALLOFF_SIGMA = 215       # Default sigma for falloff
UPDATE_INTERVAL = 1000    # Interval for updating sensor data
HOST = '127.0.0.1'
PORT = 65432
sensors = {}              # Dictionary to store sensor data
next_sensor_id = 1        # ID for next sensor
fire_location = None      # Current fire location
selected_sensor = None    # Currently selected sensor for moving
drag_offset = (0, 0)      # Offset for dragging sensors

sock = None               # Socket connection to server

# Background image path
BACKGROUND_IMAGE_PATH = r"image.jpg"  # Modify path as needed

# Load background image
background_image = None
background_photo = None

def load_background_image():
    """Load the image file to be used as background."""
    global background_image, background_photo
    try:
        background_image = Image.open(BACKGROUND_IMAGE_PATH)
        background_image = background_image.resize((WIDTH, HEIGHT))
        background_photo = ImageTk.PhotoImage(background_image)
    except Exception as e:
        print(f"Error loading image: {e}")
    

def connect_socket():
    """Attempt to establish socket connection."""
    global sock
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            print("Connected to server")
            return
        except ConnectionRefusedError:
            print("Server not available. Retrying...")
            time.sleep(2)

def send_sensor_data():
    """Send sensor data to the server."""
    if sock is None:
        return
    try:
        data = []
        for sensor_id, s in sensors.items():
            flipped_y = HEIGHT - s["location"][1]
            data.append(f"{sensor_id},{s['location'][0]},{flipped_y},{s['temperature']:.2f}")
        sock.sendall(("\n".join(data) + "\n").encode('utf-8'))
    except Exception as e:
        print(f"Error sending data: {e}")

def update_temperatures():
    """Update sensor temperatures based on proximity to fire."""
    if fire_location:
        fx, fy = fire_location
        for sensor_id, data in sensors.items():
            sx, sy = data["location"]
            distance = np.hypot(sx - fx, sy - fy)
            falloff = np.exp(-(distance**2) / (2 * FALLOFF_SIGMA**2))  # Use updated sigma
            data["temperature"] = SENSOR_TEMP + (FIRE_TEMP - SENSOR_TEMP) * falloff
    else:
        for data in sensors.values():
            data["temperature"] = SENSOR_TEMP

def add_sensor():
    """Add a new sensor."""
    global next_sensor_id
    x, y = WIDTH // 2, HEIGHT // 2
    sensors[next_sensor_id] = {"location": (x, y), "temperature": SENSOR_TEMP}
    next_sensor_id += 1
    update_temperatures()
    draw_sensors()

def place_fire(event):
    """Place fire with right-click."""
    global fire_location
    fire_location = (event.x, event.y)
    update_temperatures()
    draw_sensors()

def on_press(event):
    """Select sensor to move."""
    global selected_sensor, drag_offset
    min_dist = float('inf')
    selected_sensor = None
    for sensor_id, data in sensors.items():
        sx, sy = data["location"]
        dx = event.x - sx
        dy = event.y - sy
        dist = np.hypot(dx, dy)
        if dist < 10 and dist < min_dist:
            min_dist = dist
            selected_sensor = sensor_id
            drag_offset = (dx, dy)

def on_motion(event):
    """Move selected sensor."""
    if selected_sensor is not None:
        sensors[selected_sensor]["location"] = (event.x - drag_offset[0], event.y - drag_offset[1])
        update_temperatures()
        draw_sensors()

def on_release(event):
    """Release selected sensor."""
    global selected_sensor
    selected_sensor = None

def update_fire_temp(val):
    """Update fire temperature based on slider value."""
    global FIRE_TEMP
    FIRE_TEMP = int(val)
    update_temperatures()
    draw_sensors()

def update_sigma(val):
    """Update sigma value for fire temperature falloff based on slider value."""
    global FALLOFF_SIGMA
    FALLOFF_SIGMA = int(val)
    update_temperatures()
    draw_sensors()

def draw_sensors():
    """Update sensor display."""
    canvas.delete("all")

    # Draw background image
    if background_photo:
        canvas.create_image(0, 0, image=background_photo, anchor=tk.NW)
    else:
        # Fallback: Draw a gray rectangle so you can still see the sensors
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#f0f0f0")

    if fire_location:
        fx, fy = fire_location
        canvas.create_oval(fx-10, fy-10, fx+10, fy+10, fill="red", tags="fire")
        canvas.create_text(fx, fy-20, text="Fire", fill="black")
    
    for s in sensors.values():
        x, y = s["location"]
        canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue")
        canvas.create_text(x, y-15, text=f"{s['temperature']:.1f}°C", fill="black")

def update_loop():
    """Loop to send sensor data."""
    send_sensor_data()
    root.after(UPDATE_INTERVAL, update_loop)

# GUI setup
root = tk.Tk()
root.title("Virtual Sensor Controller")

# Load the background image
load_background_image()

# Canvas for drawing the sensors and fire
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="white")
canvas.pack()

# Add sensor button
btn_frame = tk.Frame(root)
btn_frame.pack()
add_btn = tk.Button(btn_frame, text="Add Sensor", command=add_sensor)
add_btn.pack(side=tk.LEFT)

# Fire temperature slider
temp_slider = tk.Scale(root, from_=100, to=1000, orient="horizontal", label="Fire Temperature (°C)", command=update_fire_temp)
temp_slider.set(FIRE_TEMP)  # Default fire temperature
temp_slider.pack()

# Sigma slider for fire falloff
sigma_slider = tk.Scale(root, from_=100, to=1000, orient="horizontal", label="Falloff Sigma", command=update_sigma)
sigma_slider.set(FALLOFF_SIGMA)  # Default sigma
sigma_slider.pack()

# Canvas event bindings
canvas.bind("<Button-3>", place_fire)
canvas.bind("<Button-1>", on_press)
canvas.bind("<B1-Motion>", on_motion)
canvas.bind("<ButtonRelease-1>", on_release)

# Connect to server in a separate thread
threading.Thread(target=connect_socket, daemon=True).start()

# Start updating the sensor data
root.after(UPDATE_INTERVAL, update_loop)

root.mainloop()
