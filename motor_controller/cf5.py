import numpy as np
import cv2
from picamera import PiCamera
import PIL.Image
from io import BytesIO
import serial
import os

# Camera settings
res_y, res_x = 120, 160  # Reduced resolution
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

def detect_edges_canny(image):
    """Detect edges using Canny edge detection and return edge coordinates."""
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    canny_edges = cv2.Canny(gray_image, 100, 200)
    edge_locations = np.column_stack(np.where(canny_edges > 0))
    return edge_locations, canny_edges

def average_edge_columns_per_row(edge_locations, img_height, img_width):
    """Calculate the average column position for each row with detected edges."""
    row_avg = np.zeros(img_height)
    row_counts = np.zeros(img_height)
    
    for y, x in edge_locations:
        row_avg[y] += x
        row_counts[y] += 1
    
    # Avoid division by zero
    row_avg[row_counts > 0] /= row_counts[row_counts > 0]
    
    return row_avg

# Capture and process image stream
stream = BytesIO()
image_count = 0

for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
    stream.seek(0)
    img = np.array(PIL.Image.open(stream))
    
    if img.ndim == 3 and img.shape[2] == 3:
        # Save the original image for debugging
        image_filename = os.path.join(output_dir, f"original_image_{image_count:04d}.jpg")
        cv2.imwrite(image_filename, img)
        
        # Detect edges using Canny
        edge_locations, canny_edges = detect_edges_canny(img)
        
        # Save the Canny edge image for debugging
        canny_filename = os.path.join(output_dir, f"canny_edges_{image_count:04d}.jpg")
        cv2.imwrite(canny_filename, canny_edges)
        
        # Calculate average column positions per row
        row_avg = average_edge_columns_per_row(edge_locations, res_y, res_x)
        
        print("Row-wise average column positions:", row_avg)
        
        # Combine and calculate the final average (if needed)
        if row_avg.size > 0:
            final_average = np.mean(row_avg) / res_x * 100
            ser.write((str(final_average) + '\n').encode())
            print("Final Average:", final_average)
        
    else:
        print("Image does not have 3 channels, skipping edge detection.")

    image_count += 1

    # Clear stream
    stream.seek(0)
    stream.truncate()
