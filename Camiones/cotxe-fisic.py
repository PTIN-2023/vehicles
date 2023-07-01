import mfrc522
import RPi.GPIO as GPIO
import time
from threading import Thread
import json
import paho.mqtt.client as mqtt

status_car = {
    1 : "loading",
    2 : "unloading",
    3 : "delivering",
    4 : "returning",
    5 : "waits",
    6 : "repairing",
    7 : "alert"
}

status_desc = {
    1 : "loading - se encuentra en el almacén cargando paquetes.",
    2 : "unloading - es troba en la colmena descarregant.",
    3 : "delivering - camí cap a la colmena.",
    4 : "returning - tornada al magatzem.",
    5 : "waits - no fa res.",
    6 : "repairing - en taller per revisió o avaria.",
    7 : "alert - possible avaria de camí o qualsevol situació anormal."
}

clientS = mqtt.Client()

ID = 0
status = 5
UID = [0, 0, 0, 0, 0]
UIDant = [0, 0, 0, 0, 0]

coordinates = None
start_coordinates = False
RFIDs = [
    [195, 226, 46, 149, 154],
    [38,  60, 249,  41, 202],
    [166, 51, 127, 165, 79],
    [67, 107, 155, 148, 39]
]

# Initialize the battery level and the autonomy
autonomy = 2000
battery_level = 100

EN = [7, 33]
IN = [11, 13, 29, 31]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(EN[0], GPIO.OUT)
GPIO.setup(EN[1], GPIO.OUT)

GPIO.setup(IN[0],GPIO.OUT)
GPIO.setup(IN[1],GPIO.OUT)
GPIO.setup(IN[2],GPIO.OUT)
GPIO.setup(IN[3],GPIO.OUT)

PA = GPIO.PWM(EN[0], 100)
PB = GPIO.PWM(EN[1], 100)

GPIO.output(IN[0],GPIO.LOW)
GPIO.output(IN[1],GPIO.LOW)
GPIO.output(IN[2],GPIO.LOW)
GPIO.output(IN[3],GPIO.LOW)

def startCar(direction):

    global PA
    global PB
    global IN

    PA.start(35)
    PB.start(35)

    if direction > 0:
        print("MOVING FORWARD")
        GPIO.output(IN[0],GPIO.HIGH)
        GPIO.output(IN[1],GPIO.LOW)
        GPIO.output(IN[2],GPIO.HIGH)
        GPIO.output(IN[3],GPIO.LOW)
    else:
        print("MOVING BACKWARDS")
        GPIO.output(IN[0],GPIO.LOW)
        GPIO.output(IN[1],GPIO.HIGH)
        GPIO.output(IN[2],GPIO.LOW)
        GPIO.output(IN[3],GPIO.HIGH)

def stopCar():

    global IN

    print("STOP")

    GPIO.output(IN[0],GPIO.LOW)
    GPIO.output(IN[1],GPIO.LOW)
    GPIO.output(IN[2],GPIO.LOW)
    GPIO.output(IN[3],GPIO.LOW)

def scan():

    global UID
    global start_coordinates

    # Disable warining
    GPIO.setwarnings(False)
    # Create an object of the class MFRC522
    lectorRFID = mfrc522.MFRC522()

    # Welcome message
    print ("RFID | TransMED - PTIN 2023")

    continue_reading = True
    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    while continue_reading:
        # Scan for cards    
        status, TagType = lectorRFID.MFRC522_Request(lectorRFID.PICC_REQIDL)
        # Get the UID of the card
        status, uid = lectorRFID.MFRC522_Anticoll()
        # If we have the UID, continue
        if status == lectorRFID.MI_OK:
            if start_coordinates:
                UID = [uid[0], uid[1], uid[2], uid[3], uid[4]]

                #print("UID SCANNED AND IN ROUTE: ", UID)

           # else:

                #print("UID SCANNED AND NOT IN ROUTE: ", uid)


def send_location(id, location, status, battery, autonomy):

    # Connect to MQTT server
    clientS.connect("147.83.159.195", 24183, 60)
    # JSON
    msg = {"id_car": id,
           "location_act": {
               "latitude": location[0],
               "longitude": location[1]
           },
           "status_num": status,
           "status": status_car[status],
           "battery": battery,
           "autonomy": autonomy}

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)
    # Publish in "PTIN2023/A1/CAR"
    clientS.publish("PTIN2023/CAR/UPDATELOCATION", mensaje_json)

    print("SENDED LOCATION")
    print(msg)

    # Close MQTT connection
    clientS.disconnect()

def update_status(id, status):

    # Connect to MQTT server
    clientS.connect("147.83.159.195", 24183, 60)
    # JSON
    msg = {	"id_car":       id,
            "status_num":   status,
            "status":       status_car[status] }
    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)
    # Publish in "PTIN2023/A1/CAR"
    clientS.publish("PTIN2023/CAR/UPDATESTATUS", mensaje_json)

    print("SENDED STATUS:")
    print(msg)

    # Close MQTT connection
    clientS.disconnect()

def is_json(data):

    try:
        json.loads(data)
        return True
    except json.decoder.JSONDecodeError:
        return False

def on_connect(client, userdata, flags, rc):

    if rc == 0:
        print("Cloud connectat amb èxit. ")
    client.subscribe("PTIN2023/#")

def on_message(client, userdata, msg):

    global ID
    global coordinates
    
    if msg.topic == "PTIN2023/CAR/STARTROUTE":
        if (is_json(msg.payload.decode('utf-8'))):
            payload = json.loads(msg.payload.decode('utf-8'))
            needed_keys = ["id_car", "order", "route"]
            if all(key in payload for key in needed_keys):
                if ID == payload[needed_keys[0]] and payload[needed_keys[1]] == 1:
                    coordinates = json.loads(payload[needed_keys[2]])

                    print("RECEIVED ROUTE: " + str(coordinates[0]) + " -> " + str(coordinates[-1]))

                    coordinatesroute = [coordinates[0], coordinates[int(len(coordinates) / 3)], coordinates[int(len(coordinates) / 1.5)], coordinates[len(coordinates) - 1]]
                    coordinates = coordinatesroute

                    print("EFECTIVE ROUTE: ")
                    for x in coordinates:
                        print(" -" + str(x))

            else:
                print("FORMAT ERROR! --> PTIN2023/CAR/STARTROUTE")
        else:
            print("Message: " + msg.payload.decode('utf-8'))

def start():

    clientR = mqtt.Client()
    clientR.on_connect = on_connect
    clientR.on_message = on_message
    clientR.connect("147.83.159.195", 24183, 60)
    clientR.loop_forever()

def control(false=None):

    global UID
    global UIDant
    global coordinates
    global start_coordinates
    global status
    global battery_level
    global autonomy
    
    returning = False
    while True:

        # Si tienes ruta pero no has empezado empiezas
        if coordinates != None and not start_coordinates:
            autonomy = 2000
            battery_level = 100
            start_coordinates = True

            # En proceso de carga ~ 15s
            status = 1
            update_status(ID, 1)
            time.sleep(15)

            # En reparto
            status = 3
            update_status(ID, 3)
            startCar(1)
            returning = False

        if start_coordinates and UID != UIDant:
            UIDant = UID
            autonomy = autonomy - 200
            battery_level = battery_level - 10
            num = RFIDs.index(UID)

            print("UID SCANNED POSITION:" + str(num))

            location = coordinates[num]

            print("RELATIONAL COORDINATE: ")
            print(location)

            send_location(ID, location, status, battery_level, autonomy)

            if num == len(RFIDs)-1:
                stopCar()
                status = 2
                # En proceso de descarga ~ 15s
                update_status(ID, 2)
                autonomy = 2000
                battery_level = 100
                time.sleep(15)

                # Vuelta al almacén
                status = 4
                update_status(ID, 4)
                startCar(-1)
                returning = True

            if num == 0 and returning == True:
                stopCar()
                # En espera
                status = 5
                update_status(ID, 5)
                start_coordinates = False
                coordinates = None
                UIDant = [0, 0, 0, 0, 0]
                UID = [0, 0, 0, 0, 0]
                autonomy = 2000
                battery_level = 100
                returning = False

        time.sleep(0.25)


if __name__ == '__main__':

    GPS = Thread(target=scan)
    API = Thread(target=start)
    CTL = Thread(target=control)

    CTL.start()
    API.start()
    GPS.start()

    CTL.join()
    API.join()
    GPS.join()