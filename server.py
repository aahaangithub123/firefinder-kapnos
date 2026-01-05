import socket
import threading
import tkinter as tk
from tkinter import messagebox

# Constants
HOST = '127.0.0.1'
PORT = 65432
clients = []  # Store connected clients
sensors = {}  # {sensor_id: {"location": (x, y), "temperature": temp}}

# Functions to handle server logic
def handle_client(conn, addr):
    """Receive sensor data and broadcast to all connected clients."""
    global sensors
    print(f"Client connected: {addr}")
    clients.append(conn)
    buffer = ""

    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
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

            # Send updated sensor data to all clients
            broadcast_data()
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        conn.close()
        clients.remove(conn)

def broadcast_data():
    """Send sensor data to all connected clients."""
    if not sensors:
        return
    data = "\n".join(f"{sid},{s['location'][0]},{s['location'][1]},{s['temperature']:.2f}"
                     for sid, s in sensors.items()) + "\n"
    for client in clients:
        try:
            client.sendall(data.encode('utf-8'))
        except:
            clients.remove(client)

def start_server():
    """Start the server and listen for connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Server listening on {HOST}:{PORT}...")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# GUI setup
def start_gui():
    """Start the server GUI."""
    root = tk.Tk()
    root.title("Server")

    # Display sensor data
    sensor_data_frame = tk.Frame(root)
    sensor_data_frame.pack()

    sensor_listbox = tk.Listbox(sensor_data_frame, width=40, height=10)
    sensor_listbox.pack()

    def update_sensor_list():
        """Update the listbox with current sensor data."""
        sensor_listbox.delete(0, tk.END)
        for sid, s in sensors.items():
            sensor_listbox.insert(tk.END, f"ID: {sid}, Location: {s['location']}, Temp: {s['temperature']:.2f}°C")
        root.after(1000, update_sensor_list)  # Update every second

    # Start the server in a separate thread
    threading.Thread(target=start_server, daemon=True).start()

    update_sensor_list()  # Start updating sensor data in the listbox
    root.mainloop()

if __name__ == "__main__":
    start_gui()
