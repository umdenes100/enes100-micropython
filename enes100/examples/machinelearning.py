# necessary for access to VS and other lib functions
from enes100ml import enes100
import time

# enes100.begin('Team Name', 'Mission Type', Aruco ID, Room Num, Tx Pin, Rx Pin)
enes100.begin('asimple2dmodel', 'SEED', 210, 1116, 17, 16)

while(1):
    enes100.print('Requesting prediction...')
    result = enes100.ml_get_prediction(1)
    enes100.print('Prediction result:' + str(result))
    time.sleep(5)
