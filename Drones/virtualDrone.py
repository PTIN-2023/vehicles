import math, time
from threading import Thread
# ---------------------------- #
import json
import paho.mqtt.client as mqtt


status_dron = {
    1: "carga - se encuentra en la colmena recogiendo el paquete.", 
    2: "descarga - llegada al destino (cliente)",
    3: "entrega - de camino hacia el cliente",
    4: "retorno - vuelve a la colmena", 
    5: "esperando recogida - esperando al cliente (QR)",
    6: "en espera - no hace nada (situado en colmena)",
    7: "en reparación - en taller por revisión o avería.",
    8: "alerta - posible avería de camino o cualquier situación anormal."
}

clientS = mqtt.Client()

ID = 1

coordinates = None
dron_return = False
wait_client = False
user_confirmed = True   # Nos lo mandan
order_delivered = False
start_coordinates = False

# Initialize the battery level and the autonomy
autonomy = 500
battery_level = 100

# ------------------------------------------------------------------------------ #

def get_angle(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.atan2(dy, dx)

# Function to control the dron movement based on the angle
def move_dron(angle, distance, battery_level, autonomy):
    
    # Calculate the distance traveled by the dron
    distance_traveled = math.sqrt(distance[0]**2 + distance[1]**2)

    # Calculate the battery usage based on the distance traveled
    battery_usage = distance_traveled / 0.025  # Assuming the dron uses 0.025 units of battery per meter
    
    # Update the battery level
    battery_level -= battery_usage

    # Update the autonomy based on the distance traveled and the battery usage
    autonomy -= distance_traveled / 100 * battery_level * 20

    stats = "Battery level: %.2f | Autonomy: %.2f | " % (battery_level, autonomy)

    # Send signal to the dron to move in the appropriate direction based on the angle
    if angle > math.pi/4 and angle < 3*math.pi/4:
        # Move forward
        print(stats + "Moving forward")
    
    elif angle > -3*math.pi/4 and angle < -math.pi/4:
        # Move backward
        print(stats + "Moving backward")
    
    elif angle >= 3*math.pi/4 or angle <= -3*math.pi/4:
        # Turn left
        print(stats + "Turning left")
    
    else:
        # Turn right
        print(stats + "Turning right")
    
    return battery_level, autonomy

def start_dron():
    
    global wait_client
    
    global autonomy
    global battery_level

    x1, y1 = coordinates[0][0], coordinates[0][1]

    # Loop through each coordinate
    for i in range(1, len(coordinates)):
        x2, y2 = coordinates[i][0], coordinates[i][1]

        # Calculate the distance between the current point and the next point
        distance = (x2 - x1, y2 - y1)

        # Calculate the angle between the current point and the next point
        angle = get_angle(x1, y1, x2, y2)

        # Control the dron movement based on the angle and update the battery level and the autonomy
        battery_level, autonomy = move_dron(angle, distance, battery_level, autonomy)

        # Send the dron position to Cloud
        send_location(ID, coordinates[i], 4 if dron_return else 3, battery_level, autonomy)

        # Update the current point
        x1, y1 = x2, y2

        # Add some delay to simulate the dron movement
        time.sleep(0.5)

    wait_client = not wait_client
    coordinates.reverse()

# ------------------------------------------------------------------------------ #

def send_location(id, location, status, battery, autonomy):

    # Connect to MQTT server
    clientS.connect("147.83.159.195", 24183, 60)

    # JSON
    msg = {	"id_dron": 	        id,
            "location_act": 	{
                "latitude":     location[0],
                "longitude":    location[1]
            },
            "status":	        status,
            "battery":          battery,
            "autonomy":         autonomy}

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)

    # Publish in "PTIN2023/DRON"
    clientS.publish("PTIN2023/DRON/UPDATELOCATION", mensaje_json)

    # Close MQTT connection
    clientS.disconnect()

def update_status(id, status):

    # Connect to MQTT server
    clientS.connect("147.83.159.195", 24183, 60)

    # JSON
    msg = {	"id_dron":   id,
            "status":   status }

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)

    # Publish in "PTIN2023/DRON"
    clientS.publish("PTIN2023/DRON/UPDATESTATUS", mensaje_json)

    print("DRON: " + str(id) + " | STATUS:  " + status_dron[status])

    # Close MQTT connection
    clientS.disconnect()

def update_status(id, status, statusorder):

    # Connect to MQTT server
    clientS.connect("147.83.159.195", 24183, 60)

    # JSON
    msg = {	"id_dron":      id,
            "status":       status,
            "statusorder":  statusorder }

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)

    # Publish in "PTIN2023/DRON"
    clientS.publish("PTIN2023/DRON/UPDATESTATUS", mensaje_json)

    print("DRON: " + str(id) + " | STATUS:  " + status_dron[status])

    # Close MQTT connection
    clientS.disconnect()

# ------------------------------------------------------------------------------ #

def is_json(data):
    try:
        json.loads(data)
        return True
    except json.decoder.JSONDecodeError:
        return False

def on_connect(client, userdata, flags, rc):

    if rc == 0:
        print("Edge connectat amb èxit. ")
    client.subscribe("PTIN2023/#")

def on_message(client, userdata, msg):
    
    if msg.topic == "PTIN2023/DRON/ORDER":	

        global ID
        global coordinates    
        if(is_json(msg.payload.decode('utf-8'))):
            
            payload = json.loads(msg.payload.decode('utf-8'))
            needed_keys = ["id_dron", "order", "route"]

            if all(key in payload for key in needed_keys):                
                if ID == payload[needed_keys[0]] and payload[needed_keys[1]] == 1:
                    coordinates = json.loads(payload[needed_keys[2]])['coordinates']
                    print("RECEIVED ROUTE: " + str(coordinates[0]) + " -> " + str(coordinates[-1]))
            else:
                print("FORMAT ERROR! --> PTIN2023/CAR/ORDER")        
        else:
            print("Message: " + msg.payload.decode('utf-8'))

def start():

    clientR = mqtt.Client()
    clientR.on_connect = on_connect
    clientR.on_message = on_message

    clientR.connect("147.83.159.195", 24183, 60)
    clientR.loop_forever()

# ------------------------------------------------------------------------------ #

def control():

    global dron_return
    global coordinates
    global wait_client
    global order_delivered
    global start_coordinates

    while True:
        
        if coordinates != None and not start_coordinates:
            start_coordinates = True

            # En proceso de carga ~ 5s
            update_status(ID, 1)
            time.sleep(5)

            # En reparto
            update_status(ID, 3)
            start_dron()

        time.sleep(0.25)

        if start_coordinates:
                            
            if wait_client:

                # Esperando al cliente
                update_status(ID, 5)
                time.sleep(10)

                if user_confirmed:   
                    # En proceso de descarga ~ 5s
                    update_status(ID, 2)
                    time.sleep(5)

                    order_delivered = False

                else:
                    order_delivered = False
                
                wait_client = not wait_client
                dron_return = not dron_return
                            
            elif dron_return:
                
                # Vuelta a a la colmena
                update_status(ID, 4)
                start_dron()

                # En espera
                update_status(ID, 6)
                start_coordinates = False

                coordinates = None
                dron_return = False
                wait_client = False
                order_delivered = False

if __name__ == '__main__':

    API = Thread(target=start)
    CTL = Thread(target=control)

    CTL.start()
    API.start()

    CTL.join()
    API.join()
