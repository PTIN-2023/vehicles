import paho.mqtt.client as mqtt
import json

# Crea un objeto cliente MQTT
client = mqtt.Client()

# Conecta al servidor MQTT
client.connect("147.83.159.195", 24183, 60)

# Crea un mensaje JSON
mensaje = {	"id_dron": 	1,
        	"order": 	1,
            "route":	0}

# recibido de mapas
route = {"coordinates" : "[[0, 0], [2, 0]]",
         "type": "LineString"}

mensaje["route"] = route["coordinates"]

# Codifica el mensaje JSON a una cadena
mensaje_json = json.dumps(mensaje)

# Publica el mensaje en el topic "PTIN2023/A1/CAR"
client.publish("PTIN2023/DRON/STARTROUTE", mensaje_json)

# Cierra la conexión MQTT
client.disconnect()
