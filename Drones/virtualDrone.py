import math, time
from threading import Thread
# ---------------------------- #
import json
import paho.mqtt.client as mqtt
import requests

status_dron = {
    1: "loading",
    2: "unloading",
    3: "delivering",
	4: "awaiting",
	5: "returning",
   	6: "waits",
	7: "repairing",
	8: "alert"
}

status_desc = {
    1: "loading - es troba en la colmena agafant el paquet.",
    2: "unloading - arribada al destí (client).",
    3: "delivering - camí cap al client.",
	4: "awaiting - esperant al client (QR).",
	5: "returning - tornada a la colmena.",
   	6: "waits - no fa res (situat en colmena)",
	7: "repairing - en taller per revisió o avaria.",
	8: "alert- possible avaria de camí o qualsevol situació anormal."
}

clientS = mqtt.Client()

ID = 1

coordinates = None
dron_return = False
wait_client = False
user_confirmed = False   # Nos lo mandan
order_delivered = False
start_coordinates = False

time_wait_client = 50 # secons

# API per el temps que fa
api_key = "preguntar pel grup"
base_url = "http://api.openweathermap.org/data/2.5/weather?"
complete_url = base_url + "appid=" + api_key + "&units=metric"

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
        send_location(ID, coordinates[i], 5 if dron_return else 3, battery_level, autonomy)

        # Update the current point
        x1, y1 = x2, y2

        # Add some delay to simulate the dron movement
        time.sleep(1)

    wait_client = True
    coordinates.reverse()

# ------------------------------------------------------------------------------ #

def send_location(id, location, status, battery, autonomy):

    # Connect to MQTT server
    clientS.connect("147.83.159.195", 24183, 60)

    # Anomalia bateria
    if battery <= 5:
        print("CRÍTIC: Nivell de bateria crític (%d). Retornant dron a la colmena..." % battery)
        status=5
    elif battery <= 10:
        print("ATENCIÓ: Nivell de bateria baix (%d)" % battery)

    # Anomalia temps
    # Posem factor Random perque no fagi calls a la api cada dos per tres
    if(bool(randint(0,9))):
        url = complete_url + "&lat=" + location[0] + "&lon=" + location[1]
        response = requests.get(url)
        x = response.json()
        if x["cod"] != "404":   
            y = x["main"]
            temperatura = y["temp"]
            full = x["weather"]
            condicio = full[0]["main"]
            if condicio == "rain" or condicio == "storm" or temperatura > 35 or temperatura < 5:
                print("ALERTA: Condicions atmosferiques adverses.") 
                print("Temperatura: %d" % (temperatura))
                print("Condicions: %s" % (condicions))
                print("Dron en espera.")
                status=6
        else:
            print("Avís: Hi ha hagut un error en la connexió amb l'API del temps.")

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

def update_status(id, status, temps):

    # Connect to MQTT server
    clientS.connect("147.83.159.195", 24183, 60)

    # Anomalia fallo tecnic
    segons_anomalia = 100
    fallos_tecnics=["El dron ha explotat", "Motor averiat", "Ala trencada", "Sensor averiat", "S'ha perdut la comunicació"]
    # Si es supera el temps de anomalia i (opcional) el factor aleatori 1/10
    if int(time.time()) - temps > segons_anomalia and not bool(randint(0,9)):
        print("CRÍTIC: Hi ha hagut un error tècnic amb el dron de ID %d, missatge d'error: '%s'" % id, fallos_tecnics[randint(0,4)]) 
        print("    Es requereix asistència per retirar el dron de l'útima posició enregistrada.")
        status=8

    # Anomalia obstacle
    segons_anomalia = 50
    # Si es supera el temps de anomalia i (opcional) el factor aleatori 1/10
    if int(time.time()) - temps > segons_anomalia:
        print("ATENCIÓ: Obstacle imprevist a la ruta. Redirigint...") 
        status=8

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
    
    #anomalia pedido cancelado
    elif msg.topic == "PTIN2023/DRON/CANCELDELIVERY":
        if(is_json(msg.payload.decode('utf-8'))):

            payload = json.loads(msg.payload.decode('utf-8'))
            needed_keys = ["id_dron"]
            
            if all(key in payload for key in needed_keys):                
                if ID == payload[needed_keys[0]]:
                    wait_client = False
                    dron_return = True
                    print("USER RECEIVE CANCELED!")
            else:
                print("FORMAT ERROR! --> PTIN2023/DRON/CANCELDELIVERY")
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
                if waiting > time_wait_client:
                # Anomalia: usuari no recull el paquet a temps
                    update_status(ID, 5, temps)
                    # Es podria posar anomalia nova de tornant a colemna amb error
                    order_delivered = False
                    print("Error: Temps d'espera per recollir el paquet esgotat. Retornant a la colmena...")
                else:

                    if user_confirmed:   
                        # En proceso de descarga ~ 5s
                        update_status(ID, 2, temps)
                        time.sleep(5)

                        order_delivered = True
                    else:
                        # Anomalia: usuari no autoritzat pel paquet
                        update_status(ID, 5, temps)
                        # Es podria posar anomalia nova de tornant a colemna amb error
                        order_delivered = False
                        print("Error: Usuari que ha intentat recollir el paquet no està autroitzat. Retornant a la colmena...")
                
                wait_client = False
                dron_return = True

            elif dron_return:
                
                # Vuelta a a la colmena
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
