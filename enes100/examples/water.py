# necessary for access to VS and other lib functions
from enes100 import enes100

# Team Name, Mission Type, Aruco ID, Room Num
enes100.begin('Under the Sea', 'WATER', 210, 1116)

# There is no get function in the micropython library... the location vars are automatically updated.
# Enes100.x -> your x coordinate. 0-4, in meters, -1 if aruco is not visible
# Enes100.y -> your y coordinate. 0-2, in meters, -1 if aruco is not visible
# Enes100.theta -> your theta. -pi to pi, in radians, -1 if aruco is not visible

# will print OTV coordinates if aruco id in begin statement is visible on arena
if enes100.is_visible:
    enes100.print(f'We are at {enes100.x=} {enes100.y=} {enes100.theta=}')
else:
    enes100.print('Not visible.')

enes100.mission('DEPTH', 30) # Transmit the depth of the water in the pool
enes100.mission('WATER_TYPE', 'FRESH_UNPOLLUTED') # transmit the state of the pool
