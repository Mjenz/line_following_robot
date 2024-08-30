import numpy as np
import cv2
import serial
import os
from threading import Thread

# Serial port
ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=1)

# Define image crop dimensions
x = 640
y = 100

class VideoStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Set buffer to 1
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# Start the video stream thread
vs = VideoStream().start()

# Image processing loop
image_count = 0

while True:
    frame = vs.read()

    if frame is None:
        print("Failed to capture image")
        continue

    # Crop the region of interest
    img = frame[190:290, 0:640]

    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(gray_image, (3, 3), 0)
    _, binary = cv2.threshold(img_blur, 125, 200, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    if contours:
        # Find the largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Calculate moments of the largest contour
        M = cv2.moments(largest_contour)

        # Calculate the x-coordinate of the center
        if M['m00'] != 0.0:
            center = int(M['m10'] / M['m00'])
            ser.write((str(center) + '\n').encode())
            print("Final Average:", center)

    image_count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Stop the video stream
vs.stop()
cv2.destroyAllWindows()