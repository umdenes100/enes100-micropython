# **ENES100 Micropython Library**
An PyPl library for use in the ENES100 course to allow ESP32 microcontrollers to communicate with the ENES100 Vision System via on-board WiFi.

## Download and Installation 
You must download Thonny IDE to your computer. The latest version can be downloaded from the Thonny website.
Flashing MicroPython Firmware using Thonny IDE
In this section, you’ll learn how to flash MicroPython firmware on your boards using Thonny IDE. Follow the next steps:
1) Connect your ESP32 board to your computer.
2) Open Thonny IDE. Go to Tools > Options > Interpreter.
3) Select the interpreter you want to use accordingly to the board you’re using and select the COM port your board is connected to. Finally, click on the link Install or update firmware(esptool).
	
4) Next, select ESP32 as the Micropython family, Espressif - ESP32 / WROOM as the variant, and 1.24.1 as the version. Then, click install.

5) To make sure that the installation was successful, type help() into the shell. You should receive a message like this.


## Usage
To use the library, you have to direct the compiler to include it in your code. Add it manually by typing **from enes100 import \*** at the very top of your file.
### enes100.begin
`enes100.begin(team_name: str, team_type: str, aruco_id: int, room_num: int)`

Initializes the ENES100 library and establishes communication with the Vision System.
- team_name: Name of the team that will show up in the Vision System
- team_type: Type of mission your team is running.
	- Valid Mission Types: `CRASH_SITE`, `DATA`, `MATERIAL`, `FIRE`, `WATER`, `SEED`
- aruco_id: ID of your Aruco Marker
- room_num: The number of the classroom in which you are located (1116 or 1120)

### enes100.x and similar
The Aruco Marker has 4 values
- x: x-coordinate of the Aruco Marker (from 0.0 to 4.0), -1 if aruco is not visible
- y: y-coordinate of the Aruco Marker (From 0.0 to 2.0), -1 if aruco is not visible
- theta: angle of the Aruco Marker (from -pi radians to pi radians), -1 if aruco is not visible
- visibility: whether the ArUco marker is visible (true or false)

These values can be queried by using the following commands:
- `enes100.x`
- `enes100.y`
- `enes100.theta`
- `enes100.isVisible()`
enes100.get variants will make sure you get the latest data available to you about your OTV's location. There is no need to save these as a separate variable.

### enes100.is_connected()
`enes100.is_connected()`
Returns true if the ESP8266 is connected to the Vision System, false otherwise. Note: enes100.begin will not return until this function is true.

### enes100.print()
`enes100.print(message: str)`
Sends a message to the vision system with a new line. Any messages sent after will be printed in a new line below the ' println'

### enes100.mission()
`enes100.mission(type: str, message: str)
Sends value for a mission objective.
- type: what type of mission call you are sending
- message: mission value associated with the mission type.

All the definitions defined in the Enes100 library correlate to an integer. To save you the trouble, you can call the uppercase definition like LENGTH for Crash Site teams or MATERIAL_TYPE for Material Identification teams.

For the valid mission calls below, the value i will denote an integer value.

Valid calls for **CRASH_SITE**:
- `enes100.mission(LENGTH, i)` i is in millimeters
- `enes100.mission(HEIGHT, i)` i is in millimeters
- `enes100.mission(DIRECTION, NORMAL_X)` the normal of the exposed panels points in the positive and negative x direction
- `enes100.mission(DIRECTION, NORMAL_Y)` the normal of the exposed panels points in the positive and negative y direction

Valid calls for **DATA**:
- `enes100.mission(CYCLE, i)` i is the duty cycle percent (ex. 10, 30, 50, 70, 90)
- `enes100.mission(MAGNETISM, MAGNETIC)`
- `enes100.mission(MAGNETISM, NOT_MAGNETIC)`

Valid calls for **MATERIAL**:
- `enes100.mission(WEIGHT, HEAVY)`
- `enes100.mission(WEIGHT, MEDIUM)`
- `enes100.mission(WEIGHT, LIGHT)`
- `enes100.mission(MATERIAL_TYPE, FOAM)`
- `enes100.mission(MATERIAL_TYPE, PLASTIC)`

Valid calls for **FIRE**:
- `enes100.mission(NUM_CANDLES, i)` i is an integer (0, 1, 2, 3, 4, 5)
- `enes100.mission(TOPOGRAPHY, TOP_A)`
- `enes100.mission(TOPOGRAPHY, TOP_B)`
- `enes100.mission(TOPOGRAPHY, TOP_C)`

Valid calls for **WATER**:
- `enes100.mission(DEPTH, i)` i is in mm
- `enes100.mission(WATER_TYPE, FRESH_UNPOLLUTED)`
- `enes100.mission(WATER_TYPE, FRESH_POLLUTED)`

#### Valid calls for SEED:
- `enes100.mission(PERCENTAGE, i)` i is a percentage
- `enes100.mission(LOCATION, cord)` where cord is a Coordinate object

## Product Demonstration Procedures
During the product demonstration, messages sent using print() will not be shown on the Vision System console. You should use the mission calls to send results.
