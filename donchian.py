import requests
import re
import locale
import time as tm
import pickle
import numpy as np
import yfinance as yf
from sklearn.linear_model import LinearRegression
from math import floor
from datetime import datetime, timedelta, time
from bs4 import BeautifulSoup
from dbhelper import DBHelper

db = DBHelper()

class donchianCeV:

    def avglist(self, num):
        #ciro: procura pela função nativa 'sum' do python - assim que você vir você
        sumOfNumbers = 0
        for t in num:
            #ciro: mesmo sem usar 'sum', poderia ter feito sumOfNumbers += t
            sumOfNumbers = sumOfNumbers + t

        avg = sumOfNumbers / len(num)
        return avg

    def save_obj(self, obj, name):
        with open('obj/'+ name + '.pkl', 'wb+') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def load_obj(self, name):
        with open('obj/' + name + '.pkl', 'rb') as f:
            return pickle.load(f)

    def gather_stock_list(self, dbname):
        stockList = []
        trials = 1
        #ciro: você está comparando dois objetos e isso pode dar errado em algumas circunstâncias (outras linguagens também)
        #sugiro trocar 'stockList == []' por len(stockList) == 0, porque você garante que a variável sempre seja uma list
        while stockList == [] and trials < 300:
            page = requests.get('http://bvmf.bmfbovespa.com.br/indices/ResumoCarteiraTeorica.aspx?Indice=SMLL&idioma=pt-br')
            #ciro: gostei de ver usando BS
            resultado = BeautifulSoup(page.content, 'html.parser')
            for stock in resultado.findAll('td', {'class': 'rgSorted'}):
                stockText = stock.findAll(text=True)
                stockText = [x for x in stockText if x != '\n']
                stockList.extend(stockText)
            trials += 1
            #ciro: isso é um pouco arbitrário, mas esperar apenas 1 segundo pra tentar de novo parece rápido demais
            #a própria request deve levar mais tempo que isso - eu colocaria 5 ou 10 segundos de espera, mas é arbitrário, de fato
            tm.sleep(1)
        day_nowDB = str(datetime.now().date())
        #ciro: idem acima
        if stockList == []:
            stockListRaw = db.get_stocks("SMALL", dbname)
            stockList.extend(stockListRaw[0][0].split(' '))
        else:
            stocks = ' '.join(stockList)
            db.upd_stocks(stocks, day_nowDB, dbname)
        #ciro: primeira vez na vida que vejo esse locals(), não conhecia
        #procurei saber do que se tratava, recomendo fortemente não usá-lo havendo alternativa
        #sugestão: 'stockListRaw' é definido no if-else acima, então aproveita a mesma estrutura
        #e coloca esses dois returns acima também.
        if 'stockListRaw' in locals():
            return stockList, stockListRaw
        else:
            return stockList

    def gather_EOD(self, stockList):
        day_before = str(datetime.now().date()-timedelta(days=320))
        day_now = str(datetime.now().date()+timedelta(days=2))
        i = 1
        #ciro: esse nome de variável é ruim porque se aproxima de 'reserved words' (google it)
        iF = len(stockList)
        k = 1
        history_all = {}
        close_all = {}
        jump = 10
        while i <= iF:
            m = i
            frstocks = []
            j = k*jump
            while i <= j and i <= iF:
                frstocks.append(f'{stockList[i-1]}.SA')
                i += 1
            frstocksY = ' '.join(frstocks)
            try:
                dataY = yf.download(frstocksY, interval='1d', auto_adjust=True, start=day_before, end=day_now)
                data = dataY.to_dict()
                if len(frstocks) == 1:
                    stockhigh = [float('%.2f' % data['High'][x]) for x in data['High']]
                    stocklow = [float('%.2f' % data['Low'][x]) for x in data['Low']]
                    avg_list = [stockhigh, stocklow]
                    stockavg = [(x+y)/2 for x,y in zip(*avg_list)]
                    #ciro: 'frstocks[0].split('.')[0]' aparece 3x nas próximas 6 linhas sem sofrer modificação
                    #sugestão: criar uma variavel, setar 'frstocks[0].split('.')[0]' e substituir
                    history_all[frstocks[0].split('.')[0]] = [stockhigh, stocklow, stockavg]
                    closing = float('%.2f' % dataY['Close'][-1])
                    if closing == 0 or np.isnan(closing):
                        close_all[frstocks[0].split('.')[0]] = float('%.2f' % dataY['Close'][-2])
                    else:
                        close_all[frstocks[0].split('.')[0]] = closing
                else:
                    for stock in frstocks:
                        stockhigh = [float('%.2f' % data[('High', stock)][x]) for x in data[('High', stock)]]
                        stocklow = [float('%.2f' % data[('Low', stock)][x]) for x in data[('Low', stock)]]
                        avg_list = [stockhigh, stocklow]
                        stockavg = [(x+y)/2 for x,y in zip(*avg_list)]
                        #ciro: mesma coisa relatada acima
                        history_all[stock.split('.')[0]] = [stockhigh, stocklow, stockavg]
                        closing = float('%.2f' % dataY[('Close', stock)][-1])
                        if closing == 0 or np.isnan(closing):
                            close_all[stock.split('.')[0]] = float('%.2f' % dataY[('Close', stock)][-2])
                        else:
                            close_all[stock.split('.')[0]] = closing
                k += 1
            except:
                i = m
                tm.sleep(1)
        self.save_obj(history_all, 'history')
        self.save_obj(close_all, 'close')
        return history_all, close_all

    def donch_Compra_func(self, user, dbname, sameday, manual):
        resultado_final = []
        day_before_close = str(datetime.now().date()-timedelta(days=4))
        day_now = str(datetime.now().date()+timedelta(days=2))
        
        stockList_all = self.gather_stock_list(dbname)
        if type(stockList_all) == tuple:
            stockList = stockList_all[0]
            #ciro: eu não vi essa variável 'stockListRaw' sendo utilizada dentro dessa função
            #se for verdade, melhor não extraí-la aqui
            stockListRaw = stockList_all[1]
        else:
            stockList = stockList_all

        #ciro: por que sentiu necessidade de try-except aqui?
        #quem vir isso não vai entender porque pode dar erro
        #sugestão: controlar melhor o retorno dos métodos 'self.load_obj' e 'self.gather_EOD'
        try:
            history_all = self.load_obj('history')
        except:
            history_all, close_all = self.gather_EOD(stockList)

        if not (datetime.now().time() >= time(13,0) \
                and datetime.now().time() < time(21,0)):
            close_all = self.load_obj('close')
        else:
            i = 1
            iF = len(stockList)
            k = 1
            close_all = {}
            jump = 15
            while i <= iF:
                m = i
                frstocks = []
                j = k*jump
                while i <= j and i <= iF:
                    frstocks.append(f'{stockList[i-1]}.SA')
                    i += 1
                frstocksY = ' '.join(frstocks)
                try:
                    dataY = yf.download(frstocksY, interval='1d', auto_adjust=True, start=day_before_close, end=day_now)
                    data = dataY.to_dict()
                    if len(frstocks) == 1:
                        closing = float('%.2f' % dataY['Close'][-1])
                        if closing == 0 or np.isnan(closing):
                            close_all[frstocks[0].split('.')[0]] = float('%.2f' % dataY['Close'][-2])
                        else:
                            close_all[frstocks[0].split('.')[0]] = closing
                    else:
                        for stock in frstocks:
                            closing = float('%.2f' % dataY[('Close', stock)][-1])
                            if closing == 0 or np.isnan(closing):
                                close_all[stock.split('.')[0]] = float('%.2f' % dataY[('Close', stock)][-2])
                            else:
                                close_all[stock.split('.')[0]] = closing
                    k += 1
                except:
                    i = m
                    tm.sleep(1)

        # ---------------------------- Analysis method goes here ---------------------------------
        
        return resultado_final
    
    def donch_Carteira(self, user, dbname):
        #ciro: é desnecessário usar if-else se for apenas setar booleano
        #sugestão: sameday = datetime.now().time() <= time(13,21) or datetime.now().time() > time(21,0))
        if (datetime.now().time() <= time(13,21) \
            or datetime.now().time() > time(21,0)):
            sameday = True
        else:
            sameday = False
        carteira = db.get_carteira(user, dbname)
        if carteira == []:
            resultado_final = 1
        else:
            resultado_final = []
            
            day_before = str(datetime.now().date()-timedelta(days=55))
            day_now = str(datetime.now().date()+timedelta(days=2))

            #13 = ultimo item da lista de stocks
            i = 1 #1-13
            iF = len(carteira)
            k = 1 #1-3
            history_all = {}
            close_all = {}
            jump = 10
            while i <= iF:
                m = i
                frstocks = []
                j = k*jump
                while i <= j and i <= iF:
                    frstocks.append(f'{carteira[i-1]}.SA')
                    i += 1
                frstocksY = ' '.join(frstocks)
                try:
                    dataY = yf.download(frstocksY, interval='1d', auto_adjust=True, start=day_before, end=day_now)
                    data = dataY.to_dict()
                    if len(frstocks) == 1:
                        stocklow = [float('%.2f' % data['Low'][x]) for x in data['Low']]
                        history_all[frstocks[0].split('.')[0]] = stocklow
                        closing = float('%.2f' % dataY['Close'][-1])
                        if closing == 0 or np.isnan(closing):
                            close_all[frstocks[0].split('.')[0]] = float('%.2f' % dataY['Close'][-2])
                        else:
                            close_all[frstocks[0].split('.')[0]] = closing
                    else:   
                        for stock in frstocks:
                            stocklow = [float('%.2f' % data[('Low', stock)][x]) for x in data[('Low', stock)]]
                            history_all[stock.split('.')[0]] = stocklow
                            closing = float('%.2f' % dataY[('Close', stock)][-1])
                            if closing == 0 or np.isnan(closing):
                                close_all[stock.split('.')[0]] = float('%.2f' % dataY[('Close', stock)][-2])
                            else:
                                close_all[stock.split('.')[0]] = closing
                    k += 1
                except:
                    i = m
                    tm.sleep(1)
                    
        # ---------------------------- Analysis method goes here ---------------------------------
        #ciro: suponho que aqui fosse o núcleo da metodologia
        #sugestão: pensa numa forma de isolar a metodologia não apenas como trecho de código
        #mas como um módulo do python mesmo - basta copiar-colar um (ou mais) arquivo pro código funcionar
        return resultado_final

    def donch_Compra(self, user, dbname, manual):
        if (datetime.now().time() <= time(10,21) \
            or datetime.now().time() > time(18,0)):
            sameday = True
        else:
            sameday = False
        analysis = self.donch_Compra_func(user, dbname, sameday, manual)
        return analysis
