# Embedded Thermostat Controller (Python, GPIO, LCD)

An embedded thermostat-style controller written in Python for a Raspberry Pi that monitors temperature, manages off/heat/cool operating states, and provides real-time feedback via an LCD display, LED indicators, and button input.

## Features
- Reads temperature data from an I2C-connected sensor.
- Implements off, heat, and cool operating states using a state machine.
- Displays real-time system information on a 16x2 LCD screen.
- Uses physical buttons to cycle states and adjust temperature setpoints.
- Provides visual feedback using PWM-controlled LED indicators.
- Periodically outputs system status via serial communication.

## Technologies Used
- **Python**
- **Raspberry Pi OS (Linux)**
- **GPIO / I2C**
- **LCD display**
- **PWM LEDs**
- **State machine–based control logic**

## Hardware Platform
- Raspberry Pi 4 (Ultimate)
- I2C temperature sensor
- 16x2 character LCD
- GPIO push buttons
- PWM-controlled LEDs

## Setup & Installation

### Prerequisites
- Raspberry Pi running Raspberry Pi OS (Linux)
- Python 3
- GPIO, I2C, and LCD wiring completed correctly

### Clone the Repository
git clone https://github.com/bscamp63/Embedded-Thermostat-Controller
cd Embedded-Thermostat-Controller

### Install Dependencies
pip3 install adafruit-circuitpython-ahtx0 gpiozero pyserial statemachine

### Run the Program
python3 thermostat.py
