import tkinter as tk
import tkinter.ttk as ttk
from tkinter import BOTH, RIGHT, RAISED
from tkinter.ttk import Frame, Button, Style
import os
import time
from datetime import datetime
import json
import requests
import http.client, urllib.parse

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

tempSensor = '/sys/bus/w1/devices/22-0000005740da/w1_slave'
url = "https://XXX.execute-api.us-east-2.amazonaws.com/prod/chernobylFunc"


sanakirja = {"data1": ["1", "2", "3"],
            "data2": ["4", "5", "6"],
            "data3": ["7", "8", "9"]}


class ChernobylStation(Frame):

    def __init__(self):
        super().__init__()

        self.frameMain = Frame(self, relief=RAISED, borderwidth=1)
        self.style = Style()

        self.valikko = ttk.Combobox(self.frameMain, values=list(sanakirja.keys()))
        self.label = tk.Label(self.frameMain, text="Select date from the drop down menu")
        self.closeButton = Button(self, text="Close", command=self.quit)
        self.searchButton = Button(self.frameMain, text="Search", command=lambda: self.plot())

        self.initUI()

    def plot(self):
        self.label.configure(text=self.valikko.get())

    def initUI(self):
        self.master.title("Chernobyl Control Station 1")
        self.style.theme_use("default")
        self.frameMain.pack(fill=BOTH, expand=True)
        self.label.place(x=100, y=80)
        self.valikko.place(x=80, y=120)
        self.searchButton.place(x=240, y=120)
        self.pack(fill=BOTH, expand=True)
        self.closeButton.pack(side=RIGHT, padx=5, pady=5)

    def rawTemp(self):
        f = open(tempSensor, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def readTemp(self):
        lines = self.rawTemp()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.rawTemp()
        tempOutput = lines[1].find('t=')
        if tempOutput != -1:
            tempString = lines[1].strip()[tempOutput + 2:]
            tempC = float(tempString) / 1000.0
            tempF = tempC * 9.0 / 5.0 + 32.0

        # print("Temperature in Celcius: ",tempC)
        # print("Temperature in Fahrenheit: ", tempF)

        return tempC

    def getDate(self):
        return self.date()

    def getTime(self):
        return self.time()


def main():
    root = tk.Tk()
    root.geometry("400x300")
    app = ChernobylStation()
    root.mainloop()
    while True:
        d = datetime.now()
        measurements = {
            "timestamp": str(d),
            "temperature": str(ChernobylStation().readTemp()),
            "date": str(ChernobylStation().getDate(d)),
            "time": str(ChernobylStation().getTime(d))
        }

        post_body = json.dumps(measurements)
        r = requests.post(url, data=post_body)
        print("Trying to send data: ", measurements)
        print(r.text)
        time.sleep(1)
