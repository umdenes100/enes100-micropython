# necessary for access to VS and other lib functions
from enes100 import *

def simple_test():
    # Team Name, Mission Type, Aruco ID, Room Num
    Enes100.begin("Name pending...", DATA, 205, 1116)
    Enes100.println("Connected!")
    
    # There is no get function in the micropython library... the location vars are automatically updated.
    # Enes100.x -> your x coordinate. 0-4, in meters, -1 if aruco is not visible
    # Enes100.y -> your y coordinate. 0-2, in meters, -1 if aruco is not visible
    # Enes100.theta -> your theta. -pi to pi, in radians, -1 if aruco is not visible
    
    # will print OTV coordinates if aruco id in begin statement is visible on arena
    if Enes100.is_visible:
        Enes100.print(f"We are at {Enes100.x=} {Enes100.y=} {Enes100.theta=}")
    else:
        Enes100.print("Not visible.")

simple_test()