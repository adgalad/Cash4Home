import json
import requests
import os
import time
import sys

## Pair: BTCUSD, USDBTC, DASHUSD, etc
class PriceRetriever:
  def __init__(self):
    self.localbitcoins = {}
    self.gemini = {}
    self.bitinka = {}
    self.ripio = {}

  def ask(self):
    # print(requests.get('https://localbitcoins.com//bitcoinaverage/ticker-all-currencies/').content)
    try:
        self.localbitcoins = json.loads(requests.get('https://localbitcoins.com//bitcoinaverage/ticker-all-currencies/').content.decode('utf-8'))
    except:
        self.localbitcoins = None
    
    try:
        self.gemini = json.loads(requests.get('https://api.gemini.com/v1/pubticker/btcusd').content.decode('utf-8'))
    except:
        self.gemini = None
    

    try:
        self.bitinka = json.loads(requests.get('https://www.bitinka.com/api/apinka/ticker?format=json').content.decode('utf-8'))
    except:
        self.bitinka = None
    

    try:
        self.ripio = json.loads(requests.get('https://www.ripio.com/api/v1/rates/').content.decode('utf-8'))
    except:
        self.ripio = None

  def avg(self, symbol, prices):
    count = 0
    average = 0
    if not (symbol in prices and prices[symbol]['prices']): return 0

    for k,v in prices[symbol]['prices'].items():
        average += v
        count += 1

    return average/count

  def getPriceInformation(self):
    prices = {
                'USD': { 'prices':{}, 'name':'', 'avg': 0 },
                'ARS': { 'prices':{}, 'name':'', 'avg': 0 },
                'PEN': { 'prices':{}, 'name':'', 'avg': 0 },
                'VEF': { 'prices':{}, 'name':'', 'avg': 0 }
            }

    if self.localbitcoins:
        prices['USD']['prices']['Localbitcoins'] = float(self.localbitcoins["USD"]["avg_12h"])
        prices['VEF']['prices']['Localbitcoins'] = float(self.localbitcoins['VEF']['avg_12h'])
        prices['ARS']['prices']['Localbitcoins'] = float(self.localbitcoins['ARS']['avg_12h'])
        prices['PEN']['prices']['Localbitcoins'] = float(self.localbitcoins['PEN']['avg_12h'])
    
    if self.gemini:
        prices['USD']['prices']['Gemini'] = float(self.gemini['ask'])
    
    if self.bitinka:
        prices['USD']['prices']['Bitinka'] = float(self.bitinka['USD']['ask'])
        prices['ARS']['prices']['Bitinka'] = float(self.bitinka['ARS']['ask'])
        prices['PEN']['prices']['Bitinka'] = float(self.bitinka['PEN']['ask'])

    if self.ripio:
        prices['USD']['prices']['Ripio (Venta)'] = float(self.ripio['rates']['USD_SELL'])
        prices['USD']['prices']['Ripio (Compra)'] = float(self.ripio['rates']['USD_BUY'])
        prices['ARS']['prices']['Ripio (Venta)'] = float(self.ripio['rates']['ARS_SELL'])
        prices['ARS']['prices']['Ripio (Compra)'] = float(self.ripio['rates']['ARS_BUY'])
        prices['PEN']['prices']['Ripio (Venta)'] = float(self.ripio['rates']['PEN_SELL'])
        prices['PEN']['prices']['Ripio (Compra)'] = float(self.ripio['rates']['PEN_BUY'])

    prices['USD']['avg'] = self.avg('USD', prices)
    prices['VEF']['avg'] = self.avg('VEF', prices)
    prices['ARS']['avg'] = self.avg('ARS', prices)
    prices['PEN']['avg'] = self.avg('PEN', prices)

    prices['USD']['symbol'] = '$'
    prices['VEF']['symbol'] = 'Bs.'
    prices['ARS']['symbol'] = '$'
    prices['PEN']['symbol'] = '$'
    
    return prices




class UpdateBTCPrice():
    RUN_EVERY_SECS = 2

    def __init__(self):
        self.BTCPrice = PriceRetriever()
    
    def do(self):
        try:
            self.BTCPrice.ask()
            info = json.dumps(self.BTCPrice.getPriceInformation())
            file = open(os.path.join('./media', "BTCPrice.json"), "w")
            file.write(info)
            file.close()

        except Exception as e:
            print(e)

        
        

x = UpdateBTCPrice()

while(True):
    x.do()
    time.sleep(x.RUN_EVERY_SECS)