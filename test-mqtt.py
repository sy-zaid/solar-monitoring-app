import paho.mqtt.client as mqtt
import time, json
import random

client = mqtt.Client()
client.connect("localhost", 1883)

# alert_types = ["info", "warning", "error"]
ac_output_power = 220
battery_discharge_current = 20
while True:
    power = random.randint(1000, 3000)
    voltage = random.randint(200, 250)
    
    # Regular data
    # client.publish("inverter/alert",300)
    
    client.publish('05 --- Grid Up',f"ALERT🚨 BATTERY DRAINING FAST:\n{ac_output_power}W | \n{battery_discharge_current}A is higher than normal usage and battery will drop faster. Please reduce the load")
    
    # Notifications based on conditions
    # if power > 2800:
    #     client.publish(200)
    #     client.publish("inverter/alert", "High power shutdown risk!")
    
    
    print(f"Sent data - Power: {power}W, Voltage: {voltage}V")
    time.sleep(20)