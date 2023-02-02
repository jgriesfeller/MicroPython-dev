import machine
# from bme280_float import *
# import gr_sensor

import time
from umqtt.simple import MQTTClient
import ubinascii
import secrets
import ntptime

# ds18b20_pin1 = const(4)
# ds18b20_pin2 = const(5)
TPL_PIN = const(37)
# NEOPXL_PIN = tinys2.RGB_DATA
#LED_PIN = const(13)
SLEEP_SEC = 5000
DEEPSLEEP_SEC = 10000 - SLEEP_SEC
# wdt = machine.WDT(timeout=int(DEEPSLEEP_SEC / 2))

BOARD_NAME = 's2_mqtt_test'

# import neopixel
SEND_DATA = True
SET_TIME = False


NEOPXL_READ_COLOR = (0,50,0)
NEOPXL_SEND_COLOR = (50,0,0)
qos = 1

topicdummy = "esp8266mqtttest"
client_id = ubinascii.hexlify(machine.unique_id())
fridge_topicupper = b'home/{}/fridgeupper'.format(topicdummy)
fridge_topiclower = b'home/{}/fridgelower'.format(topicdummy)
fridge_pres_topic = b'home/{}/fridge_pres'.format(topicdummy)
fridge_rh_topic = b'home/{}/fridge_rh'.format(topicdummy)
fridge_temp_topic = b'home/{}/fridge_temp'.format(topicdummy)
voltage_topic = b'home/{}/voltage'.format(topicdummy)

#tplpin = machine.Pin(TPL_PIN, machine.Pin.OUT,)

#led = machine.Pin(LED_PIN, machine.Pin.OUT,)
# i2c = machine.SoftI2C(scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN))
# i2c.scan()
# bme280 = BME280(i2c=i2c)
# the 1st reading is mostly wrong...
T, P, Rh = [22.0,1013.0,66.0]
bat_voltage = 3.99
tempupper = 33.0
templower = -11.0
time.sleep_ms(200)

def main():
#     wdt.feed()
    
    while True:
        print(f"T: {T}, P: {P}, Rh: {Rh}")
        
        if SEND_DATA:
            # light up LED while sending
#             np[0] = NEOPXL_SEND_COLOR
#             np.write()

            from gr_wifi import wifi_connect, gr_wifi_down, gr_settime
            # wlan = wifi_connect()
            try:               
                wifi_up = wlan.isconnected()
                print('wifi is up')
                print(wlan.ifconfig())
            except:
                print('wifi is down')
                wlan = wifi_connect()
                print(wlan.ifconfig())

                wifi_up = wlan.isconnected()
            if SET_TIME:
                gr_settime(wlan=wlan, verbose=True)
            
                
            client = MQTTClient(client_id,
                                secrets.secrets_local['mqtt_broker'],
                                user=secrets.secrets_local['mqtt_user'],
                                password=secrets.secrets_local['mqtt_pass'])
            client.connect()
            print('publishing {} {}'.format(fridge_topicupper, tempupper))
            client.publish(fridge_topicupper, '{}'.format(tempupper), qos=qos)
            print('publishing {} {}'.format(fridge_topiclower, templower))
            client.publish(fridge_topiclower, '{}'.format(templower), qos=qos)
            
            print('publishing {} {}'.format(fridge_rh_topic, Rh))
            client.publish(fridge_rh_topic, '{}'.format(Rh), qos=qos)
            
            print('publishing {} {}'.format(fridge_temp_topic, T))
            client.publish(fridge_temp_topic, '{}'.format(T), qos=qos)

            print('publishing {} {}'.format(fridge_pres_topic, P))
            client.publish(fridge_pres_topic, '{}'.format(P), qos=qos)
            
            client.publish(voltage_topic, '{}'.format(bat_voltage), qos=qos)
            print('published {} {}'.format(voltage_topic, bat_voltage))
            
            client.disconnect()
            print('published..')
            gr_wifi_down(wlan)
            
        print('switching off..')
#         wdt.feed()
        print(f"sleeping {SLEEP_SEC/1000} sec..")
        machine.sleep(SLEEP_SEC)

        print(f"deep sleeping {DEEPSLEEP_SEC/1000} sec..")
        machine.sleep(100)        
        machine.deepsleep(DEEPSLEEP_SEC)


main()

