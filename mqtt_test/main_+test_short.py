# clean.py Test of asynchronous mqtt client with clean session.
# (C) Copyright Peter Hinch 2017-2019.
# Released under the MIT licence.

# Public brokers https://github.com/mqtt/mqtt.github.io/wiki/public_brokers

# The use of clean_session means that after a connection failure subscriptions
# must be renewed (MQTT spec 3.1.2.4). This is done by the connect handler.
# Note that publications issued during the outage will be missed. If this is
# an issue see unclean.py.

# red LED: ON == WiFi fail
# blue LED heartbeat: demonstrates scheduler is running.

from mqtt_as import MQTTClient, config
#from config import wifi_led, blue_led  # Local definitions
import uasyncio as asyncio
import secrets
import time
import gc
gc.collect()
import gr_sensor
from machine import Pin

topic_genuine_ds18b20 = b'home/ds18b20_genuine/temperature'


genuine_pin = const(9)
blue_led_pin = const(15)

blue_led = Pin(blue_led_pin, Pin.OUT, value = 1)

def toggle_pin(pin):
    if pin.value() == 1:
        pin.off()
    else:
        pin.on()
        
    



# Subscription callback
def sub_cb(topic, msg, retained):
    print((topic, msg, retained))

# Demonstrate scheduler is operational.
async def heartbeat():
    s = True
    while True:
        await asyncio.sleep_ms(500)
        toggle_pin(blue_led)

async def wifi_han(state):
#    wifi_led(not state)
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):
    await client.subscribe('foo_topic', 1)

async def main(client):
    try:
        await client.connect()
    except OSError:
        print('Connection failed.')
        return
    n = 0
    while True:
        genuine_data = gr_sensor.read_ds18b20(genuine_pin)
        for data in genuine_data:
            print('genuine T id {}: {}'.format(data, genuine_data[data]))
            genuine_temp = genuine_data[data]
        await asyncio.sleep(5)
        print('publish {} {}'.format(topic_genuine_ds18b20, genuine_temp))
        # If WiFi is down the following will pause for the duration.
        await client.publish(topic_genuine_ds18b20, '{}'.format(genuine_temp), qos = 0)
        n += 1
        await asyncio.sleep(60)
#         time.sleep(60)

# Define configuration
config['subs_cb'] = sub_cb
config['wifi_coro'] = wifi_han
config['connect_coro'] = conn_han
config['clean'] = True

config['server'] = secrets.secrets_local['mqtt_broker']
config['user'] = secrets.secrets_local['mqtt_user']
config['password'] = secrets.secrets_local['mqtt_pass']

# config['server'] = 'iot.eclipse.org'

# Not needed if you're only using ESP8266
config['ssid'] = secrets.secrets_local['ssid']
config['wifi_pw'] = secrets.secrets_local['wifi_passwd']

# Set up client
# MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)

asyncio.create_task(heartbeat())
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
    asyncio.new_event_loop()
