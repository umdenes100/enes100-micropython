import network
import time
import json
import _thread

from . import uwebsockets


class Enes100:
    # Fixed SSID (as requested)
    WIFI_SSID = "umd-iot"

    # If a MAC isn't found in wifi.txt, fall back to this password (optional).
    # You can set to "" to force "must be in wifi.txt".
    WIFI_PASS_FALLBACK = "MfGYtzSD6nvq"

    # wifi.txt location (relative to filesystem root)
    WIFI_TXT_PATH = "enes100/wifi.txt"

    # Room -> Vision IP mapping
    ROOM_IP_MAP = {
        1201: "10.112.9.116",
        1116: "10.112.9.114",
    }

    WS_PORT = 7755
    WS_PATH = "/ws"

    # Timing
    _RECONNECT_DELAY_MS = 2000
    _WS_RECV_TIMEOUT_S = 2

    _PING_PERIOD_MS = 5000
    _PING_MISS_LIMIT = 5

    _POSE_REQUEST_PERIOD_MS = 250  # 4Hz

    DEBUG = False

    # --- internal shared state (protected by _lock) ---
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

    # Dynamic WiFi credentials/hostname from wifi.txt
    _wifi_pass = WIFI_PASS_FALLBACK
    _hostname = None
    _mac_str = None

    _x = -1.0
    _y = -1.0
    _theta = -1.0
    _visible = False

    _missed_pongs = 0

    # Print queue (bounded)
    _print_queue = []
    _PRINT_QUEUE_MAX = 20

    # -------- Public API --------

    @classmethod
    def begin(cls, teamName, teamType, markerId, roomNumber):
        """
        Starts background thread that maintains WiFi + WS and updates pose.

        Also:
          - reads MAC address
          - looks up password + hostname in enes100/wifi.txt
          - sets dhcp hostname
        """
        if cls._lock is None:
            cls._lock = _thread.allocate_lock()

        with cls._lock:
            cls._team_name = str(teamName)
            cls._team_type = str(teamType)
            cls._marker_id = int(markerId)
            cls._room_number = int(roomNumber)
            cls._vision_ip = cls.ROOM_IP_MAP.get(cls._room_number, "10.112.9.116")

            cls._stop_flag = False

        # Ensure WiFi at least once before starting thread (fail-fast)
        cls._wifi_connect()

        # Start worker thread once
        if not cls._thread_started:
            cls._thread_started = True
            _thread.start_new_thread(cls._worker_thread, ())

        # Block briefly waiting for first connection attempt
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
        """
        Queue a print message to be sent by the background thread.
        """
        s = str(msg)
        with cls._lock:
            if len(cls._print_queue) >= cls._PRINT_QUEUE_MAX:
                cls._print_queue.pop(0)
            cls._print_queue.append(s)
        return True

    @classmethod
    def stop(cls):
        """
        Optional: stop background thread and close WS.
        """
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

            # Ensure WiFi
            if not cls._wifi_ok():
                try:
                    cls._wifi_connect()
                except Exception as e:
                    if cls.DEBUG:
                        print("[enes100] wifi_connect failed:", repr(e))
                    cls._drop_ws()
                    time.sleep_ms(cls._RECONNECT_DELAY_MS)
                    continue

            # Ensure WS
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

            # Send queued prints
            cls._flush_print_queue()

            # Client ping
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

            # Pose request
            if time.ticks_diff(now, last_pose_req_ms) >= cls._POSE_REQUEST_PERIOD_MS:
                last_pose_req_ms = now
                try:
                    cls._ws_send({"op": "aruco", "teamName": cls._team_name})
                except Exception:
                    cls._drop_ws()
                    continue

            # Receive a few messages (non-blocking-ish due to timeout)
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
        # mac_bytes is bytes-like length 6
        return ":".join("{:02x}".format(b) for b in mac_bytes)

    @classmethod
    def _read_wifi_txt_for_mac(cls, mac_str):
        """
        Parse enes100/wifi.txt lines:
          NAME<TAB>MAC<TAB>PASSWORD

        Returns (hostname, password) or (None, None) if not found.
        Ignores blank lines and lines starting with '#'.
        """
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
            # file missing
            return None, None
        except Exception:
            return None, None

        return None, None

    @classmethod
    def _wifi_connect(cls):
        wlan = network.WLAN(network.STA_IF)

        # Store early
        with cls._lock:
            cls._wlan = wlan

        # Determine MAC and lookup wifi.txt (do this before connect)
        try:
            mac_bytes = wlan.config("mac")
            mac_str = cls._mac_bytes_to_str(mac_bytes)
        except Exception:
            mac_str = None

        hostname = None
        password = None

        if mac_str is not None:
            hostname, password = cls._read_wifi_txt_for_mac(mac_str)
            with cls._lock:
                cls._mac_str = mac_str

        if hostname is None or password is None:
            # Not found; fall back
            password = cls.WIFI_PASS_FALLBACK
            hostname = None

        # Save chosen creds
        with cls._lock:
            cls._wifi_pass = password
            cls._hostname = hostname

        # Apply hostname if possible (ESP32 MicroPython supports dhcp_hostname on many builds)
        if hostname:
            try:
                wlan.config(dhcp_hostname=hostname)
            except Exception:
                # Not supported on this firmware; ignore
                pass

        # reset trick (prevents internal state error)
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

        # BEGIN message (matches your working client)
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
                # reply pong
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
                cls._ws_send({
                    "op": "print",
                    "teamName": cls._team_name,
                    "message": s,
                })
            except Exception:
                cls._drop_ws()
                return

