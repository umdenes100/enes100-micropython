# necessary for access to VS and other lib functions
from enes100 import Enes100

# Team Name, Mission Type, Aruco ID, Room Num
Enes100.begin('What is it?', 'MATERIALS', 210, 1116)

# There is no get function in the micropython library... the location vars are automatically updated.
# Enes100.getX() -> your x coordinate. 0-4, in meters, -1 if aruco is not visible
# Enes100.getY() -> your y coordinate. 0-2, in meters, -1 if aruco is not visible
# Enes100.getTheta() -> your theta. -pi to pi, in radians, -1 if aruco is not visible

# will print OTV coordinates if aruco id in begin statement is visible on arena
if Enes100.isVisible():
    Enes100.print(f'We are at {Enes100.getX()=}, {Enes100.getY()=}, {Enes100.getTheta()=}')
else:
    Enes100.print("Not visible.")

Enes100.mission(WEIGHT, LIGHT) # Transmit the weight of the material 
Enes100.mission(MATERIAL_TYPE, FOAM) # Transmit the material type 

