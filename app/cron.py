import json
import requests
from django_cron import CronJobBase, Schedule
from C4H.settings import MEDIA_ROOT
import os
        

## Pair: BTCUSD, USDBTC, DASHUSD, etc
class PriceRetriever:
  def __init__(self):
    self.localbitcoins = {}
    self.gemini = {}
    self.bitinka = {}
    self.ripio = {}

  def ask(self):
    # print(requests.get('https://localbitcoins.com//bitcoinaverage/ticker-all-currencies/').content)
    self.localbitcoins = json.loads(requests.get('https://localbitcoins.com//bitcoinaverage/ticker-all-currencies/').content)
    self.gemini = json.loads(requests.get('https://api.gemini.com/v1/pubticker/btcusd').content)
    self.bitinka = json.loads(requests.get('https://www.bitinka.com/api/apinka/ticker?format=json').content)
    self.ripio = json.loads(requests.get('https://www.ripio.com/api/v1/rates/').content)

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


BTCPrice = PriceRetriever()

class UpdateBTCPrice(CronJobBase):
    RUN_EVERY_MINS = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'app.cron.UpdateBTCPrice'    # a unique code

    def do(self):
        global BTCPrice
        BTCPrice.ask()
        print(">>>>")
        print(os.path.join(MEDIA_ROOT, "BTCPrice"))
        file  = open(os.path.join(MEDIA_ROOT, "BTCPrice.json"), "w")
        info = json.dumps(BTCPrice.getPriceInformation())
        print(info)
        file.write(info)
        file.close()