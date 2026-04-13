# necessary for access to VS and other lib functions
from enes100 import Enes100
# Team Name, Mission Type, Aruco ID, Room Num
def simple_test():
    Enes100.begin('Testing123', 'DATA', 231, 1116)
    Enes100.print('Connected!')
    
    # Enes100.getX() -> your x coordinate. 0-4, in meters, -1 if aruco is not visible
    # Enes100.getY() -> your y coordinate. 0-2, in meters, -1 if aruco is not visible
    # Enes100.getTheta() -> your theta. -pi to pi, in radians, -1 if aruco is not visible
    
    # will print OTV coordinates if aruco id in begin statement is visible on arena
    if Enes100.isVisible():
        Enes100.print(f'We are at {Enes100.getX()=}, {Enes100.getY()=}, {Enes100.getTheta()=}')
    else:
        Enes100.print('Not visible.')

while(1):
    simple_test()
