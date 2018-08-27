import json
import requests
import os
import time
import sys

## Pair: BTCUSD, USDBTC, DASHUSD, etc
class PriceRetriever:
  def __init__(self):
    self.localbitcoins = None
    self.gemini = None
    self.bitinka = None
    self.ripio = None
    self.cexio = None
    self.coinbase = None

  def ask(self):
    # print(requests.get('https://localbitcoins.com//bitcoinaverage/ticker-all-currencies/').content)
    try:
        self.localbitcoins = json.loads(requests.get('https://localbitcoins.com/bitcoinaverage/ticker-all-currencies/', timeout=10).content.decode('utf-8'))
    except:
        self.localbitcoins = None
    
    try:
        self.gemini = json.loads(requests.get('https://api.gemini.com/v1/pubticker/btcusd', timeout=10).content.decode('utf-8'))
    except:
        self.gemini = None
    

    try:
        self.bitinka = json.loads(requests.get('https://www.bitinka.com/api/apinka/ticker?format=json', timeout=10).content.decode('utf-8'))
    except:
        self.bitinka = None
    
    
    
    try:
        self.ripio = json.loads(requests.get('https://www.ripio.com/api/v1/rates/', timeout=10).content.decode('utf-8'))
    except:
        self.ripio = None
    
    try:
        self.cexio = json.loads(requests.get('https://cex.io/api/ticker/BTC/USD', timeout=10).content.decode('utf-8'))
    except:
        self.cexio = None
    
    try:
        self.binance = json.loads(requests.get('https://api.binance.com/api/v1/ticker/price?symbol=BTCUSDT', timeout=10).content.decode('utf-8'))
    except:
        self.binance = None

    try:
        self.coinbase = json.loads(requests.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC', timeout=10).content.decode('utf-8'))
    except:
        self.coinbase = None

  def avg(self, symbol, prices):
    count = 0
    average = 0
    if not (symbol in prices and prices[symbol]['prices']): return 0

    for k,v in prices[symbol]['prices'].items():
        average += v
        count += 1

    return average/count

  def getPriceInformation(self):
    try:
        file = open(os.path.join('./staticfiles', "BTCPrice.json"), "r")
    except Exception as e:
        open(os.path.join('./staticfiles', "BTCPrice.json"), "w").close()

        file = open(os.path.join('./staticfiles', "BTCPrice.json"), "r")
    try:
        prices = json.loads(file.read())
    except Exception as e:
        prices = {
                    'USD': { 'prices':{}, 'name':'', 'avg': 0 },
                    'VES': { 'prices':{}, 'name':'', 'avg': 0 },
                    'ARS': { 'prices':{}, 'name':'', 'avg': 0 },
                    'PEN': { 'prices':{}, 'name':'', 'avg': 0 },
                }

    if self.localbitcoins:
        prices['USD']['prices']['Localbitcoins'] = float(self.localbitcoins["USD"]["rates"]['last'])
        prices['VES']['prices']['Localbitcoins'] = float(self.localbitcoins['VES']['rates']['last'])
        prices['ARS']['prices']['Localbitcoins'] = float(self.localbitcoins['ARS']['rates']['last'])
        prices['PEN']['prices']['Localbitcoins'] = float(self.localbitcoins['PEN']['rates']['last'])
    
    if self.gemini:
        prices['USD']['prices']['Gemini'] = float(self.gemini['ask'])
    
    if self.bitinka:
        prices['USD']['prices']['Bitinka'] = float(self.bitinka['USD']['ask'])
        prices['ARS']['prices']['Bitinka'] = float(self.bitinka['ARS']['ask'])
        prices['PEN']['prices']['Bitinka'] = float(self.bitinka['PEN']['ask'])

    if self.ripio:
        prices['USD']['prices']['Ripio']  = float(self.ripio['rates']['USD_SELL'])
        # prices['USD']['prices']['Ripio (Compra)'] = float(self.ripio['rates']['USD_BUY'])
        # prices['ARS']['prices']['Ripio']  = float(self.ripio['rates']['ARS_SELL'])
        prices['ARS']['prices']['Ripio'] = float(self.ripio['rates']['ARS_BUY'])
        # prices['PEN']['prices']['Ripio']  = float(self.ripio['rates']['PEN_SELL'])
        prices['PEN']['prices']['Ripio'] = float(self.ripio['rates']['PEN_BUY'])

    if self.binance:
        prices['USD']['prices']['Binance']  = float(self.binance['price'])

    if self.cexio:
        prices['USD']['prices']['Cex.io'] = float(self.cexio['ask'])

    if self.coinbase:
        prices['USD']['prices']['Coinbase'] = float(self.coinbase['data']['rates']['USD'])
        prices['ARS']['prices']['Coinbase'] = float(self.coinbase['data']['rates']['ARS'])
        prices['PEN']['prices']['Coinbase'] = float(self.coinbase['data']['rates']['PEN'])

    prices['USD']['avg'] = self.avg('USD', prices)
    prices['VES']['avg'] = self.avg('VES', prices)
    prices['ARS']['avg'] = self.avg('ARS', prices)
    prices['PEN']['avg'] = self.avg('PEN', prices)

    prices['USD']['symbol'] = '$'
    prices['VES']['symbol'] = 'Bs.'
    prices['ARS']['symbol'] = '$'
    prices['PEN']['symbol'] = '$'
    file.close()
    return prices




class UpdateBTCPrice():
    RUN_EVERY_SECS = 2

    def __init__(self):
        self.BTCPrice = PriceRetriever()
    

    def do(self):
        try:
            
            self.BTCPrice.ask()
            info = json.dumps(self.BTCPrice.getPriceInformation())
            file = open(os.path.join('./staticfiles', "BTCPrice.json"), "w")
            file.write(info)
            file.close()

        except Exception as e:
            print(">>", e)

        
        

x = UpdateBTCPrice()

while(True):
    x.do()
    time.sleep(x.RUN_EVERY_SECS)
