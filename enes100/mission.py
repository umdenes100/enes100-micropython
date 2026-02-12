# mission.py
# MicroPython-friendly (no Enum dependency). Just integer constants and dict maps.

# ----------------------------
# Mission "type" enums (first argument to Enes100.mission)
# ----------------------------

# CRASH
DIRECTION = 0
LENGTH = 1
HEIGHT = 2

# DATA
CYCLE = 0
MAGNETISM = 1

# MATERIAL
WEIGHT = 0
MATERIAL_TYPE = 1

# FIRE
NUM_CANDLES = 0
TOPOGRAPHY = 1

# WATER
DEPTH = 0
WATER_TYPE = 1

# SEED
LOCATION = 0

# HYDROGEN
LED_COLOR = 0
VOLTAGE_OUTPUT = 1


# ----------------------------
# Value enums (second argument to Enes100.mission)
# ----------------------------

# CRASH directions
PLUS_X = 0
MINUS_X = 1
PLUS_Y = 2
MINUS_Y = 3

# DATA magnetism
MAGNETIC = 0
NOT_MAGNETIC = 1

# MATERIAL weight
HEAVY = 0
MEDIUM = 1
LIGHT = 2

# MATERIAL type (maps to squishy/not squishy wording you gave)
FOAM = 0
PLASTIC = 1

# FIRE topography
TOP_A = 0
TOP_B = 1
TOP_C = 2

# WATER types
FRESH_UNPOLLUTED = 0
FRESH_POLLUTED = 1
SALTY_UNPOLLUTED = 2
SALTY_POLLUTED = 3

# SEED plot locations (plantable substrate)
BOTH = 0
NEITHER = 1
ADJACENT = 2
DIAGONAL = 3

# HYDROGEN voltages
VOLTAGE_1 = 1
VOLTAGE_2 = 2
VOLTAGE_3 = 3
VOLTAGE_4 = 4
VOLTAGE_5 = 5

# HYDROGEN LED colors
WHITE = 0
RED = 1
YELLOW = 2
GREEN = 3
BLUE = 4


# ----------------------------
# Internal helpers
# ----------------------------

def _norm_mission_name(name):
    # Accept lower/upper/Title-case etc.
    if name is None:
        return ""
    return str(name).strip().upper()

def _qmarks():
    return "?????"

def _wrap(sentence):
    # Mimic Vision System mission formatting style
    # (Mission submissions in VS typically show "MISSION MESSAGE: ...")
    return "MISSION MESSAGE: " + sentence

# ----------------------------
# Mission formatter core
# ----------------------------

class MissionFormatter:
    def __init__(self):
        self._mission = ""  # normalized uppercase

    def set_mission(self, mission_name):
        self._mission = _norm_mission_name(mission_name)

    def get_mission(self):
        return self._mission

    def handle(self, mtype, msg, print_func):
        """
        mtype: int (first arg)
        msg: int (second arg) but we accept anything convertible
        print_func: callable(str) -> bool (Enes100.print)
        """
        mission = self._mission

        # If mission isn't set, still print something obvious
        if not mission:
            s = _wrap("Mission is not set. Got type={} message={}.".format(mtype, msg))
            return print_func(s)

        # Route by mission name
        if mission in ("CRASH", "CRASH_SITE", "CRASHSITE"):
            out = self._crash(mtype, msg)
        elif mission == "DATA":
            out = self._data(mtype, msg)
        elif mission == "MATERIAL":
            out = self._material(mtype, msg)
        elif mission == "FIRE":
            out = self._fire(mtype, msg)
        elif mission == "WATER":
            out = self._water(mtype, msg)
        elif mission == "SEED":
            out = self._seed(mtype, msg)
        elif mission == "HYDROGEN":
            out = self._hydrogen(mtype, msg)
        else:
            out = _wrap("Unknown mission '{}'.".format(mission))

        return print_func(out)

    # ---- Per-mission implementations ----

    def _crash(self, mtype, msg):
        if mtype == DIRECTION:
            dirmap = {
                PLUS_X: "+x",
                MINUS_X: "-x",
                PLUS_Y: "+y",
                MINUS_Y: "-y",
            }
            direction = dirmap.get(int(msg), _qmarks())
            return _wrap("The direction of the abnormality is in the {} direction.".format(direction))

        if mtype == LENGTH:
            return _wrap("The length of the side with abnormality is {}mm.".format(int(msg)))

        if mtype == HEIGHT:
            return _wrap("The height of the side with abnormality is {}mm.".format(int(msg)))

        return _wrap("The direction of the abnormality is in the {} direction.".format(_qmarks()))

    def _data(self, mtype, msg):
        if mtype == CYCLE:
            return _wrap("The duty cycle is {}%.".format(int(msg)))

        if mtype == MAGNETISM:
            magmap = {
                MAGNETIC: "MAGNETIC",
                NOT_MAGNETIC: "NOT MAGNETIC",
            }
            m = magmap.get(int(msg), _qmarks())
            if m == _qmarks():
                return _wrap("The disk is {}.".format(m))
            return _wrap("The disk is {}.".format(m))

        return _wrap("The disk is {}.".format(_qmarks()))

    def _material(self, mtype, msg):
        if mtype == WEIGHT:
            wmap = {
                HEAVY: "HEAVY",
                MEDIUM: "MEDIUM",
                LIGHT: "LIGHT",
            }
            w = wmap.get(int(msg), _qmarks())
            return _wrap("The weight of the material is {}.".format(w))

        if mtype == MATERIAL_TYPE:
            # You asked for FOAM/PLASTIC calls but mission text is SQUISHY / NOT SQUISHY
            tmap = {
                FOAM: "SQUISHY",
                PLASTIC: "NOT SQUISHY",
            }
            t = tmap.get(int(msg), _qmarks())
            if t == "SQUISHY":
                return _wrap("The material is SQUISHY.")
            if t == "NOT SQUISHY":
                return _wrap("The material is NOT SQUISHY.")
            return _wrap("The material is {}.".format(_qmarks()))

        return _wrap("The material is {}.".format(_qmarks()))

    def _fire(self, mtype, msg):
        if mtype == NUM_CANDLES:
            return _wrap("The number of candles lit is {}.".format(int(msg)))

        if mtype == TOPOGRAPHY:
            tmap = {TOP_A: "A", TOP_B: "B", TOP_C: "C"}
            t = tmap.get(int(msg), _qmarks())
            return _wrap("The topography of the fire mission is:  {}".format(t))

        return _wrap("The topography of the fire mission is:  {}".format(_qmarks()))

    def _water(self, mtype, msg):
        if mtype == DEPTH:
            return _wrap("The depth of the water is {}mm.".format(int(msg)))

        if mtype == WATER_TYPE:
            wmap = {
                FRESH_UNPOLLUTED: "FRESH and UNPOLLUTED",
                FRESH_POLLUTED: "FRESH and POLLUTED",
                SALTY_UNPOLLUTED: "SALTY and UNPOLLUTED",
                SALTY_POLLUTED: "SALTY and POLLUTED",
            }
            w = wmap.get(int(msg), _qmarks())
            if w == _qmarks():
                return _wrap("The water is {}.".format(_qmarks()))
            return _wrap("The water is {}.".format(w))

        return _wrap("The water is {}.".format(_qmarks()))

    def _seed(self, mtype, msg):
        if mtype == LOCATION:
            pmap = {
                BOTH: "BOTH",
                NEITHER: "NEITHER",
                ADJACENT: "ADJACENT",
                DIAGONAL: "DIAGONAL",
            }
            p = pmap.get(int(msg), _qmarks())
            return _wrap("The far plots are {} plantable substrate.".format(p))

        return _wrap("The far plots are {} plantable substrate.".format(_qmarks()))

    def _hydrogen(self, mtype, msg):
        if mtype == VOLTAGE_OUTPUT:
            v = int(msg)
            if v in (1, 2, 3, 4, 5):
                return _wrap("The voltage output is {} VOLT{}.".format(v, "" if v == 1 else "S"))
            return _wrap("The voltage output is {}.".format(_qmarks()))

        if mtype == LED_COLOR:
            cmap = {
                WHITE: "WHITE",
                RED: "RED",
                YELLOW: "YELLOW",
                GREEN: "GREEN",
                BLUE: "BLUE",
            }
            c = cmap.get(int(msg), _qmarks())
            return _wrap("The LED color is {}.".format(c))

        return _wrap("The LED color is {}.".format(_qmarks()))

