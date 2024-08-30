# # CODE FOR RASBERRY PI ZERO W TO CAPTURE IMAGES AND DO IMAGE PROCESSING 
# # COMMUNICATES VIA UART TO RASPI PICO FOR MOTOR CONTROL

# Import necessary libraries
import cv2
import serial
import os

# Initialize the serial port, baud rate, timeout
ser = serial.Serial(port='/dev/ttyS0', baudrate=115200, timeout=1)

# Create a directory for saving images, if it doesn't exist
output_dir = "/home/alazartegegnework/captured_images_2"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Initialize counter variable
image_count = 0

# Define image crop dimensions (full width, cropped height)
x = 640
y = 100

# Initialize OpenCV video capture
capture = cv2.VideoCapture(0)

# Set image buffer to 1 so that it analyzes the most up to date photo
capture.set(cv2.CAP_PROP_BUFFERSIZE, 1) 

# Check video stream is open
if not capture.isOpened():
    print("Error: Could not open video capture")
    exit()

# Infinite loop during operation
while True:
    
    # Get the image
    ret, image = capture.read()

    # Check for failure to get image
    if not ret:
        print("Failed to capture image")
        continue

    # Save initial image
    file_name = os.path.join(output_dir, f"before_{image_count:04d}.jpg")
    cv2.imwrite(file_name, image)

    # Crop the region of interest
    img = image[190:290, 0:640]

    # Save cropped image
    img_name = os.path.join(output_dir, f"img_{image_count:04d}.jpg")
    cv2.imwrite(img_name, img)

    # OpenCV: grayscale the image
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Save grayscale image (https://www.geeksforgeeks.org/python-grayscaling-of-images-using-opencv/)
    gray_name = os.path.join(output_dir, f"gray_{image_count:04d}.jpg")
    cv2.imwrite(gray_name, gray_image)

    # OpenCV: Use Gaussian Blur on image (https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html)
    img_blur = cv2.GaussianBlur(gray_image,(3,3), 0)

    # Save blurred image
    blur_name = os.path.join(output_dir, f"blur_{image_count:04d}.jpg")
    cv2.imwrite(blur_name, img_blur)

    # OpenCV: Use thresholding (https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html)
    _, binary = cv2.threshold(img_blur, 125, 200, cv2.THRESH_BINARY)
    
    # Save thresholded image
    thresh_name = os.path.join(output_dir, f"binary_{image_count:04d}.jpg")
    cv2.imwrite(thresh_name, binary)

    # OpenCV: Use countour finding (https://docs.opencv.org/3.4/d4/d73/tutorial_py_contours_begin.html)
    contours, contours_image = cv2.findContours(binary, 1, cv2.CHAIN_APPROX_NONE)

    # If contours were found
    if contours:

        # Find the largest contour because its the line
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate moments of the largest contour
        M = cv2.moments(largest_contour)
        
        # Calculate the x, y coordinates of the center
        if M['m00'] != 0.0:
            center = int(M['m10'] / M['m00'])
    
    # Pass the center of the line to the Pico via UART
    ser.write((str(center) + '\n').encode())

    # Print to screen
    print("Final Average:", (center))

    # Increment counter
    image_count += 1