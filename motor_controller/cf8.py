import numpy as np
import cv2
import serial
import os

# Camera settings
# res_y, res_x = 120, 176  # Reduced resolution

# Serial port
ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=1)

# Create a directory for saving images if it doesn't exist
output_dir = "/home/alazartegegnework/captured_images_2"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Capture and process image stream
image_count = 0

# Define image crop dimensions
x = 640
y = 100

capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Set buffer to 1 so that it analyzes the most up to date photo

if not capture.isOpened():
    print("Error: Could not open video capture")
    exit()

while True:
    ret, image = capture.read()
    
    if not ret:
        print("Failed to capture image")
        continue
    # file_name = os.path.join(output_dir, f"before_{image_count:04d}.jpg")
    # cv2.imwrite(file_name, image)

    # Crop the region of interest
    img = image[190:290, 0:640]
    img_name = os.path.join(output_dir, f"img_{image_count:04d}.jpg")
    cv2.imwrite(img_name, img)
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_name = os.path.join(output_dir, f"gray_{image_count:04d}.jpg")
    cv2.imwrite(gray_name, gray_image)
    img_blur = cv2.GaussianBlur(gray_image,(3,3), 0)
    _, binary = cv2.threshold(img_blur, 125, 200, cv2.THRESH_BINARY)
    thresh_name = os.path.join(output_dir, f"binary_{image_count:04d}.jpg")
    cv2.imwrite(thresh_name, binary)
    # contours, contours_image = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    contours, contours_image = cv2.findContours(binary, 1, cv2.CHAIN_APPROX_NONE)
    contours_name = os.path.join(output_dir, f"contour_{image_count:04d}.jpg")
    cv2.imwrite(contours_name, contours_image)

    if contours:
        # find the largest contour because its the line
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate moments of the largest contour
        M = cv2.moments(largest_contour)
        
        # Calculate the x, y coordinates of the center
        if M['m00'] != 0.0:
            center = int(M['m10'] / M['m00'])
    
    ser.write((str(center) + '\n').encode())
    print("Final Average:", (center))

    image_count += 1