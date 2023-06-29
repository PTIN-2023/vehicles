import math, time, argparse, random
from djitellopy import Tello
from threading import Thread
# ---------------------------- #
import json
import paho.mqtt.client as mqtt
import requests
# ---------------------------- #
tello = Tello()
ID = 0
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

coordinates_normalized = [[0, 0], [1, 0], [1, 1]]

coordinates = None
dron_return = False
wait_client = False
user_confirmed = False
order_delivered = False
start_coordinates = False

time_wait_client = 10

# Initialize the battery level and the autonomy
autonomy = 500
battery_level = 100

# Saves current drone orientation (in degrees as int)
orientation = 0

# ------------------------------------------------------------------------------ #

def get_angle(x1, y1, x2, y2):
    
    global orientation

    dx = x2 - x1
    dy = y2 - y1
    
    dif_d = int(math.degrees(math.atan2(dy, dx)))
    dif_d -= orientation
    
    if dif_d > 180 or dif_d < -180:
        dif_d = dif_d%180

    orientation += dif_d

    print("orientation: %d", orientation)

    return dif_d

# Function to control the dron movement based on the angle
def move_dron(angle, distance, battery_level, autonomy):

    print("DRON FÍSIC: Sortint a un punt")
    
    tello.rotate_clockwise(angle)
    tello.move_forward(distance*100)

    # Calculate the battery usage based on the distance traveled
    battery_level = tello.get_battery()

    # Update the autonomy based on the distance traveled and the battery usage
    autonomy = (battery_level/100) * 8

    stats = "Nivell de bateria: %.2f | Autonomia en minuts: %.2f | " % (battery_level, autonomy)

    return battery_level, autonomy

def start_dron():

    global wait_client

    global orientation
    global autonomy
    global dron_return
    global battery_level

    # Get starting point
    x1, y1 = coordinates[0][0], coordinates[0][1]

    print("DRON FÍSIC: Connectant amb el dron...")
    tello.connect()

    print("DRON FÍSIC: Ready for takeoff. ")
    tello.takeoff()
    print("DRON FÍSIC: Iniciant ruta")
    tello.move_up(100)

    # Loop through each coordinate
    for i in range(1, len(coordinates)):

        # Get next point
        x2, y2 = coordinates_normalized[i][0], coordinates_normalized[i][1]

        # Calculate the distance between the current point and the next point
        distance = int(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))

        # Updates the current orientation to get the minimum degree value
        orientation = orientation%360

        # Calculate the angle between the current point and the next point
        angle = get_angle(x1, y1, x2, y2)

        # Control the dron movement based on the angle and update the battery level and the autonomy
        battery_level, autonomy = move_dron(angle, distance, battery_level, autonomy)

        # Send the dron position to Cloud
        send_location(ID, coordinates[0], 5 if dron_return else 3, battery_level, autonomy)

        # Update the current point
        x1, y1 = x2, y2

    print("DRON FÍSIC: S'ha arribat al final de la ruta.")
    # tello.move_down(tello.get_distance_tof())
    if dron_return:
        if orientation > 180:
            orientation = 360-orientation
        elif orientation < 180:
            orientation = -orientation

        tello.rotate_clockwise(orientation)
        orientation = 0
    tello.land()

    wait_client = True
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
            "status_num":       status,
            "status":           status_dron[status],
            "battery":          battery,
            "autonomy":         autonomy}

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)

    # Publish in "PTIN2023/DRON"
    clientS.publish("PTIN2023/VILANOVA/DRON/UPDATELOCATION", mensaje_json)

    # Close MQTT connection
    clientS.disconnect()

def update_status(id, status, temps):

    # Connect to MQTT server
    clientS.connect("147.83.159.195", 24183, 60)

    # JSON
    msg = {	"id_dron":      id,
            "status_num":   status,
            "status":       status_dron[status]}

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)

    # Publish in "PTIN2023/DRON"
    clientS.publish("PTIN2023/VILANOVA/DRON/UPDATESTATUS", mensaje_json)

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
    temps = int(time.time())
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
            update_status(ID, 1, temps)
            time.sleep(5)

            # En reparto
            update_status(ID, 3, temps)
            start_dron()

        time.sleep(0.25)

        if start_coordinates:

            if wait_client:

                # Esperando al cliente
                update_status(ID, 4, temps)

                waiting = 0
                init = time.time()
                while not user_confirmed and waiting < time_wait_client:
                    waiting = (time.time() - init)

	            # Atencio, el temps que espera el podem modificar
                if waiting >= time_wait_client:
                    update_status(ID, 5, temps)
                    order_delivered = False

                else:
                    if user_confirmed:
                        update_status(ID, 2, temps)
                        time.sleep(5)
                        order_delivered = True
                    else:
                        update_status(ID, 5, temps)
                        order_delivered = False

                wait_client = False
                dron_return = True

            elif dron_return:

                update_status(ID, 5, temps)
                start_dron()

                # En espera
                update_status(ID, 6, temps)
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
