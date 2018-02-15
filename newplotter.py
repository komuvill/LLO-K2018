import matplotlib.pyplot as plt
from datetime import datetime
import pymysql


db = pymysql.connect(host="xxx", user="xxx", passwd="xxx", db="xxx")
x = []
y = []

query = "SELECT time, date, temp FROM chernobylmeasurements WHERE date LIKE '2018-02-15'"
cur = db.cursor()
cur.execute(query)
taulu = cur.fetchall()

for e in taulu:
    y.append(float(e[2]))
    x.append(datetime.strptime(e[1]+" "+e[0], '%Y-%m-%d %H:%M:%S'))
    
plt.plot( x, y, linestyle='-', marker='o')
plt.gcf().autofmt_xdate()
plt.show()
