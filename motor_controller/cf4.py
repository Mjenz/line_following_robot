import numpy as np
from io import BytesIO
import cv2
from picamera import PiCamera
import serial
import PIL.Image
import os

# Camera settings
res_y, res_x = 120, 120
camera = PiCamera()
camera.resolution = (res_x, res_y)
camera.framerate = 30
camera.iso = 400
camera.exposure_mode = 'sports'
camera.color_effects = (128, 128)
camera.shutter_speed = 10000

# Serial port
ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=1)

# Create a directory for saving images if it doesn't exist
output_dir = "/home/mjenz/captured_images"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Capture and process image stream
stream = BytesIO()
image_count = 0

for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
    stream.seek(0)
    img = np.array(PIL.Image.open(stream))
    
    # Thresholding
    _, thresh1 = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
    
    # Save the thresholded image for later debugging
    image_filename = os.path.join(output_dir, f"thresholded_image_{image_count:04d}.jpg")
    cv2.imwrite(image_filename, thresh1)
    image_count += 1
    
    # Initialize arrays to store detected edges for vertical and horizontal scans
    vertical_centers = []
    horizontal_centers = []

    # Vertical scan (left-to-right and right-to-left)
    for k in range(0, res_y):
        left_edge = np.argmax(thresh1[:, k] > 100)
        right_edge = np.argmax(thresh1[::-1, k] > 100)
        
        if right_edge != 0:  # If an edge is found
            right_edge = res_x - right_edge
        
        if left_edge > 0 and right_edge > 0:
            vertical_center = (left_edge + right_edge) / 2.0
            vertical_centers.append(vertical_center)

    # Horizontal scan (top-to-bottom and bottom-to-top)
    for i in range(0, res_x):
        top_edge = np.argmax(thresh1[i, :] > 100)
        bottom_edge = np.argmax(thresh1[i, ::-1] > 100)
        
        if bottom_edge != 0:  # If an edge is found
            bottom_edge = res_y - bottom_edge
        
        if top_edge > 0 and bottom_edge > 0:
            horizontal_center = (top_edge + bottom_edge) / 2.0
            horizontal_centers.append(horizontal_center)
    
    # Combine results from both scans
    combined_centers = vertical_centers + horizontal_centers

    # Filter out zeros (non-detections) and compute the average center position
    combined_centers = [c for c in combined_centers if c > 0]
    if len(combined_centers) > 0:
        final_average = np.mean(combined_centers) / res_x * 100
        ser.write((str(final_average) + '\n').encode())
        print("Final Average:", final_average)
    
    # Clear stream
    stream.seek(0)
    stream.truncate()
