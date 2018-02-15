import os
import time
from datetime import datetime
import json
import requests
import http.client, urllib.parse

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

tempSensor = '/sys/bus/w1/devices/22-0000005740da/w1_slave'
url = "https://XXXXXXXXXX.execute-api.us-east-2.amazonaws.com/prod/chernobylFunc"


def rawTemp():
    f = open(tempSensor, 'r')
    lines = f.readlines()
    f.close()
    return lines

def readTemp():
    lines = rawTemp()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = rawTemp()
    tempOutput = lines[1].find('t=')
    if tempOutput != -1:
        tempString = lines[1].strip()[tempOutput+2:]
        tempC = float(tempString) / 1000.0
        tempF = tempC * 9.0 / 5.0 + 32.0
    
    #print("Temperature in Celcius: ",tempC)
    #print("Temperature in Fahrenheit: ", tempF)
    
    return tempC

def getDate(d):
    return d.date()

def getTime(d):
    return d.time()
         
def main():
    
    while True:
        d = datetime.now()
        measurements = {
            "timestamp": str(d),
            "temperature": str(readTemp()),
            "date" : str(getDate(d)),
            "time" : str(getTime(d))
            }
        
        post_body = json.dumps(measurements)
        r = requests.post(url, data = post_body)
        print("Trying to send data: ", measurements)
        print(r.text)
        time.sleep(1)

if __name__ == "__main__":
    main()
