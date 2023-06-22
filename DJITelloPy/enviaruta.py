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
route = {"coordinates" : "[[41.220972, 1.729895], [41.220594, 1.730095], [41.220821, 1.730957], [41.222103, 1.730341], [41.222625, 1.732058], [41.222967, 1.732593], [41.223435, 1.732913], [41.224977, 1.733119], [41.225046, 1.733229], [41.225324, 1.733257], [41.225684, 1.733531], [41.226188, 1.73421], [41.22931, 1.737807], [41.229572, 1.738258], [41.229682, 1.738483], [41.229879, 1.738329], [41.229798, 1.738106], [41.22967, 1.738094], [41.22918, 1.737657], [41.228995, 1.737265], [41.228027, 1.736156], [41.227883, 1.735887],[41.228285, 1.735424]]",
         "type": "LineString"}

mensaje["route"] = route["coordinates"]

# Codifica el mensaje JSON a una cadena
mensaje_json = json.dumps(mensaje)

# Publica el mensaje en el topic "PTIN2023/A1/CAR"
client.publish("PTIN2023/DRON/STARTROUTE", mensaje_json)

# Cierra la conexión MQTT
client.disconnect()
