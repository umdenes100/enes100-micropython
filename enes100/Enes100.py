import network
import time
import json
import _thread

from . import uwebsockets
from .wifi_db import WIFI_MAP

# Mission formatting + constants
from .mission import MissionFormatter
from . import mission as _m


class Enes100:

    # ----------------------------
    # Re-export mission constants (so callers can do Enes100.DEPTH, Enes100.RED, etc.)
    # ----------------------------

    # Mission "type" constants (first argument to Enes100.mission)
    DIRECTION = _m.DIRECTION
    LENGTH = _m.LENGTH
    HEIGHT = _m.HEIGHT

    CYCLE = _m.CYCLE
    MAGNETISM = _m.MAGNETISM

    WEIGHT = _m.WEIGHT
    MATERIAL_TYPE = _m.MATERIAL_TYPE

    NUM_CANDLES = _m.NUM_CANDLES
    TOPOGRAPHY = _m.TOPOGRAPHY

    DEPTH = _m.DEPTH
    WATER_TYPE = _m.WATER_TYPE

    LOCATION = _m.LOCATION

    LED_COLOR = _m.LED_COLOR
    VOLTAGE_OUTPUT = _m.VOLTAGE_OUTPUT

    # Option constants (second argument to Enes100.mission for categorical calls)
    # Crash directions
    PLUS_X = _m.PLUS_X
    MINUS_X = _m.MINUS_X
    PLUS_Y = _m.PLUS_Y
    MINUS_Y = _m.MINUS_Y

    # Data magnetism
    MAGNETIC = _m.MAGNETIC
    NOT_MAGNETIC = _m.NOT_MAGNETIC

    # Material weight/type
    HEAVY = _m.HEAVY
    MEDIUM = _m.MEDIUM
    LIGHT = _m.LIGHT
    FOAM = _m.FOAM
    PLASTIC = _m.PLASTIC

    # Fire topography
    TOP_A = _m.TOP_A
    TOP_B = _m.TOP_B
    TOP_C = _m.TOP_C

    # Water types
    FRESH_UNPOLLUTED = _m.FRESH_UNPOLLUTED
    FRESH_POLLUTED = _m.FRESH_POLLUTED
    SALTY_UNPOLLUTED = _m.SALTY_UNPOLLUTED
    SALTY_POLLUTED = _m.SALTY_POLLUTED

    # Seed plots
    BOTH = _m.BOTH
    NEITHER = _m.NEITHER
    ADJACENT = _m.ADJACENT
    DIAGONAL = _m.DIAGONAL

    # Hydrogen voltages/colors
    VOLTAGE_1 = _m.VOLTAGE_1
    VOLTAGE_2 = _m.VOLTAGE_2
    VOLTAGE_3 = _m.VOLTAGE_3
    VOLTAGE_4 = _m.VOLTAGE_4
    VOLTAGE_5 = _m.VOLTAGE_5

    WHITE = _m.WHITE
    RED = _m.RED
    YELLOW = _m.YELLOW
    GREEN = _m.GREEN
    BLUE = _m.BLUE

    # ----------------------------
    # Original config / state
    # ----------------------------

    WIFI_SSID = "umd-iot"

    # If MAC not found, either refuse or fall back.
    REQUIRE_KNOWN_MAC = True
    WIFI_PASS_FALLBACK = "MfGYtzSD6nvq"

    # Optional:
    WIFI_TXT_PATH = "enes100/wifi.txt"

    ROOM_IP_MAP = {
        1201: "10.112.9.116",
        1116: "10.112.9.114",
    }

    WS_PORT = 7755
    WS_PATH = "/ws"

    _RECONNECT_DELAY_MS = 2000
    _WS_RECV_TIMEOUT_S = 2

    _PING_PERIOD_MS = 5000
    _PING_MISS_LIMIT = 5

    _POSE_REQUEST_PERIOD_MS = 250  # 4Hz

    DEBUG = False

    # Mission formatter (auto-set from begin(teamType))
    _mission_fmt = MissionFormatter()

    _lock = None
    _thread_started = False
    _stop_flag = False

    _wlan = None
    _ws = None
    _connected = False

    _team_name = ""
    _team_type = ""
    _marker_id = -1
    _room_number = 0
    _vision_ip = "10.112.9.116"

    _wifi_pass = WIFI_PASS_FALLBACK
    _hostname = None
    _mac_str = None

    _x = -1.0
    _y = -1.0
    _theta = -1.0
    _visible = False

    _missed_pongs = 0

    _print_queue = []
    _PRINT_QUEUE_MAX = 20

    # -------- Public API --------

    @classmethod
    def begin(cls, teamName, teamType, markerId, roomNumber):
        if cls._lock is None:
            cls._lock = _thread.allocate_lock()

        with cls._lock:
            cls._team_name = str(teamName)
            cls._team_type = str(teamType)

            # Auto-set mission name from teamType (case-insensitive handled in mission.py)
            cls._mission_fmt.set_mission(cls._team_type)

            cls._marker_id = int(markerId)
            cls._room_number = int(roomNumber)
            cls._vision_ip = cls.ROOM_IP_MAP.get(cls._room_number, "10.112.9.116")
            cls._stop_flag = False

        cls._wifi_connect()

        if not cls._thread_started:
            cls._thread_started = True
            _thread.start_new_thread(cls._worker_thread, ())

        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < 5000:
            if cls.isConnected():
                return True
            time.sleep_ms(50)

        return cls.isConnected()

    @classmethod
    def isConnected(cls):
        with cls._lock:
            try:
                wlan_ok = (cls._wlan is not None and cls._wlan.isconnected())
            except Exception:
                wlan_ok = False
            return bool(wlan_ok and cls._connected and (cls._ws is not None))

    @classmethod
    def getX(cls):
        with cls._lock:
            return cls._x

    @classmethod
    def getY(cls):
        with cls._lock:
            return cls._y

    @classmethod
    def getTheta(cls):
        with cls._lock:
            return cls._theta

    @classmethod
    def isVisible(cls):
        with cls._lock:
            return bool(cls._visible)

    @classmethod
    def print(cls, msg):
        s = str(msg)
        with cls._lock:
            if len(cls._print_queue) >= cls._PRINT_QUEUE_MAX:
                cls._print_queue.pop(0)
            cls._print_queue.append(s)
        return True

    @classmethod
    def mission(cls, type, message):
        """
        Mimic mission submissions by printing standardized mission text.
        Prototype: Enes100.mission(int type, int message)
        """
        with cls._lock:
            fmt = cls._mission_fmt
        return fmt.handle(int(type), int(message), cls.print)

    @classmethod
    def stop(cls):
        with cls._lock:
            cls._stop_flag = True
        time.sleep_ms(200)

    @classmethod
    def addRoom(cls, roomNumber, visionIp):
        with cls._lock:
            cls.ROOM_IP_MAP[int(roomNumber)] = str(visionIp)

    # -------- Worker thread --------

    @classmethod
    def _worker_thread(cls):
        last_ping_ms = time.ticks_ms()
        last_pose_req_ms = time.ticks_ms()

        while True:
            with cls._lock:
                if cls._stop_flag:
                    break

            if not cls._wifi_ok():
                try:
                    cls._wifi_connect()
                except Exception as e:
                    if cls.DEBUG:
                        print("[enes100] wifi_connect failed:", repr(e))
                    cls._drop_ws()
                    time.sleep_ms(cls._RECONNECT_DELAY_MS)
                    continue

            if not cls._ws_ok():
                try:
                    cls._connect_ws_and_begin()
                    last_ping_ms = time.ticks_ms()
                    last_pose_req_ms = time.ticks_ms()
                except Exception as e:
                    if cls.DEBUG:
                        print("[enes100] ws_connect failed:", repr(e))
                    cls._drop_ws()
                    time.sleep_ms(cls._RECONNECT_DELAY_MS)
                    continue

            now = time.ticks_ms()

            cls._flush_print_queue()

            if time.ticks_diff(now, last_ping_ms) >= cls._PING_PERIOD_MS:
                last_ping_ms = now
                try:
                    cls._ws_send({"op": "ping", "teamName": cls._team_name, "status": "ping"})
                    with cls._lock:
                        cls._missed_pongs += 1
                        if cls._missed_pongs >= cls._PING_MISS_LIMIT:
                            if cls.DEBUG:
                                print("[enes100] missed pongs -> disconnect")
                            cls._drop_ws()
                            continue
                except Exception:
                    cls._drop_ws()
                    continue

            if time.ticks_diff(now, last_pose_req_ms) >= cls._POSE_REQUEST_PERIOD_MS:
                last_pose_req_ms = now
                try:
                    cls._ws_send({"op": "aruco", "teamName": cls._team_name})
                except Exception:
                    cls._drop_ws()
                    continue

            for _ in range(4):
                msg = None
                try:
                    msg = cls._ws_recv()
                except Exception:
                    cls._drop_ws()

                if not msg:
                    break

                cls._handle_message(msg)

            time.sleep_ms(10)

        cls._drop_ws()
        with cls._lock:
            cls._thread_started = False

    # -------- Internal helpers --------

    @classmethod
    def _wifi_ok(cls):
        with cls._lock:
            wlan = cls._wlan
        if wlan is None:
            return False
        try:
            return wlan.isconnected()
        except Exception:
            return False

    @staticmethod
    def _mac_bytes_to_str(mac_bytes):
        return ":".join("{:02x}".format(b) for b in mac_bytes)

    @classmethod
    def _read_wifi_txt_for_mac(cls, mac_str):
        # Optional path-based lookup if wifi.txt happens to exist
        try:
            with open(cls.WIFI_TXT_PATH, "r") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 3:
                        continue
                    name = parts[0].strip()
                    mac = parts[1].strip().lower()
                    pw = parts[2].strip()
                    if mac == mac_str.lower():
                        return name, pw
        except OSError:
            return None, None
        except Exception:
            return None, None
        return None, None

    @classmethod
    def _lookup_wifi_creds(cls, mac_str):
        # 1) try wifi.txt (if present)
        name, pw = cls._read_wifi_txt_for_mac(mac_str)
        if name and pw:
            return name, pw

        # 2) fallback to installed python mapping
        tup = WIFI_MAP.get(mac_str.lower())
        if tup:
            return tup[0], tup[1]

        return None, None

    @classmethod
    def _wifi_connect(cls):
        wlan = network.WLAN(network.STA_IF)

        with cls._lock:
            cls._wlan = wlan
        # DEBUG
        # Determine MAC and lookup creds
        # network.WLAN(network.AP_IF).active(False); wlan.active(True); wlan.active(False); wlan.config(mac=b'\xcc\x7b\x5c\x36\x91\x30'); wlan.active(True)
        try:
            mac_bytes = wlan.config("mac")
            mac_str = cls._mac_bytes_to_str(mac_bytes)
        except Exception:
            mac_str = None

        hostname = None
        password = None

        if mac_str:
            hostname, password = cls._lookup_wifi_creds(mac_str)
            with cls._lock:
                cls._mac_str = mac_str

        if not hostname or not password:
            if cls.REQUIRE_KNOWN_MAC:
                raise RuntimeError("MAC not found in wifi_db (and wifi.txt missing). mac={}".format(mac_str))
            hostname = None
            password = cls.WIFI_PASS_FALLBACK

        with cls._lock:
            cls._wifi_pass = password
            cls._hostname = hostname

        # Apply hostname if supported
        if hostname:
            try:
                wlan.config(dhcp_hostname=hostname)
            except Exception:
                pass

        # reset trick
        try:
            wlan.active(False)
            time.sleep(0.5)
        except Exception:
            pass

        wlan.active(True)
        time.sleep(0.5)

        try:
            ap = network.WLAN(network.AP_IF)
            ap.active(False)
        except Exception:
            pass

        if wlan.isconnected():
            return

        if cls.DEBUG:
            with cls._lock:
                print("[enes100] Connecting WiFi SSID={} mac={} host={}...".format(
                    cls.WIFI_SSID, cls._mac_str, cls._hostname
                ))

        wlan.connect(cls.WIFI_SSID, password)

        t0 = time.time()
        while not wlan.isconnected():
            if time.time() - t0 > 25:
                raise RuntimeError("WiFi connect timeout")
            time.sleep(0.2)

        if cls.DEBUG:
            print("[enes100] WiFi connected:", wlan.ifconfig())

    @classmethod
    def _ws_ok(cls):
        with cls._lock:
            return bool(cls._connected and (cls._ws is not None))

    @classmethod
    def _ws_url(cls):
        with cls._lock:
            ip = cls._vision_ip
        path = cls.WS_PATH
        if not path.startswith("/"):
            path = "/" + path
        return "ws://{}:{}{}".format(ip, cls.WS_PORT, path)

    @classmethod
    def _connect_ws_and_begin(cls):
        cls._drop_ws()

        url = cls._ws_url()
        if cls.DEBUG:
            print("[enes100] WS connecting:", url)

        ws = uwebsockets.connect(url)
        ws.settimeout(cls._WS_RECV_TIMEOUT_S)

        with cls._lock:
            cls._ws = ws

        cls._ws_send({
            "op": "begin",
            "teamName": cls._team_name,
            "aruco": int(cls._marker_id),
            "teamType": cls._team_type,
        })

        with cls._lock:
            cls._connected = True
            cls._missed_pongs = 0

    @classmethod
    def _drop_ws(cls):
        ws = None
        with cls._lock:
            ws = cls._ws
            cls._ws = None
            cls._connected = False
            cls._missed_pongs = 0
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass

    @classmethod
    def _ws_send(cls, obj):
        with cls._lock:
            ws = cls._ws
        if ws is None:
            raise RuntimeError("ws not connected")
        ws.send(json.dumps(obj))

    @classmethod
    def _ws_recv(cls):
        with cls._lock:
            ws = cls._ws
        if ws is None:
            return None
        try:
            return ws.recv()
        except OSError:
            return None

    @classmethod
    def _handle_message(cls, msg):
        try:
            data = json.loads(msg)
        except Exception:
            return

        op = str(data.get("op", "")).lower()

        if op == "aruco":
            try:
                x = float(data.get("x", -1.0))
                y = float(data.get("y", -1.0))
                t = float(data.get("theta", -1.0))
                vis = bool(data.get("is_visible", False))
            except Exception:
                x, y, t, vis = -1.0, -1.0, -1.0, False

            with cls._lock:
                cls._x = x
                cls._y = y
                cls._theta = t
                cls._visible = vis

        elif op == "ping":
            status = str(data.get("status", "")).lower()
            if status == "ping":
                try:
                    cls._ws_send({"op": "ping", "teamName": cls._team_name, "status": "pong"})
                except Exception:
                    cls._drop_ws()
            elif status == "pong":
                with cls._lock:
                    cls._missed_pongs = 0

    @classmethod
    def _flush_print_queue(cls):
        to_send = None
        with cls._lock:
            if cls._ws is None or not cls._connected or not cls._print_queue:
                return
            n = 3 if len(cls._print_queue) > 3 else len(cls._print_queue)
            to_send = cls._print_queue[:n]
            del cls._print_queue[:n]

        for s in to_send:
            try:
                cls._ws_send({"op": "print", "teamName": cls._team_name, "message": s})
            except Exception:
                cls._drop_ws()
                return

