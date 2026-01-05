@echo off
:: This batch script will run all Python scripts and minimize the console windows
pip install numpy matplotlib pillow
:: Run the server.py script
start /min py server.py

:: Run the virtual_sensor.py script (Client)
start /min py virtual_sensor.py

:: Run the heatmap_demo.py script (Heatmap)
start /min py heatmap_demo.py
