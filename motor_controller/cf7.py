import numpy as np
import cv2
import serial
import os

# Camera settings
res_y, res_x = 120, 176  # Reduced resolution

# Serial port
ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=1)

# Create a directory for saving images if it doesn't exist
output_dir = "/home/mjenz/captured_images"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Skipping factor
skip_factor = 2  # Process every 2nd row

def detect_edges_canny(image):
    """Detect edges using Canny edge detection and return edge coordinates."""
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    canny_edges = cv2.Canny(gray_image, 100, 200)
    edge_locations = np.column_stack(np.where(canny_edges > 0))
    return edge_locations, canny_edges

def average_edge_columns_per_row(edge_locations, img_height, skip_factor):
    """Calculate the average column position for each row with detected edges, skipping rows."""
    row_avg = np.zeros(img_height)
    row_counts = np.zeros(img_height)
    
    for y, x in edge_locations:
        if y % skip_factor == 0:  # Skip rows based on the factor
            row_avg[y] += x
            row_counts[y] += 1
    
    # Avoid division by zero
    row_avg[row_counts > 0] /= row_counts[row_counts > 0]
    
    return row_avg

# Capture and process image stream
capture = cv2.VideoCapture(0)

if not capture.isOpened():
    print("Error: Could not open video capture")
    exit()

# Set camera properties to reduce latency
capture.set(cv2.CAP_PROP_FRAME_WIDTH, res_x)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, res_y)
capture.set(cv2.CAP_PROP_FPS, 30)

# x = 720
# y = 100

while True:
    ret, img = capture.read()
    
    if not ret:
        print("Failed to capture image")
        continue
    
    # Crop the region of interest
    # img = image[200:300, 0:x]
    
    if img.ndim == 3 and img.shape[2] == 3:
        # Detect edges using Canny
        edge_locations, _ = detect_edges_canny(img)
        
        # Calculate average column positions per row with row skipping
        row_avg = average_edge_columns_per_row(edge_locations, res_y, skip_factor)
        
        # Calculate and send the final average column position
        if row_avg.size > 0:
            final_average = np.mean(row_avg[row_avg > 0]) / res_x * 100  # Normalize to percentage
            ser.write((str(final_average) + '\n').encode())
            print("Final Average:", final_average)
    else:
        print("Image does not have 3 channels, skipping edge detection.")

    # image_count += 1