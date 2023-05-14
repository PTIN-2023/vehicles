import math
import time
# import json

# Function to calculate the angle between two points
def get_angle(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.atan2(dy, dx)

# Function to control the car movement based on the angle
def move_car(angle):
    # Send signal to the car to move in the appropriate direction based on the angle
    if angle > math.pi/4 and angle < 3*math.pi/4:
        # Move forward
        print("Moving forward")
    elif angle > -3*math.pi/4 and angle < -math.pi/4:
        # Move backward
        print("Moving backward")
    elif angle >= 3*math.pi/4 or angle <= -3*math.pi/4:
        # Turn left
        print("Turning left")
    else:
        # Turn right
        print("Turning right")

# Sample JSON data
# json_data = '{"coordinates":[[1.729895,41.220972],[1.730095,41.220594],[1.730957,41.220821],[1.730341,41.222103],[1.732058,41.222625],[1.732593,41.222967],[1.732913,41.223435],[1.733119,41.224977],[1.733229,41.225046],[1.733257,41.225324],[1.733531,41.225684],[1.73421,41.226188],[1.737807,41.22931],[1.738258,41.229572],[1.738483,41.229682],[1.738329,41.229879],[1.738106,41.229798],[1.738094,41.22967],[1.737657,41.22918],[1.737265,41.228995],[1.736156,41.228027],[1.735887,41.227883],[1.735424,41.228285]],"type":"LineString"}'

# Parse JSON data
#data = json.loads(json_data)

# Sample string data
coordinates_str = "[[1.729895,41.220972],[1.730095,41.220594],[1.730957,41.220821],[1.730341,41.222103],[1.732058,41.222625],[1.732593,41.222967],[1.732913,41.223435],[1.733119,41.224977],[1.733229,41.225046],[1.733257,41.225324],[1.733531,41.225684],[1.73421,41.226188],[1.737807,41.22931],[1.738258,41.229572],[1.738483,41.229682],[1.738329,41.229879],[1.738106,41.229798],[1.738094,41.22967],[1.737657,41.22918],[1.737265,41.228995],[1.736156,41.228027],[1.735887,41.227883],[1.735424,41.228285]]"

# Convert string data to a list of coordinates
coordinates = eval(coordinates_str)

# Extract the latitude and longitude values from the coordinates array
#coordinates = data['coordinates']
x1, y1 = coordinates[0][0], coordinates[0][1]

# Loop through each coordinate
for i in range(1, len(coordinates)):
    x2, y2 = coordinates[i][0], coordinates[i][1]

    # Calculate the angle between the current point and the next point
    angle = get_angle(x1, y1, x2, y2)

    # Control the car movement based on the angle
    move_car(angle)

    # Update the current point
    x1, y1 = x2, y2

    # Add some delay to simulate the car movement
    time.sleep(1)
