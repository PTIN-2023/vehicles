import math, time, argparse, random
from djitellopy import Tello
from threading import Thread
# ---------------------------- #
import json
import paho.mqtt.client as mqtt
import requests
# ---------------------------- #
tello = Tello()

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

# API per el temps que fa
api_key = "Secret"
base_url = "http://api.openweathermap.org/data/2.5/weather?"
complete_url = base_url + "appid=" + api_key + "&units=metric"

# Initialize the battery level and the autonomy
autonomy = 500
battery_level = 100

# ------------------------------------------------------------------------------ #

def get_angle(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return int(math.degrees(math.atan2(dy, dx)))

# Function to control the dron movement based on the angle
def move_dron(angle, distance, battery_level, autonomy):

    print("DRON FÍSIC: Connectant amb el dron...")
    tello.connect()

    print("DRON FÍSIC: Ready for takeoff. ")
    # OJITO: Potser s'ha de posar tello.takeoff() perque funcuini al principi
    tello.takeoff()
    tello.move_up(50)

    print("DRON FÍSIC: Iniciant ruta")
    tello.rotate_clockwise(angle)
    tello.move_forward(distance*100)
    # Multiplica * 100 perque estava en metres

    print("DRON FÍSIC: S'ha arribat al final de la ruta. Aterritzant i esperant al client per escanejar...")
    # tello.move_down(tello.get_distance_tof())
    tello.land()

    # Això es un placeholder, cal programar el que es llegeixi el qr i torni
    qr_escanejat = False
    while not qr_escanejat:
        if not bool(random.randint(0,999)):
            qr_escanejat = True
            print("DRON FÍSIC: QR escanejat. Retornant a base...")

    tello.takeoff()
    tello.move_up(50)
    tello.rotate_clockwise(180)
    tello.move_forward(int(distance)*100)

    print("DRON FÍSIC: Aterritzant a base")
    # tello.move_down(50)
    tello.land()


    # Calculate the battery usage based on the distance traveled
    battery_level = tello.get_battery()

    # Update the autonomy based on the distance traveled and the battery usage
    autonomy = (battery_level/100) * 8

    stats = "Nivell de bateria: %.2f | Autonomia en minuts: %.2f | " % (battery_level, autonomy)

    return battery_level, autonomy

def start_dron():

    global wait_client

    global autonomy
    global dron_return
    global battery_level

    #Obtenir coordenades inici i final (nomes hi ha aquestes dos)
    x1, y1 = coordinates[0][0], coordinates[0][1]

    x2, y2 = coordinates[len(coordinates[0])-1][0], coordinates[len(coordinates[0])-1][1]

    # Calculate the distance between the current point and the next point
    distance = int(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))

    # Calculate the angle between the current point and the next point
    angle = get_angle(x1, y1, x2, y2)

    # Control the dron movement based on the angle and update the battery level and the autonomy
    battery_level, autonomy = move_dron(angle, distance, battery_level, autonomy)

    # Send the dron position to Cloud
    send_location(ID, coordinates[0], 5 if dron_return else 3, battery_level, autonomy)

    # Update the current point
    x1, y1 = x2, y2

    wait_client = True
    coordinates.reverse()

"""
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
"""

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
    if(bool(random.randint(0,9))):
        url = complete_url + "&lat=" + str(location[0]) + "&lon=" + str(location[1])
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
    if int(time.time()) - temps > segons_anomalia and not bool(random.randint(0,9)):
        print("CRÍTIC: Hi ha hagut un error tècnic amb el dron de ID %d, missatge d'error: '%s'" % id, fallos_tecnics[random.randint(0,4)])
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
