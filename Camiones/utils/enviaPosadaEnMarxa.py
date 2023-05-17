import paho.mqtt.client as mqtt
import json

# Crea un objeto cliente MQTT
client = mqtt.Client()

# Conecta al servidor MQTT
client.connect("test.mosquitto.org", 1883, 60)

# Crea un mensaje JSON
mensaje = {	"idVehicle": 123456789, 
	   	"estatVehicle": "START"
	   }

# Codifica el mensaje JSON a una cadena
mensaje_json = json.dumps(mensaje)

# Publica el mensaje en el topic "PTIN2023/A1/CAR"
client.publish("PTIN2023/A1/CAR/STATUS", mensaje_json)

# Cierra la conexión MQTT
client.disconnect()
