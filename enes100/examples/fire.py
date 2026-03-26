# necessary for access to VS and other lib functions
from enes100 import Enes100

# Team Name, Mission Type, Aruco ID, Room Num
Enes100.begin('It\'s Lit!', 'FIRE', 210, 1116)

# enes100.x -> your x coordinate. 0-4, in meters, -1 if aruco is not visible
# enes100.y -> your y coordinate. 0-2, in meters, -1 if aruco is not visible
# enes100.theta -> your theta. -pi to pi, in radians, -1 if aruco is not visible

# will print OTV coordinates if aruco id in begin statement is visible on arena
if Enes100.isVisible():
    Enes100.print(f'We are at {Enes100.getX()=} {Enes100.getY()=} {Enes100.getTheta()=}')
else:
    Enes100.print('Not visible.')

Enes100.mission(NUM_CANDLES, 3) # Transmit the number of fires lit
Enes100.mission(TOPOGRAPHY, TOP_A) # Transmit topography of the fire mission
