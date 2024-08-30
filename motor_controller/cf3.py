import numpy as np
from io import BytesIO
from time import sleep
import cv2
from picamera import PiCamera
import serial
import PIL.Image
import os

# Camera settings
res_y, res_x = 240, 320
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
image_count = 0  # Counter to keep track of image files

for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
    stream.seek(0)
    img = np.array(PIL.Image.open(stream))
    
    # Thresholding
    _, thresh1 = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
    
    # Save the thresholded image for later debugging
    image_filename = os.path.join(output_dir, f"thresholded_image_{image_count:04d}.jpg")
    cv2.imwrite(image_filename, thresh1)
    image_count += 1  # Increment the image counter
    
    # Vertical scan
    vert_line_left = np.argmax(thresh1[:, :int(res_y/2)], axis=1)
    vert_line_right = np.argmax(thresh1[:, int(res_y/2)::-1], axis=1)
    
    
    # Horizontal scan
    horiz_line_left = np.argmax(thresh1[int(res_x/3):, :], axis=0)
    horiz_line_right = np.argmax(thresh1[int(res_x/3):, ::-1], axis=0)
    
    
    # Adjust right-side results to match the original coordinate system
    vert_line_right = res_y - 1 - vert_line_right
    horiz_line_right = res_x - 1 - horiz_line_right

    # Filter out non-detections (values of zero)
    vert_line_left = vert_line_left[vert_line_left > 0]
    vert_line_right = vert_line_right[vert_line_right > 0]
    horiz_line_left = horiz_line_left[horiz_line_left > 0]
    horiz_line_right = horiz_line_right[horiz_line_right > 0]

    # Ensure both arrays have the same length
    vert_min_length = min(len(vert_line_left), len(vert_line_right))
    horiz_min_length = min(len(horiz_line_left), len(horiz_line_right))
    if vert_min_length > 0:
        # Take only the first `min_length` elements to match lengths
        vert_line_left = vert_line_left[:vert_min_length]
        vert_line_right = vert_line_right[:vert_min_length]
        
        # Calculate the average positions
        avg_vertical_edges = (vert_line_left + vert_line_right) / 2.0
        

    if horiz_min_length > 0:
         # Take only the first `min_length` elements to match lengths
        horiz_line_left = horiz_line_left[:horiz_min_length]
        horiz_line_right = horiz_line_right[:horiz_min_length]
        
        # Calculate the average positions
        avg_horizontal_edges = (horiz_line_left + horiz_line_right) / 2.0
        

    # Combine and average
    combined_lines = np.hstack((avg_vertical_edges, avg_horizontal_edges))
    print("Combined Line Positions:", combined_lines)  # Debugging output

    if combined_lines.size > 0:
        final_average = np.mean(combined_lines) / res_x * 100
        ser.write((str(final_average) + '\n').encode())
        print("Final Average:", final_average)
    
    # Clear stream
    stream.seek(0)
    stream.truncate()

