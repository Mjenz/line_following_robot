import numpy as np
from io import BytesIO
from time import sleep
import cv2
from picamera import PiCamera
import serial  # Ensure this is correct
import PIL.Image
print("Things imported")

# resolution
res_y = 120
res_x = 120

# init camera, check the test code on the thing rn
camera = PiCamera()
camera.resolution = (res_x, res_y)
camera.framerate = 30            # max framerate
camera.iso = 400               
camera.exposure_mode = 'sports'  # Fast exposure mode
camera.color_effects = (128,128) # turn camera to black and white
camera.shutter_speed = 10000    # Fast shutter speed for quick capture
print("Camera initialized")

# serial port initialization
ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=1)
print("Serial open")

# capture test picture
camera.capture('/home/mjenz/image.jpg')

# Use continuous capture mode
stream = BytesIO()
for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
    # Reading image 
    stream.seek(0)
    img = np.array(PIL.Image.open(stream))      # turn image black and white (redundant?)
    ret, thresh1 = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)  # Use threshholding

    decimator = 10                                      # decimator for for loop to increase speed
    decimator2 = 3
    avg_all = np.zeros((res_x + res_y))                 # the percentage across the frame this pixle is
    reached_line = 0                                    # boolean to track line finding

    # vertical scan
    for k in range(0,int(res_y/2),decimator):            # loop through y vals, stop 1/2 through
        for i in range(0,res_x,decimator2):                           # loop through x vals
            if thresh1[i,k] > 100 and not reached_line: # wait for first edge of line
                reached_line = 1                        # turn on bool
            elif reached_line and thresh1[i,k] > 100:   # wait for line to dissapear
                continue                                # do nothing
            elif reached_line:                          # once intensity has dropped below the threshold
                reached_line = 0                        # turn off bool
                avg_all[k] = k/res_y * 100               # record x val percentage across picture
        if reached_line:                                # check if there was a line found
            reached_line = 0                            # reset so that there are no cross line averages

    # horizontal scan
    for i in range(int(res_x/3),res_x,decimator):       # loop through x vals, start 1/3 through
        for k in range(0,res_y,decimator2):                          # loop through y vals
            if thresh1[i,k] > 100 and not reached_line: # wait for first edge of line
                reached_line = 1                        # turn on bool
                one = k                                 # record x value
            elif reached_line and thresh1[i,k] > 100:   # wait for line to dissapear
                continue                                # do nothing
            elif reached_line:                          # once intensity has dropped below the threshold
                reached_line = 0                        # turn off bool
                two = k                                 # record x value
                a = int((one+two)/2)                    # rind center of the line
                avg_all[res_y + i] = a/res_y * 100      # record center of the line
        if reached_line:                                # check if there wwas a line found
            reached_line = 0                            # reset so that there are no cross line averages

    
    
    no_zeros_avg = avg_all[avg_all != 0.0]              # get rid of all extra indicies
    print(no_zeros_avg)
    final_average = np.average(no_zeros_avg)            # get average
        
    ser.write((str(final_average) + '\n').encode())     # send it over UART
    print("Run executed")
    print(final_average)

