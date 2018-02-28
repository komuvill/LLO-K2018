import tkinter as tk
import tkinter.ttk as ttk
from tkinter import BOTH, RIGHT, RAISED
from tkinter.ttk import Frame, Button, Style
import os
import time
from datetime import datetime
import pymysql
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

tempSensor = '/sys/bus/w1/devices/22-0000005740da/w1_slave'

uniqueDatesRaw = []
uniqueDatesParsed = []

db = pymysql.connect(host="xxx", user="xxx", passwd="xxx", db="xxx")
query = ""

ledPin = 20
buttonPin = 23
meltdownPin = 18
meltdownInProgress = False
kuittaus = False #Kriittisen massan kuittaus
timer = 0 #Timer käynnistyy, jos kriittistä massaa ei kuitata

class ChernobylStation(Frame):
    
    #Käyttöliittymäkomponenttien, pinnien yms. alkumäärittelyt
    def __init__(self):
        super().__init__()
        self.frameMain = Frame(self, relief=RAISED, borderwidth=1)
        self.style = Style()
        uniqueDatesRaw = self.getUniqueDates()
        
        #Siivotaan uniikkien päivämäärien raakadatasta ylimääräiset merkit pois
        for row in uniqueDatesRaw:
            line = str(row)
            uniqueDatesParsed.append(line.lstrip("(,'").rstrip("',)"))
            
        #Käyttöliittymäkomponentit    
        self.valikko = ttk.Combobox(self.frameMain, values=list(uniqueDatesParsed))
        self.label = tk.Label(self.frameMain, text="Select date from the drop down menu")
        self.closeButton = Button(self, text="Close", command =lambda: self.close())
        self.plotButton = Button(self.frameMain, text="Plot", command=lambda: self.plot())
        self.meltDownLabel = tk.Label(self.frameMain, text="")
        #Pinnit
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ledPin, GPIO.OUT)
        GPIO.setup(meltdownPin, GPIO.OUT)
        GPIO.output(meltdownPin, GPIO.LOW)
        GPIO.setup(buttonPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        self.initUI()
    
    #Lisää käyttöliittymäkomponenttien määrittelyä
    def initUI(self):
        self.master.title("Chernobyl Control Station 1")
        self.style.theme_use("default")
        self.frameMain.pack(fill=BOTH, expand=True)
        self.label.place(x=40, y=80)
        self.valikko.place(x=40, y=120)
        self.plotButton.place(x=240, y=120)
        self.meltDownLabel.place(x = 40, y = 160)
        self.pack(fill=BOTH, expand=True)
        self.closeButton.pack(side=RIGHT, padx=5, pady=5)
    
    #Tietokantayhteyksien ja pinnien oikeaoppinen sammuttaminen
    def close(self):
        GPIO.cleanup()
        db.close()
        self.master.destroy()
    
    #Haetaan raakadata lämpötilasensorilta
    def rawTemp(self):
        f = open(tempSensor, 'r')
        lines = f.readlines()
        f.close()
        return lines
    
    #Siivotaan raakadata
    def readTemp(self):
        lines = self.rawTemp()
        
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.rawTemp()
        tempOutput = lines[1].find('t=')
        
        if tempOutput != -1:
            tempString = lines[1].strip()[tempOutput + 2:]
            tempC = float(tempString) / 1000.0
            
        return tempC
    
    #Palauttaa datetime-olion päivämääräkomponentin
    @staticmethod
    def getDate(d):
        return d.date()
    #Palauttaa datetime-olion kellonaikakomponentin
    @staticmethod
    def getTime(d):
        return d.strftime("%H:%M:%S")
    
    #Datan plottaus halutulta päivämäärältä
    def plot(self):
        date = self.valikko.get()
        taulu = self.getReadings(date)
        x = []
        y = []
        for e in taulu:
            y.append(float(e[1]))
            x.append(datetime.strptime(e[0], '%H:%M:%S'))
            
        plt.plot( x, y, linestyle='-' , marker='o')
        plt.gcf().autofmt_xdate()
        plt.show()
    
    #Tallennetaan lukemat tietokantaan, kutsutaan sekunnin välein
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
    
    #Haetaan halutun päivämäärän mittaustulokset, palauttaa tuplen
    def getReadings(self, date):
        query = "SELECT time, temp FROM chernobylmeasurements WHERE date LIKE '{0}'".format(date)
        print(query)
        cur = db.cursor()
        cur.execute(query)
        taulu = cur.fetchall()
        return taulu
    
    #Hakee uniikit päivämäärät, jolloin mittauksia on suoritettu   
    def getUniqueDates(self):
        query = "SELECT DISTINCT(date) FROM chernobylmeasurements"
        cur = db.cursor()
        cur.execute(query)
        taulu = cur.fetchall()
        return taulu
    
    #Hakee tuoreimman mittaustuloksen tietokannasta ja käynnistää reaktorin ytimen sulamisen
    def checkIfMeltdownImminent(self):
        query = "SELECT temp FROM chernobylmeasurements WHERE id = (SELECT max(id) FROM chernobylmeasurements)"
        cur = db.cursor()
        cur.execute(query)
        latestTemp = str(cur.fetchall()).lstrip("((").rstrip(",),)")
        self.after(10, self.checkIfMeltdownImminent) #Metodia kutsutaan 10 millisekunnin välein
        global meltdownInProgress, kuittaus, timer
        
        #Jos mitattu lämpötila on yli 23 astetta käynnistetään ajastin ja sytytetään keltainen ledi merkiksi lähestyvästä katastrofista
        if((float(latestTemp)) > 23.0 and kuittaus == False):
            if(GPIO.input(ledPin) == False):
                GPIO.output(ledPin, GPIO.HIGH)
                
            self.meltDownLabel.config(text = "MELTDOWN IS IMMINENT!", bg = "red")
            meltdownInProgress = True
            timer += 1
        elif(meltdownInProgress != True or kuittaus == True):
            self.meltDownLabel.config(text = "Everything is fine, latest reading: " + latestTemp, bg="light green")
            #Uusi ytimen sulaminen voi alkaa vasta kun entinen on kuitattu ja lämpötila laskee takaisin alle 23 asteen
            if((float(latestTemp)) < 23.0):
               kuittaus = False
               
        self.preventMeltdown() #Tarkastetaan onko teknikko käynnistänyt sulamisen estämisen
        #timer-muuttuja saa arvon 500 noin 5 sekunnissa, onnettomuus on tällöin tapahtunut
        if(timer > 500):
            GPIO.output(meltdownPin, GPIO.HIGH)

    def preventMeltdown(self):
        global meltdownInProgress, kuittaus, timer
        #Kuittaus tapahtuu painonapilla
        if(GPIO.input(buttonPin) == False):
           GPIO.output(ledPin, GPIO.LOW)
           meltdownInProgress = False
           kuittaus = True
           timer = 0           
#Ohjelman pääfunktio                     
def main():
    root = tk.Tk()
    root.geometry("400x300")
    app = ChernobylStation()
    root.after(0, app.sendReadings())
    root.after(0, app.checkIfMeltdownImminent())
    root.mainloop()
        
if __name__ == "__main__":
    try:
        main()
    #Ctrl+C Pythonin shellissä saa aikaan KeyboardInterruptin, joka sammuttaa tietokantayhteyden ja "siivoaa" pinnit    
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, closing the database!")
        db.close()
        GPIO.cleanup()
        root.quit()
