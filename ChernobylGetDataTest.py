import os
import time
from datetime import datetime
import json
import requests
import http.client, urllib.parse

url = "https://XXXXXXXXXX.execute-api.us-east-2.amazonaws.com/prod/dataBackToChernobyl"
r = requests.get(url)

print(r.text)
