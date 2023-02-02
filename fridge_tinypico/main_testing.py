import machine
from machine import Pin
from bme280_float import *
import gr_sensor

import time
from umqtt.simple2 import MQTTClient
import ubinascii
import secrets
import ntptime

from gr_wifi import wifi_connect, gr_wifi_down, gr_settime

board = "tinypico"

from tinypico import get_battery_voltage, go_deepsleep
import tinypico as cfg
from tinypico import get_battery_charging as get_vbus_present

DOT_READ_COLOR = (0,30,0,1)
DOT_SEND_COLOR = (30,0,0,1)
qos = 1


um_flag = True

bat_voltage = get_battery_voltage()

if get_vbus_present():
    print('on USB')
    bat_voltage = 5.0
else:
    print('on battery')
    bat_voltage = get_battery_voltage()
    


SDA_PIN = cfg.I2C_SDA
SCL_PIN = cfg.I2C_SCL
ds18b20_pin1 = const(4)
ds18b20_pin2 = const(14)

#DOTSTAR
from dotstar import DotStar
spi = machine.SoftSPI(sck=Pin( cfg.DOTSTAR_CLK ), mosi=Pin( cfg.DOTSTAR_DATA ), miso=Pin( cfg.SPI_MISO) )
dotstar = DotStar(spi, 1, brightness = 0.1 )
cfg.set_dotstar_power( True )
dotstar[0] = DOT_READ_COLOR

SLEEP_SEC = 5000
DEEPSLEEP_SEC = 300000 - SLEEP_SEC

BOARD_NAME = 'tinypicofridge'

SEND_DATA = True
SET_TIME = False

SLEEP_FLAG = False
MAX_TRIES = 10


topicdummy = "tinypicofridge"
client_id = ubinascii.hexlify(machine.unique_id())
payload_dict = {}
payload_dict[b'home/{}/fridgeupper'.format(topicdummy)] = ''
payload_dict[b'home/{}/fridgelower'.format(topicdummy)] = ''
payload_dict[b'home/{}/fridge_pres'.format(topicdummy)] = ''
payload_dict[b'home/{}/fridge_rh'.format(topicdummy)] = ''
payload_dict[b'home/{}/fridge_temp'.format(topicdummy)] = ''
payload_dict[b'home/{}/voltage'.format(topicdummy)] = ''


# fridge_topicupper = b'home/{}/fridgeupper'.format(topicdummy)
# fridge_topiclower = b'home/{}/fridgelower'.format(topicdummy)
# fridge_pres_topic = b'home/{}/fridge_pres'.format(topicdummy)
# fridge_rh_topic = b'home/{}/fridge_rh'.format(topicdummy)
# fridge_temp_topic = b'home/{}/fridge_temp'.format(topicdummy)
# voltage_topic = b'home/{}/voltage'.format(topicdummy)

i2c = machine.SoftI2C(scl=machine.Pin(SCL_PIN), sda=machine.Pin(SDA_PIN))
# i2c.scan()
bme280 = BME280(i2c=i2c)
# the 1st reading is mostly wrong...
T, P, Rh = bme280.read_compensated_data()
time.sleep_ms(200)



def gr_go_sleep(wlan):
    print('switching off..')
    dotstar[0] = ( 0, 0, 0, 1)
    cfg.set_dotstar_power( False )
#         wdt.feed()
    gr_wifi_down(wlan)
    print(f"sleeping {SLEEP_SEC/1000} sec..")
    machine.sleep(SLEEP_SEC)

    print(f"deep sleeping {DEEPSLEEP_SEC/1000} sec..")
    machine.sleep(100)        
    cfg.go_deepsleep(DEEPSLEEP_SEC)


# Received messages from subscriptions will be delivered to this callback
def gr_subscribe_topic(topic, msg, retain, dup):
    print((topic, msg, retain, dup))
    SLEEP_FLAG = True

def gr_pup_data (mqtt_client, payload_dict, qos=0, verbose_flag=True):
    for topic in sorted(payload_dict):
        if verbose_flag:
            print('publishing {} {}'.format(topic, payload_dict[topic]))
        mqtt_client.publish(topic, payload_dict[topic], qos=qos)
    if verbose_flag:
        print('published...')
    

def main():
    print(f"bat voltage: {bat_voltage}")

    # read DS18B20s
    ds_data = gr_sensor.read_ds18b20(ds18b20_pin1)
    for data in ds_data:
        print('T id {}: {}'.format(data, ds_data[data]))
        tempupper = ds_data[data]
    ds_data = gr_sensor.read_ds18b20(ds18b20_pin2)
    for data in ds_data:
        print('T id {}: {}'.format(data, ds_data[data]))
        templower = ds_data[data]
    if templower > tempupper:
        tmp = templower
        templower = tempupper
        tempupper = tmp
    #read BME280
    T, P, Rh = bme280.read_compensated_data()
    P = P/100.
    print(f"T: {T}, P: {P}, Rh: {Rh}")
    topic_to_subscribe = b'home/{}/voltage'.format(topicdummy)
    payload_dict[b'home/{}/fridgeupper'.format(topicdummy)] = '{}'.format(tempupper)
    payload_dict[b'home/{}/fridgelower'.format(topicdummy)] = '{}'.format(templower)
    payload_dict[b'home/{}/fridge_pres'.format(topicdummy)] = '{}'.format(P)
    payload_dict[b'home/{}/fridge_rh'.format(topicdummy)] = '{}'.format(Rh)
    payload_dict[b'home/{}/fridge_temp'.format(topicdummy)] = '{}'.format(T)
    payload_dict[topic_to_subscribe] = '{}'.format(bat_voltage)
        
        
    #     wdt.feed()
    while True:
        
        if SEND_DATA:
            # light up LED while sending
            dotstar[0] = DOT_SEND_COLOR

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
            client.set_callback(gr_subscribe_topic)
            client.connect()
            client.subscribe(topic_to_subscribe)

            gr_pup_data(client, payload_dict, qos=qos, verbose_flag=True)
            
            MAX_TRIES = 10
            m_idx = 0
            while MAX_TRIES > m_idx:
                client.check_msg()
                
                if SLEEP_FLAG:
                    print('going to sleep...')
                    gr_go_sleep(wlan)
                else:
                    machine.sleep(10000)
                    gr_pup_data(client, payload_dict, qos=qos, verbose_flag=True)
                    print(f"publish try #{m_idx}")
                    m_idx += 1
            
            
            


main()

