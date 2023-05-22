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
mensaje = {	"id_car": 123456789, 
	   	"pos_act_x": 8.432412321,
	   	"pos_act_y": -1.321312313,
	   	"batery": 60,
	   	"autonomy": 152,
	   	"state": "ESTACIONADO",
		"exp": int(time.time()) + 60*5,
		"iss": "A1"
		}
	   	
	   	
#id_car, pos_ini, pos_final, pos_act, batery, autonomy, state{CARGANDO, DESCARGANDO, ESTACIONADO, REPARTIENDO, ALERTA}
with open('sec.priv', 'r') as file:
	secret = file.read()
	file.close()

# Codifica el mensaje JSON a una cadena
token = jwt.encode(mensaje, secret, algorithm='HS256')

# Publica el mensaje en el topic "PTIN2023/A1/CAR"
client.publish("PTIN2023/A1/CAR/UPDATEPOSITION", token)

# Cierra la conexión MQTT
client.disconnect()
