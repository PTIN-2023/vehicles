import paho.mqtt.client as mqtt
import json
import jwt
import pyjwt
import time

# Crea un objeto cliente MQTT
client = mqtt.Client()

# Conecta al servidor MQTT
client.connect("test.mosquitto.org", 1883, 60)

# Crea un mensaje JSON
mensaje = {	"idVehicle": 123456789, 
	   	"estatVehicle": "START",
		"exp": int(time.time()) + 60*5,
		"iss": "A1"
	   }

# Codifica el mensaje JSON a una cadena
with open('sec.priv', 'r') as file:
	secret = file.read()
	file.close()

# Codifica el mensaje JSON a una cadena
token = jwt.encode(mensaje, secret, algorithm='HS256')

# Publica el mensaje en el topic "PTIN2023/A1/CAR"
client.publish("PTIN2023/A1/CAR/STATUS", token)

# Cierra la conexión MQTT
client.disconnect()
