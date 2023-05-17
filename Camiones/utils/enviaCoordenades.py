import paho.mqtt.client as mqtt
import json

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
	   	"state": "ESTACIONADO"}
	   	
	   	
#id_car, pos_ini, pos_final, pos_act, batery, autonomy, state{CARGANDO, DESCARGANDO, ESTACIONADO, REPARTIENDO, ALERTA}

# Codifica el mensaje JSON a una cadena
mensaje_json = json.dumps(mensaje)

# Publica el mensaje en el topic "PTIN2023/A1/CAR"
client.publish("PTIN2023/A1/CAR/UPDATEPOSITION", mensaje_json)

# Cierra la conexión MQTT
client.disconnect()
