# import everything

# ---------------------------- #
import mfrc522
import RPi.GPIO as GPIO
# ---------------------------- #
from time import sleep
from threading import Thread
# ---------------------------- #
import json
import paho.mqtt.client as mqtt
# ------------------------------------------------------------------------------ #

status_car = {
    1 : "carga - se encuentra en el almacén cargando paquetes",
    2 : "descarga - se encuentra en la colmena descargando paquetes.", 
    3 : "entrega - camino hacia la colmena",
    4 : "retorno - vuelve al almacén",
    5 : "en espera - no hace nada.",
    6 : "en reparación - en taller por revisión o avería.",
    7 : "alerta - posible avería de camino o cualquier situación anormal."
}

clientS = mqtt.Client()

ID = 123456789
RFIDs = [
    [195, 226, 46, 149, 154],
    [38,  60, 249,  41, 202], 
    [67, 107, 155, 148, 39]
]

UID = [0, 0, 0, 0, 0]
UIDant = [0, 0, 0, 0, 0]

route = None
car_return = False
start_route = False
RFID_location = None



EN = [7, 33]
IN = [11, 13, 29, 31]

# ------------------------------------------------------------------------------ #

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

    PA.start(25)
    PB.start(25)

    if direction > 0:
        GPIO.output(IN[0],GPIO.HIGH)
        GPIO.output(IN[1],GPIO.LOW)

        GPIO.output(IN[2],GPIO.HIGH)
        GPIO.output(IN[3],GPIO.LOW)
    else:
        GPIO.output(IN[0],GPIO.LOW)
        GPIO.output(IN[1],GPIO.HIGH)

        GPIO.output(IN[2],GPIO.LOW)
        GPIO.output(IN[3],GPIO.HIGH)

def stopCar():

    global IN

    GPIO.output(IN[0],GPIO.LOW)
    GPIO.output(IN[1],GPIO.LOW)

    GPIO.output(IN[2],GPIO.LOW)
    GPIO.output(IN[3],GPIO.LOW)

# ------------------------------------------------------------------------------ #

def scan():
        
    global UID
    global start_route
    continue_reading = True

    # Disable warining
    GPIO.setwarnings(False)
    
    # Create an object of the class MFRC522
    lectorRFID = mfrc522.MFRC522()

    # Welcome message
    print ("RFID | TransMED - PTIN 2023")

    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    while continue_reading:

        # Scan for cards    
        status, TagType = lectorRFID.MFRC522_Request(lectorRFID.PICC_REQIDL)

        # Get the UID of the card
        status, uid = lectorRFID.MFRC522_Anticoll()

        # If we have the UID, continue
        if status == lectorRFID.MI_OK and start_route:
            UID = [uid[0], uid[1], uid[2], uid[3], uid[4]]

# ------------------------------------------------------------------------------ #

def send_location(id, location, status = 3, battery = 100, autonomy = 3600):

    # Connect to MQTT server
    clientS.connect("test.mosquitto.org", 1883, 60)

    # JSON
    msg = {	"id_car": 	        id,
            "location_act": 	{
                "latitude":     location[0],
                "longitude":    location[1]
            },
            "status":	        status,
            "battery":          battery,
            "autonomy":         autonomy}

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)

    # Publish in "PTIN2023/A1/CAR"
    clientS.publish("PTIN2023/A1/CAR/UPDATELOCATION", mensaje_json)

    print("SENDED | Car:" + str(id) + " at " + str(location))

    # Close MQTT connection
    clientS.disconnect()

def update_status(id, status):

    # Connect to MQTT server
    clientS.connect("test.mosquitto.org", 1883, 60)

    # JSON
    msg = {	"id_car":   id,
            "status":   status }

    # Code the JSON message as a string
    mensaje_json = json.dumps(msg)

    # Publish in "PTIN2023/A1/CAR"
    clientS.publish("PTIN2023/A1/CAR/UPDATESTATUS", mensaje_json)

    print("SENDED | Car: " + str(id) + " | Status:  " + status_car[status])

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
    print("Cloud connectat amb codi " + str(rc))
    client.subscribe("PTIN2023/#")

def on_message(client, userdata, msg):
    
    if msg.topic == "PTIN2023/A1/CAR/ORDER":	

        global ID
        global route    
        if(is_json(msg.payload.decode('utf-8'))):
            
            payload = json.loads(msg.payload.decode('utf-8'))
            needed_keys = ["id_car", "order", "route"]

            if all(key in payload for key in needed_keys):                
                if ID == payload[needed_keys[0]] and payload[needed_keys[1]] == 1:
                    route = json.loads(payload[needed_keys[2]])['coordinates']
            else:
                print("FORMAT ERROR! --> PTIN2023/A1/CAR/ORDER")        
        else:
            print("Message: " + msg.payload.decode('utf-8'))

def start():

    clientR = mqtt.Client()
    clientR.on_connect = on_connect
    clientR.on_message = on_message

    clientR.connect("test.mosquitto.org", 1883, 60)
    clientR.loop_forever()

# ------------------------------------------------------------------------------ #

def control():

    global UID
    global UIDant
    
    global route
    global car_return
    global start_route
    global RFID_location
    
    while True:

        if route != None and not start_route:
            start_route = True
            RFID_location = list(zip(RFIDs, route))

            # En proceso de carga ~ 10s
            update_status(ID, 1)
            sleep(10)

            # En reparto
            startCar(1)

        sleep(0.25)

        if start_route and UID != UIDant:
            UIDant = UID
            location = [location[1] for location in RFID_location if location[0] == UID][0]
            
            send_location(ID, location)
            if UID == RFIDs[-1]:
                stopCar()
                
                if not car_return:
                    # En proceso de descarga ~ 10s
                    update_status(ID, 2)
                    sleep(10)

                    # Vuelta al almacén
                    update_status(ID, 4)
                    startCar(-1)
                    
                    RFIDs.reverse()
                    car_return = True
                    UIDant = [0, 0, 0, 0, 0]
                
                else:
                    # En espera
                    update_status(ID, 5)
                    start_route = False
                    RFIDs.reverse()
                    route = None


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
