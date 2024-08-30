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
    stream.seek(0)
    img = np.array(PIL.Image.open(stream))
    
    # Thresholding
    _, thresh1 = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
    
    # Vertical scan
    vert_line = np.argmax(thresh1[:, :int(res_y/2)], axis=1)
    vert_line = vert_line[vert_line > 0]
    
    # Horizontal scan
    horiz_line = np.argmax(thresh1[int(res_x/3):, :], axis=0)
    horiz_line = horiz_line[horiz_line > 0]
    
    # Combine and average
    combined_lines = np.hstack((vert_line, horiz_line))
    if combined_lines.size > 0:
        final_average = np.mean(combined_lines)
        ser.write((str(final_average) + '\n').encode())
        print(final_average)
    
    # Clear stream
    stream.seek(0)
    stream.truncate()