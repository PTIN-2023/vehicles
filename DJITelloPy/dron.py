import math, time, argparse
from djitellopy import Tello
from threading import Thread
# ---------------------------- #
import json
import paho.mqtt.client as mqtt
# ---------------------------- #

parser = argparse.ArgumentParser()
parser.add_argument('--id', dest = 'id', help = 'DRON ID')
args = parser.parse_args()

ID = int(args.id)

# ------------------------------------------------------------------------------ #

status_dron = {
    1: "loading",
    2: "unloading",
    3: "delivering",
	4: "awaiting",
	5: "returning",
   	6: "waits",
	7: "repairing",
	8: "alert",
    9: "delivered",
    10: "not delivered"
}

status_desc = {
    1: "loading - es troba en la colmena agafant el paquet.",
    2: "unloading - arribada al destí (client).",
    3: "delivering - camí cap al client.",
	4: "awaiting - esperant al client (QR).",
	5: "returning - tornada a la colmena.",
   	6: "waits - no fa res (situat en colmena)",
	7: "repairing - en taller per revisió o avaria.",
	8: "alert- possible avaria de camí o qualsevol situació anormal.",
    9: "delivered - el client ha rebut el paquet",
    10: "not delivered - el client no ha rebut el paquet" 
}

clientS = mqtt.Client()

coordinates = None
dron_return = False
wait_client = False
user_confirmed = False   # Nos lo mandan
order_delivered = False
start_coordinates = False

time_wait_client = 180 # seconds

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
    global dron_return
    global battery_level

    # https://djitellopy.readthedocs.io/en/latest/tello/
    # Moves -> cm, rotate -> Grados 
    tello = Tello()

    print("DRON FÍSIC: Connectant amb el dron...")
    tello.connect()
    print("DRON FÍSIC: Ready for takeoff. ")
    tello.takeoff()

    print("DRON FÍSIC: Iniciant ruta de prova")
    tello.move_forward(200)
    time.sleep(2)
    tello.rotate_clockwise(180)
    tello.move_forward(200)

    print("DRON FÍSIC: Aterritzant")
    tello.land()

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
            "status_num":       status,
            "status":           status_dron[status],
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
    msg = {	"id_dron":      id,
            "status_num":   status,
            "status":       status_dron[status]}

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)

    # Publish in "PTIN2023/DRON"
    clientS.publish("PTIN2023/DRON/UPDATESTATUS", mensaje_json)

    print("DRON: " + str(id) + " | STATUS:  " + status_desc[status])

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
    
    global ID
    
    if msg.topic == "PTIN2023/DRON/STARTROUTE":	

        global coordinates    
        if(is_json(msg.payload.decode('utf-8'))):
            
            payload = json.loads(msg.payload.decode('utf-8'))
            needed_keys = ["id_dron", "order", "route"]

            if all(key in payload for key in needed_keys):                
                if ID == payload[needed_keys[0]] and payload[needed_keys[1]] == 1:
                    coordinates = json.loads(payload[needed_keys[2]])
                    print("RECEIVED ROUTE: " + str(coordinates[0]) + " -> " + str(coordinates[-1]))
            else:
                print("FORMAT ERROR! --> PTIN2023/DRON/STARTROUTE")        
        else:
            print("Message: " + msg.payload.decode('utf-8'))

    elif msg.topic == "PTIN2023/DRON/CONFIRMDELIVERY":

        global user_confirmed
        if(is_json(msg.payload.decode('utf-8'))):

            payload = json.loads(msg.payload.decode('utf-8'))
            needed_keys = ["id_dron", "status"]
            
            if all(key in payload for key in needed_keys):                
                if ID == payload[needed_keys[0]]:
                    user_confirmed = (payload[needed_keys[1]] == 1)
                    print("USER RECEIVE CONFIRMED!", user_confirmed)
            else:
                print("FORMAT ERROR! --> PTIN2023/DRON/CONFIRMDELIVERY") 

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
    global user_confirmed
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
                update_status(ID, 4)
                
                waiting = 0
                init = time.time()
                while not user_confirmed and waiting < time_wait_client:
                    waiting = (time.time() - init)
                
                if user_confirmed:
                    # En proceso de descarga ~ 5s
                    update_status(ID, 2)
                    time.sleep(10)
                
                    update_status(ID, 9)
                    time.sleep(5)
                    order_delivered = True
                else:
                    order_delivered = False
                    update_status(ID, 10)
                
                wait_client = False
                dron_return = True

            elif dron_return:
                
                # Vuelta a a la colmena
                update_status(ID, 5)
                start_dron()

                # En espera
                update_status(ID, 6)
                start_coordinates = False

                coordinates = None
                dron_return = False
                wait_client = False
                user_confirmed = False
                order_delivered = False

if __name__ == '__main__':

    API = Thread(target=start)
    CTL = Thread(target=control)

    CTL.start()
    API.start()

    CTL.join()
    API.join()
