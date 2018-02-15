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
import pymysql

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

tempSensor = '/sys/bus/w1/devices/22-0000005740da/w1_slave'

uniqueDatesRaw = []
uniqueDatesParsed = []
filt = "[(',)]"


db = pymysql.connect(host="mysli.oamk.fi", user="t6kovi01", passwd="xxx", db="opisk_t6kovi01")
query = ""

class ChernobylStation(Frame):

    def __init__(self):
        super().__init__()
        self.frameMain = Frame(self, relief=RAISED, borderwidth=1)
        self.style = Style()
        uniqueDatesRaw = self.getUniqueDates()
        for row in uniqueDatesRaw:
            line = str(row)
            uniqueDatesParsed.append(line.replace(filt,"")) ## Ei filtteröi oikein
        self.valikko = ttk.Combobox(self.frameMain, values=list(uniqueDatesParsed))
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
        self.valikko.place(x=40, y=120)
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
    @staticmethod
    def getDate(d):
        return d.date()
    @staticmethod
    def getTime(d):
        return d.strftime("%H:%M:%S")

    
    def sendReadings(self):
        d = datetime.now()
        date = str(self.getDate(d))
        time = str(self.getTime(d))
        temp = self.readTemp()
        query = "INSERT INTO chernobylmeasurements(date, time, temp) VALUES('{0}','{1}',{2})".format(date, time, temp)
        cur = db.cursor()
        cur.execute(query)
        db.commit()
        self.after(1000, self.sendReadings)
    @staticmethod
    def getShitFromDB():
        query = "SELECT time, temp FROM chernobylmeasurements WHERE date LIKE '2018-02-15'"
        cur = db.cursor()
        cur.execute(query)
        taulu = cur.fetchall()
        print(taulu[0])
       
    def getUniqueDates(self):
        query = "SELECT DISTINCT(date) from chernobylmeasurements"
        cur = db.cursor()
        cur.execute(query)
        taulu = cur.fetchall()
        return taulu
          
def main():
    root = tk.Tk()
    root.geometry("400x300")
    app = ChernobylStation()
    root.after(0, app.sendReadings())
    root.mainloop()
        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, closing the database!")
        db.close()
