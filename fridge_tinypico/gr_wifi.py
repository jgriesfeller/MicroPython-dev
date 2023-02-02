import secrets

global sta_if

def gr_wifi_up(ssid=secrets.secrets_local['ssid'],
               passwd=secrets.secrets_local['wifi_passwd'],
               connection_time=3,
               max_tries=5,
               verbose=True):
    """bring wifi up"""
    import network
    import time
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    tries = 0
    print('wifi try {:1d}\n.'.format(tries+1))

    while tries <= max_tries:
        wlan.connect(ssid, passwd)
        if verbose:
            print("sleeping {} sec for connection...".format(connection_time))
        time.sleep(connection_time)
        connect_status = wlan.isconnected()
        if connect_status:
            break
        else:
            if verbose:
                print('wifi connect try {} failed!'.format(tries))
            tries += 1
            
    if verbose:
        print(wlan.ifconfig())
    return wlan, connect_status

def gr_wifi_down(wlan):
    """bring wifi down"""
    wlan.disconnect()
    wlan.active(False)
    
def gr_settime(wlan=None, verbose=True):
    """set time using ntp (to UTC)"""
    ext_flag = True
    if wlan is None:
        wlan, connect_status = gr_wifi_up(verbose=verbose)
        ext_flag = False

    import ntptime
    ntptime.settime()
    if verbose:
        from machine import RTC
        rtc = RTC()
        if verbose:
            print(rtc.datetime())
    if not ext_flag:
        gr_wifi_down(wlan)
    
# def gr_add_timezone(year, month, day, hour, tz_offset=1):
#     """adjust time puple to local time including daylight saving"""
#     hour += tz_offset
#     if hour > 23:
#         day += 1
#         hour = 0
#         if 
        
###########################################################################

def wifi_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(secrets.secrets_local['ssid'], secrets.secrets_local['wifi_passwd'])
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())
    return sta_if

def no_debug():
    import esp
    # you can run this from the REPL as well
    esp.osdebug(None)


