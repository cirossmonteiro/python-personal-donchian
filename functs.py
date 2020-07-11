import re
import json
import locale
from datetime import datetime
from donchian import donchianCeV
from dbhelper import DBHelper

locale.setlocale(locale.LC_ALL, '')
dc = donchianCeV()
db = DBHelper()

class Functions():

    def func_start(self):
        reply = ('Seja bem-vindo, investidor!\r\nEste bot já está pronto e irá te '
                 'atualizar diariamente sobre as ações que estão próximas de romper o '
                 'canal superior de Donchian e monitorar os papéis em carteira. O horário '
                 'programado padrão das mensagens é 10:25 (somente dias de semana), e não se esqueça de atualizar '
                 'seu portfólio! Para mais informações, utilize os comandos /help ou /comandos.\r\nBom trade!')
        return reply

    def func_help(self):
        reply = 'Em construção! Dúvidas? Contate o desenvolvedor @DanMMoreira!'
        return reply
    
    def func_com(self):
        i = 0
        comm = []
        #ciro: acho que se você colocar cada uma dessas linhas como um elemento de array, você atinge o mesmo objetivo sem ficar incrementando uma variável
        comm.insert(i, ('/donchian - Faz o bot analisar os gráficos e te mandar a mensagem automática na hora. Espere até 5 minutos para receber.'))
        i += 1
        comm.insert(i, ('/help - Explicações sobre para que serve o bot, como funciona e por quem foi desenvolvido.\r\n'))
        i += 1
        comm.insert(i, ('/comandos - Mostra esta lista de comandos.\r\n'))
        i += 1
        comm.insert(i, ('/adicionar_ativo - Adiciona ativos para a carteira, para que eles sejam monitorados ativamente. Exemplo: "PETR4". Mais detalhes em /help.\r\n'))
        i += 1
        comm.insert(i, ('/remover_ativo - Dá a opção de remover um ativo da carteira, para que ele deixe de ser monitorado. Mais detalhes em /help.\r\n'))
        i += 1
        comm.insert(i, ('/carteira - Mostra quais são os ativos que foram adicionados para serem monitorados pelo bot ativamente. Mais detalhes em /help.\r\n'))
        i += 1
        comm.insert(i, ('/portfolio - Atualiza o portfolio atual do investidor, que é utilizado para o cálculo do volume a ser comprado. Exemplo: "1435,97". Mais detalhes em /help.\r\n'))
        i += 1
        comm.insert(i, ('/info - Informa qual é o portfolio total registrado e qual hora do dia o bot está programado para enviar a mensagem automática.\r\n'))
        i += 1
        comm.insert(i, ('/hora - Modifica a hora a qual o bot irá enviar a mensagem automática. Exemplo: "18:45".'))
        reply = ''
        #ciro: acho que rola um join aqui, pra concatenar um número indefinido de strings
        for j in comm:
            reply = reply+j
        return reply

    def func_add_ativo(self, context, chat_id, dbname):
        #ciro: existe uma forma de você escrever um regex pra detectar [a-zA-Z] 4 vezes
        #só pesquisar alguma cheat sheet, que isso é bem 'básico' (regex é naturalmente difícil)
        y = re.match('^[a-zA-Z][a-zA-Z][a-zA-Z][a-zA-Z](\d|\d\d)$', context)
        if y: 
            db.add_stock(context.upper(), chat_id, dbname)
            return True
        else:
            return False

    def func_rem_ativo_A(self, chat_id, dbname):
        carteira = db.get_carteira(chat_id, dbname)
        if carteira == []:
            reply = 'Não há ativos na sua carteira! Consulte /comandos para saber como adicionar.'
        else:
            reply = self.build_keyboard(carteira)
        return reply

    def func_rem_ativo_B(self, context, chat_id, dbname):
        carteira = db.get_carteira(chat_id, dbname)
        if context in carteira:
            db.delete_stock(context, chat_id, dbname)
            return True
        else:
            return False
    
    def func_carteira(self, chat_id, dbname):
        carteira = db.get_carteira(chat_id, dbname)
        carteira = '\n'.join(carteira)
        if carteira == '':
            reply = 'A sua carteira está vazia! Veja em /comandos como adicionar ativos.'
        else:
            reply = 'A sua carteira atual é composta pelos seguintes ativos:\n'+carteira
        return reply

    def func_port(self, context, index, chat_id, dbname):
        if index == 2:
            port = '0'
            db.upd_port(port, chat_id, dbname)
            return 0
        else:
            y = re.match('^\d*((([,]|[.])(\d|\d\d)$)|$)', context)
            if y:
                valor = context.replace(',', '.') if context.rfind(',') else False
                valor = float(valor)
            else:
                return 1
            infos = db.get_info(chat_id, dbname)
            port = float(infos[0])
            if index == 0:
                port += valor
            elif index == 1:
                port -= valor
                if port < 0: return 2
            elif index == 3:
                port = valor
            port = '{:.2f}'.format(float(port))
            db.upd_port(port, chat_id, dbname)
            return 0

    def func_info(self, chat_id, dbname):
        infos = db.get_info(chat_id, dbname)
        port = locale.format('%1.2f', float(infos[0]), 1)
        hora = infos[1]
        reply = (f'Portfolio atual: R${port}\r\nHora programada: {hora}')
        return reply
    
    def func_hora(self, context, chat_id, dbname):
        y = re.match('^(([0-1][0-9])|([2][0-3]))[:][0-5][0-9]$', context)
        if y:
            db.upd_hora(context, chat_id, dbname)
            return True
        else:
            return False

    def build_keyboard(self, items):
        keyboard = [[item] for item in items]
        reply_markup = {'keyboard':keyboard, 'one_time_keyboard': True}
        k = json.dumps(reply_markup)
        return k
    
    compra_header = (' | ------ Compra ------ | \r\nStock | Vol | DUp | Close | DDown\r\nDist | Trend\r\n'
                     '<i>!!Os ativos em atenção romperam o canal superior nos últimos 3 dias! Cuidado!!\r\n\r\n</i>')

    def func_donchian(self, user, dbname, manual):
        result_Compra = dc.donch_Compra(user, dbname, manual)
        result_Carteira = dc.donch_Carteira(user, dbname)
        day_now = str(datetime.now().date())
        
        #ciro: isso de ficar comparando com int e com list parece ruim, deve ter uma forma melhor de controlar os valores da variável
        if result_Compra == 1:
            reply_Compra = 'Algo deu errado ao importar a lista de Small Caps.'
        elif result_Compra == []:
            reply_Compra = 'No momento, nenhum ativo está perto de romper o canal superior.\r\nRelaxe!'
        else:
            try:
                if result_Compra[0][8] != day_now:
                    data = result_Compra[0][8].split('-')
                    strdata = f'{data[2]}/{data[1]}/{data[0]}'
                    reply_Compra = (f'ATENÇÃO! Não foi possível atualizar a lista de Small Caps no momento. A lista utilizada foi do dia {strdata}.\r\n\r\n | ------ Compra ------ | \r\nStock | Vol | DUp | Close | DDown\r\nDist | Trend\r\n\r\n')
                else:
                    reply_Compra = self.compra_header
            except:
                reply_Compra = self.compra_header
            for item in result_Compra:
                item[2] = locale.format('%1.2f', item[2], 1)
                item[3] = locale.format('%1.2f', item[3], 1)
                item[4] = locale.format('%1.2f', item[4], 1)
                item[5] = '{:.2f}'.format(item[5])
                item[6] = '{:.2f}'.format(item[6][0])
                if item[7]:
                    reply_Compra = (reply_Compra + f'!!{item[0]} | {item[1]} | ${item[2]} | ${item[3]} | ${item[4]}\r\n'
                                                   f'<i>{item[5]}% | {item[6]}!!!!!</i>\r\n\r\n')
                else:
                    reply_Compra = (reply_Compra + f'{item[0]} | {item[1]} | ${item[2]} | ${item[3]} | ${item[4]}\r\n'
                                                   f'{item[5]}% | {item[6]}\r\n\r\n')

        if result_Carteira == 1:
            reply_Carteira = 'A sua carteira está vazia! Veja em /comandos como adicionar ativos.'
        else:
            reply_Carteira = (' | ------ Carteira ------ | \r\nStock | Close | DDown -> DDown(novo)\r\n\r\n')
            for item in result_Carteira:
                item[2] = locale.format('%1.2f', item[2], 1)
                item[3] = locale.format('%1.2f', item[3], 1)
                if item[0]:
                    item[4] = locale.format('%1.2f', item[4], 1)
                    reply_Carteira = (reply_Carteira + f'<i>!!{item[1]} | ${item[2]} | '
                                                       f'${item[3]} -> ${item[4]}!!</i>\r\n\r\n')
                else:
                    reply_Carteira = (reply_Carteira + f'{item[1]} | ${item[2]} | '
                                                       f'${item[3]}\r\n\r\n')
        return reply_Compra, reply_Carteira

    def upd_history(self, dbname):
        stockList_all = dc.gather_stock_list(dbname)
        if type(stockList_all) == tuple:
            stockList = stockList_all[0]
        else:
            stockList = stockList_all

        dc.gather_EOD(stockList)