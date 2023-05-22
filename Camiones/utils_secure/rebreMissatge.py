import paho.mqtt.client as mqtt
import json
import pyjwt
import time

codi_client = 7777

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
    
    if msg.topic == "PTIN2023/A1/CAR/STATUS":	
        with open('sec.priv', 'r') as file:
            secret = file.read()
            file.close()
        try:
            payload = msg.payload.decode(token, secret, algorithms=['HS256'])
            
            if payload["exp"] < time.time():
                print("Token expirat.")
            else:
                print(payload)
        except jwt.exceptions.InvalidTokenError:
            print('Invalid token')

        needed_keys = ['idVehicle', 'estatVehicle']

        if all(key in payload for key in needed_keys):                
            print("Vehicle: " + str(payload["idVehicle"]) + " | Estat: " + str(payload["estatVehicle"]))
            print("---------------------------------------") 
        else:
            print("ERROR FORMAT! --> PTIN2023/A1/CAR/STATUS")        
        
            
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("test.mosquitto.org", 1883 , 60)
client.loop_forever()
