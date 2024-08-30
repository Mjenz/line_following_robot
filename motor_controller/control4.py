from PIL import Image
import numpy as np
from io import BytesIO
from time import sleep
from picamera import PiCamera
import serial  # Ensure this is correct

# Adjusted resolution
resolution_x = 320  # Reduced resolution
resolution_y = 240   # Reduced resolution
VALUE = 400
skip = 4  # Adjusted to ensure sufficient sampling
skip_ah = 60
weights = [i/resolution_y for i in range(0,resolution_y,skip_ah)]
# Initialize
camera = PiCamera()
camera.resolution = (resolution_x, resolution_y)
camera.framerate = 30
camera.iso = 800
camera.exposure_mode = 'sports'  # Fast exposure mode
camera.shutter_speed = 10000     # Fast shutter speed for quick capture

# Correct serial port initialization
ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=1)
print("Serial open")

def find_edges(sum_list, skip):
    start = end = -1
    trigger = False
    for i in range(len(sum_list)):
        if sum_list[i] > VALUE and not trigger:
            start = i * skip
            trigger = True
        elif sum_list[i] < VALUE and trigger:
            end = i * skip
            break
    if end == -1:
        end = len(sum_list) * skip
    return start, end

# Allow the camera to warm up
#`sleep(2)

# Use continuous capture mode
stream = BytesIO()

for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
    try:
        stream.seek(0)
        img = Image.open(stream)
        img_data = np.array(img.convert('RGB'))

        # Extract and sum the RGB values for the middle and bottom rows
        row_indices = [i for i in range(0, resolution_y, skip_ah)]
        sums = []

        for row in row_indices:
            row_data = img_data[row, ::skip]
            row_sum = row_data.sum(axis=1)
            sums.append(row_sum)

        # Find the edges and calculate averages
        starts_ends = [find_edges(s, skip) for s in sums]
        for (start, end) in starts_ends:
            print(f"Start: {start}, End: {end}, Midpoint: {(start + end) / 2}")

        averages = [(start + end) / 2 for start, end in starts_ends]
        final_avg = np.average(averages,weights=weights.reverse())
        final = int(final_avg / 3.2)  # convert to proper scale

        ser.write((str(final) + '\n').encode())  # send it over UART
        print(final)
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Reset the stream position for the next capture
    stream.seek(0)
    stream.truncate()
