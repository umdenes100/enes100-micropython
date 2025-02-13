# **ENES100 Micropython Library**
An PyPl library for use in the ENES100 course to allow ESP32 microcontrollers to communicate with the ENES100 Vision System via on-board WiFi.

## Download and Installation 
You must download Thonny IDE to your computer. The latest version can be downloaded from the Thonny website.
Flashing MicroPython Firmware using Thonny IDE
In this section, you’ll learn how to flash MicroPython firmware on your boards using Thonny IDE. Follow the next steps:
1) Connect your ESP32 or ESP8266 board to your computer.
2) Open Thonny IDE. Go to Tools > Options > Interpreter.
3) Select the interpreter you want to use accordingly to the board you’re using and select the COM port your board is connected to. Finally, click on the link Install or update firmware(esptool).
	
4) Next, select ESP32 as the Micropython family, Espressif - ESP32 / WROOM as the variant, and 1.24.1 as the version. Then, click install.

5) To make sure that the installation was successful, type help() into the shell. You should receive a message like this.


## Usage
To use the library, you have to direct the compiler to include it in your code. Add it manually by typing **from enes100 import \*** at the very top of your file.
### Enes100.begin
`Enes100.begin(team_name, team_type, aruco_id, room_num)`

Initializes the ENES100 library and establishes communication with the Vision System.
- team_name: Name of the team that will show up in the Vision System
- team_type: Type of mission your team is running.
	- Valid Mission Types: `CRASH_SITE`, `DATA`, `MATERIAL`, `FIRE`, `WATER`, `SEED`
- aruco_id: ID of your Aruco Marker
- room_num: The number of the classroom in which you are located (1116 or 1120)

### Enes100.x and similar
The Aruco Marker has 4 values
- x: x-coordinate of the Aruco Marker (from 0.0 to 4.0)
- y: y-coordinate of the Aruco Marker (From 0.0 to 2.0)
- theta: angle of the Aruco Marker (from -pi radians to pi radians)
- visibility: whether the ArUco marker is visible (true or false)

These values can be queried by using the following commands:
- `Enes100.x`
- `Enes100.y`
- `Enes100.theta`
- `Enes100.isVisible()`
Enes100.get variants will make sure you get the latest data available to you about your OTV's location. There is no need to save these as a separate variable.

### Enes100.is_connected()
`Enes100.is_connected()`
Returns true if the ESP8266 is connected to the Vision System, false otherwise. Note: Enes100.begin will not return until this function is true.

### Enes100.print(str message)
`Enes100.print(message)`
Sends a message to the vision system with a new line. Any messages sent after will be printed in a new line below the ' println'

### Enes100.mission(int type, int message)
Sends value for a mission objective.
- type: what type of mission call you are sending
- message: mission value associated with the mission type.

All the definitions defined in the Enes100 library correlate to an integer. To save you the trouble, you can call the uppercase definition like LENGTH for Crash Site teams or MATERIAL_TYPE for Material Identification teams.

For the valid mission calls below, the value i will denote an integer value.

#### Valid calls for CRASH_SITE:
- `Enes100.mission(LENGTH, i)` i is in millimeters
- `Enes100.mission(HEIGHT, i)` i is in millimeters
- `Enes100.mission(DIRECTION, NORMAL_X)` the normal of the exposed panels points in the positive and negative x direction
- `Enes100.mission(DIRECTION, NORMAL_Y)` the normal of the exposed panels points in the positive and negative y direction

#### Valid calls for DATA:
- `Enes100.mission(CYCLE, i)` i is the duty cycle percent (ex. 10, 30, 50, 70, 90)
- `Enes100.mission(MAGNETISM, MAGNETIC)`
- `Enes100.mission(MAGNETISM, NOT_MAGNETIC)`

#### Valid calls for MATERIAL:
- `Enes100.mission(WEIGHT, HEAVY)`
- `Enes100.mission(WEIGHT, MEDIUM)`
- `Enes100.mission(WEIGHT, LIGHT)`
- `Enes100.mission(MATERIAL_TYPE, FOAM)`
- `Enes100.mission(MATERIAL_TYPE, PLASTIC)`

#### Valid calls for FIRE:
- `Enes100.mission(NUM_CANDLES, i)` i is an integer (0, 1, 2, 3, 4, 5)
- `Enes100.mission(TOPOGRAPHY, TOP_A)`
- `Enes100.mission(TOPOGRAPHY, TOP_B)`
- `Enes100.mission(TOPOGRAPHY, TOP_C)`

#### Valid calls for WATER:
- `Enes100.mission(DEPTH, i)` i is in mm
- `Enes100.mission(WATER_TYPE, FRESH_UNPOLLUTED)`
- `Enes100.mission(WATER_TYPE, FRESH_POLLUTED)`

#### Valid calls for SEED:
- `Enes100.mission(PERCENTAGE, i)` i is a percentage
- `Enes100.mission(LOCATION, cord)` where cord is a Coordinate object

## Product Demonstration Procedures
During the product demonstration, messages sent using print() will not be shown on the Vision System console. You should use the mission calls to send results.
