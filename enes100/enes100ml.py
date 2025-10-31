import network
import time
from machine import Pin, UART
import _thread
import uasyncio as asyncio
import sys
sys.path.append('/lib/enes100')

mission_stuff = {
    # Mission Types
    'CRASH_SITE' : 0,
    'DATA' : 1,
    'MATERIAL' : 2,
    'FIRE' : 3,
    'WATER' : 4,
    'SEED' : 5,
    'HYDROGEN' : 6,

    # Crash Mission
    'DIRECTION' : 0,
    'LENGTH' : 1,
    'HEIGHT' : 2,
    'NORMAL_X' : 0,
    'NORMAL_Y' : 1,

    # Data
    'CYCLE' : 0,
    'MAGNETISM' : 1,
    'MAGNETIC' : 0,
    'NOT_MAGNETIC' : 1,

    # Materials
    'WEIGHT' : 0,
    'MATERIAL_TYPE' : 1,
    'FOAM' : 0,
    'PLASTIC' : 1,
    'HEAVY' : 0,
    'MEDIUM' : 1,
    'LIGHT' : 2,

    # Fire
    'NUM_CANDLES' : 0,
    'TOPOGRAPHY' : 1,
    'TOP_A' : 0,
    'TOP_B' : 1,
    'TOP_C' : 2,

    # Water
    'DEPTH' : 0,
    'WATER_TYPE' : 1,
    'FRESH_UNPOLLUTED' : 0,
    'FRESH_POLLUTED' : 1,
    'SALT_UNPOLLUTED' : 2,
    'SALT_POLLUTED' : 3,

    # Seed
    'LOCATION' : 0,
    'PERCENTAGE' : 1,

    # Hydrogen
    'VOLTAGE_OUTPUT' : 0,
    'LED_COLOR' : 1,
    'VOLTAGE_1' : 0,
    'VOLTAGE_2' : 1,
    'VOLTAGE_3' : 2,
    'VOLTAGE_4' : 3,
    'VOLTAGE_5' : 4,
    'WHITE' : 0,
    'RED' : 1,
    'YELLOW' : 2,
    'GREEN' : 3,
    'BLUE' : 4,
}

# Transmission opcodes
OP_BEGIN = 0x01
OP_PRINT = 0x02
OP_CHECK = 0x03
OP_MISSION = 0x04
OP_ML_PREDICTION = 0x05
OP_ML_CAPTURE = 0x06
OP_IS_CONNECTED = 0x07

FLUSH_SEQUENCE = b'\xFF\xFE\xFD\xFC'

def current_milli_time():
    return round(time.time()*1000)


class Enes100:
    def __init__(self):
        self.uart = None
        
        self.team_name = ''
        self.mission_type = 0
        self.marker_id = 0
        self.room_number = 0
        
        self.x = -1.0
        self.y = -1.0
        self.theta = -1.0
        self.is_visible = False

    def begin(self, team_name, mission_type, marker_id, room_number, tx_pin, rx_pin):
        self.marker_id = marker_id
        self.uart = UART(1, baudrate=57600, tx=tx_pin, rx=rx_pin)
        

        while self.state() not in [0x00, 0x01]:
            time.sleep_ms(50)
            print(self.state())

        self.uart.write(bytes([OP_BEGIN]))
        self.uart.write(bytes([mission_stuff[mission_type.upper()]]))
        self.uart.write(marker_id.to_bytes(2, 'big'))
        self.uart.write(room_number.to_bytes(2, 'big'))
        self.uart.write(team_name.encode('utf-8'))
        self.uart.write(b'\x00')
        self.uart.write(FLUSH_SEQUENCE)

        while self.state() != 0x01:
            time.sleep_ms(50)
        
        _thread.start_new_thread(self._background_update, ())

    def _read_bytes(self, num_bytes, timeout_ms=100):
        data = b''
        start = time.ticks_ms()
        while len(data) < num_bytes:
            if self.uart.any():
                data += self.uart.read(1)
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                return None  # timed out
        return data

    def _background_update(self):
        while True:
            self._update_if_needed()
            time.sleep_ms(50)
    
    def state(self):
        if self.uart is None:
            return 0xFF
        while self.uart.any():
            self.uart.read(1)
        self.uart.write(bytes([OP_IS_CONNECTED]))
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 10 and self.uart.any() == 0:
            pass
        result = self.uart.read(1)
        if result is None or len(result) == 0:
            return 0xFF
        return result[0]
    
    def mission(self, mission_call, message_var):
        if self.uart is None:
            return -1;
        
        self.uart.write(bytes([OP_MISSION]))
        self.uart.write(bytes([mission_stuff[mission_call.upper()]]))
        
        if isinstance(message_var, str) and message_var.upper() in mission_stuff:
            message_var = mission_stuff[message_var.upper()]

            
        self.uart.write(str(message_var).encode('utf-8'))
        self.uart.write(b'\x00')
        self.uart.write(FLUSH_SEQUENCE)
        
    def ml_get_prediction(self, model_index):
        if self.uart is None:
            return -1

        # Send request
        self.uart.write(bytes([OP_ML_PREDICTION]))
        self.uart.write(bytes([model_index]))
        self.uart.write(FLUSH_SEQUENCE)

        # Give the ESP a moment to respond
        time.sleep_ms(1)

        # Flush incoming buffer (clear noise)
        while self.uart.any():
            self.uart.read(1)

        # Wait for first byte
        start = time.ticks_ms()
        while not self.uart.any():
            if time.ticks_diff(time.ticks_ms(), start) > 50:
                return -1  # timeout

        b0 = self.uart.read(1)
        if not b0:
            return -1

        # Wait for second byte
        start = time.ticks_ms()
        while not self.uart.any():
            if time.ticks_diff(time.ticks_ms(), start) > 100:
                return -1

        b1 = self.uart.read(1)
        if not b1:
            return -1

        # Combine bytes (little-endian)
        result = (b1[0] << 8) | b0[0]
        return result


    def _update_if_needed(self):
        if self.uart is None:
            return

        now = time.ticks_ms()
        if hasattr(self, 'last_update') and time.ticks_diff(now, self.last_update) < 50:
            return
        self.last_update = now

        # Flush old data
        while self.uart.any():
            self.uart.read(1)

        self.uart.write(bytes([OP_CHECK]))

        # Wait up to 100 ms for a response byte
        start = time.ticks_ms()
        while not self.uart.any():
            if time.ticks_diff(time.ticks_ms(), start) > 10:
                return

        b = self.uart.read(1)
        if not b:
            return
        b = b[0]

        # Interpret response byte
        if b == 0x00:
            return  # no update
        if b == 0x01:
            # marker not visible
            self.x = -1
            self.y = -1
            self.theta = -1
            self.is_visible = False
            return
        if b != 0x02:
            return  # invalid value

        # marker visible
        self.is_visible = True

        data = self._read_bytes(1)
        if data is None:
            return
        y_raw = data[0]
        self.y = y_raw / 100.0

        # X (2 bytes, unsigned)
        data = self._read_bytes(2)
        if data is None:
            return
        x_raw = (data[1] << 8) | data[0]
        self.x = x_raw / 100.0

        # Theta (2 bytes, signed)
        data = self._read_bytes(2)
        if data is None:
            return
        theta_raw = int.from_bytes(data, 'little', True)
        self.theta = theta_raw / 100.0
    
    def is_connected(self):
        return self.state() == 0x01

    def print(self, message):
        if self.uart is None:
            return -1;
        
        str_message = str(message)
        str_message.join('\n')
        
        self.uart.write(bytes([OP_PRINT]))          
        self.uart.write(str_message.encode('utf-8'))
        self.uart.write(b'\x00')
        self.uart.write(FLUSH_SEQUENCE)
        self.uart.flush()
        
          
enes100 = Enes100()


