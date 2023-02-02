# gr_sensor_reading

import onewire
import ds18x20
import machine
import time
from ubinascii import hexlify
import uasyncio as asyncio

async def read_ds18b20_async(pin, verbose=False):
    ow = onewire.OneWire(machine.Pin(pin))
    ds = ds18x20.DS18X20(ow)
    roms = ds.scan()
    ds.convert_temp()
    await asyncio.sleep_ms(750)
    ret = {}
    async for rom in roms:
        ret[hexlify(rom)]=ds.read_temp(rom)
        
    if verbose:
        print(ret)
    
    return ret

def read_ds18b20(pin, verbose=False):
    ow = onewire.OneWire(machine.Pin(pin))
    ds = ds18x20.DS18X20(ow)
    roms = ds.scan()
    ds.convert_temp()
    time.sleep_ms(750)
    ret = {}
    for rom in roms:
        ret[hexlify(rom)]=ds.read_temp(rom)
        
    if verbose:
        print(ret)
    
    return ret


    