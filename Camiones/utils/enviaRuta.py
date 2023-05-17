import paho.mqtt.client as mqtt
import json

# Crea un objeto cliente MQTT
client = mqtt.Client()

# Conecta al servidor MQTT
client.connect("test.mosquitto.org", 1883, 60)

# Crea un mensaje JSON
mensaje = {	"idVehicle": 123456789, 
	   	"coordenadaXO": 8.432412321,
	   	"coordenadaYO": -1.321312313, 
	   	"coordenadaXD": 12.432412321,
	   	"coordenadaYD": -4.321312313}

# Codifica el mensaje JSON a una cadena
mensaje_json = json.dumps(mensaje)

# Publica el mensaje en el topic "PTIN2023/A1/CAR"
client.publish("PTIN2023/A1/CAR/DEFINEROUTE", mensaje_json)

# Cierra la conexión MQTT
client.disconnect()
