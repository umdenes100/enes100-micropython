# necessary for access to VS and other lib functions
from enes100 import enes100
# Team Name, Mission Type, Aruco ID, Room Num
def simple_test():
    enes100.begin('Name pending...', 'DATA', 231, 1116)
    enes100.print('Connected!')
    
    # There is no get function in the micropython library... the location vars are automatically updated.
    # enes100.x -> your x coordinate. 0-4, in meters, -1 if aruco is not visible
    # enes100.y -> your y coordinate. 0-2, in meters, -1 if aruco is not visible
    # enes100.theta -> your theta. -pi to pi, in radians, -1 if aruco is not visible
    
    # will print OTV coordinates if aruco id in begin statement is visible on arena
   
   while True:
       enes100.print(f'We are at {enes100.x=} {enes100.y=} {enes100.theta=}')
       enes100.print(f'Aruco Visible? {enes100.is_visible=}')
       enes100.pring(f'Connnected? {enes100.is_connected()}')

simple_test()