# -*- coding: utf-8 -*-
import schedule
import time
import requests
import json
import configparser as cfg
import telegram.ext as tg
from functools import wraps
from telegram import Update, ParseMode, ReplyKeyboardRemove
from dbhelper import DBHelper
from functs import Functions


# ------- funcionamento do bot -------

db = DBHelper()
dbname = 'stocksDan.sqlite'
fc = Functions()
#ciro: percebi que você usa muito termo em inglês com palavra em português
#sugestão: usar apenas inglês, exceto termo mais técnico que se fosse traduzir poderia induzir ao erro
#exemplo: carteira deve poder sempre ser portfolio, ativo é asset, etc.
ADD_ATIVO_B, REM_ATIVO_B, PORTFOLIO_B, PORTFOLIO_C, HORA_B = range(5)
LIST_OF_ADMINS = [545699841]
BLACK_LIST = {
    395945106: 'Louis'
}

#ciro: falta ordem nas linhas, você mistura comandos, declarações de variáveis e 'defs'
#sugestão: recorrer ao uso de classe, até pra quebrar em mais de um arquivo
#código em python com 400 linhas é grande demais

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            response = 'Unauthorized access'
            context.bot.send_message(
                chat_id=user_id, 
                text=response,
            )
            return
        return func(update, context, *args, **kwargs)
    return wrapped

def read_token(config):
    parser = cfg.ConfigParser()
    parser.read(config)
    return parser.get('creds', 'token')

TOKEN = read_token('config.cfg')
wrapped_msg = {}
removeKeyboard = {'remove_keyboard':True}
RKR = json.dumps(removeKeyboard)
def send_msg(user, msg, msg_id, reply_markup):
    token = TOKEN
    url = (f'https://api.telegram.org/bot{token}/sendMessage?chat_id={user}&text={msg}&reply_to_message_id={msg_id}&reply_markup={reply_markup}&parse_mode=HTML')
    requests.get(url)

updater = tg.Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

def donchian_channel(user_id, manual=False):
    if user_id in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user_id, response, '', '')
        return
    message_Compra, message_Carteira = fc.func_donchian(user_id, dbname, manual)
    send_msg(user_id, message_Compra, '', '')
    send_msg(user_id, message_Carteira, '', '')

users_all = db.update(dbname)
if users_all:
    for item in users_all:
        user = item[0].replace('a', '', 1)
        infos = db.get_info(user, dbname)
        schedule.every().monday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
        schedule.every().tuesday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
        schedule.every().wednesday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
        schedule.every().thursday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
        schedule.every().friday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
    
schedule.every().monday.at('21:00').do(fc.upd_history, dbname=dbname)
schedule.every().tuesday.at('21:00').do(fc.upd_history, dbname=dbname)
schedule.every().wednesday.at('21:00').do(fc.upd_history, dbname=dbname)
schedule.every().thursday.at('21:00').do(fc.upd_history, dbname=dbname)
schedule.every().friday.at('21:00').do(fc.upd_history, dbname=dbname)

# ------- comandos -------

def admin_A(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user not in LIST_OF_ADMINS:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    admin_text = 'Qual opção?'


def atualizar():
    users = db.update(dbname)
    if users:
        for item in users:
            if item[1] == '1':
                user = item[0].replace('a', '', 1)
                infos = db.get_info(user, dbname)
                db.update_stop(user, dbname)
                schedule.clear(user)
                schedule.every().monday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
                schedule.every().tuesday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
                schedule.every().wednesday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
                schedule.every().thursday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)
                schedule.every().friday.at(infos[1]).do(donchian_channel, user_id=user).tag(user)

def start_(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')
    f_name = update.message.chat.first_name
    l_name = update.message.chat.last_name if update.message.chat.last_name else ''
    name = f'{f_name} {l_name}'
    username = update.message.chat.username

    admin_text = f'Usuário mandou:\nuser_id: {user}\nname: {name}\nusername: @{username}\n'
    send_msg(LIST_OF_ADMINS[0], admin_text, '', '')

    users = db.update(dbname)
    if users:
        for item in users:
            if str(user) == item[0].replace('a', '', 1):
                response = 'Você já deu o start! Tem algum problema? Consulte /comandos ou contate o @DanMMoreira.'
                wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
                return
                    
    schedule.every().monday.at('13:25').do(donchian_channel, user_id=user).tag(user)
    schedule.every().tuesday.at('13:25').do(donchian_channel, user_id=user).tag(user)
    schedule.every().wednesday.at('13:25').do(donchian_channel, user_id=user).tag(user)
    schedule.every().thursday.at('13:25').do(donchian_channel, user_id=user).tag(user)
    schedule.every().friday.at('13:25').do(donchian_channel, user_id=user).tag(user)

    db.setup(user, dbname)
    response = fc.func_start()
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']

def help_(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')

    response = fc.func_help()
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']

def commands(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')

    response = fc.func_com()
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']

def info(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')

    response = fc.func_info(user, dbname)
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']

def add_ativo_A(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')

    response = 'Digite o índice do ativo que deseja inserir na carteira ou clique em /cancelar.'
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
    return ADD_ATIVO_B

def add_ativo_B(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    message_id = update.message.message_id
    msg = update.message.text

    success = fc.func_add_ativo(msg, user, dbname)
    
    if success:
        response = 'O ativo '+msg+' foi adicionado com sucesso na carteira!'
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
        return tg.ConversationHandler.END
    else:
        response = 'Tente colocar o índice neste formato: "PETR4" ou clique em /cancelar.'
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
        return ADD_ATIVO_B

def rem_ativo_A(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')

    keyb = fc.func_rem_ativo_A(user, dbname)
    if not keyb.endswith('}'):
        response = keyb
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
        return tg.ConversationHandler.END
    else:
        response = 'Selecione abaixo um ativo para remover da carteira ou clique em /cancelar:'
        keyboard = keyb
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, keyboard]
        return REM_ATIVO_B

def rem_ativo_B(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')
    msg = update.message.text
    
    success = fc.func_rem_ativo_B(msg, user, dbname)
    if success:
        response = 'O ativo '+msg+' foi retirado da carteira com sucesso!'
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, RKR]
    else:
        cancel(update=update, context=context)
    return tg.ConversationHandler.END

def carteira(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')

    response = fc.func_carteira(user, dbname)
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']

def atlz_portfolio_A(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')
    response = 'Selecione uma das opções ou clique em /cancelar.'
    opts = [['Aumentar o valor'], ['Subtrair do valor'], ['Zerar'], ['Substituir o portfolio']]
    reply_markup = {'keyboard':opts, 'one_time_keyboard': True}
    k = json.dumps(reply_markup)
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, k]
    return PORTFOLIO_B

def atlz_portfolio_B(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')
    msg = update.message.text
    opts = ['Aumentar o valor', 'Subtrair do valor', 'Zerar', 'Substituir o portfolio']
    
    if msg in opts:
        context.user_data['selection'] = opts.index(msg)
        if msg == opts[2]:
            fc.func_port(None, 2, user, dbname)
            response = 'O portfolio foi zerado com sucesso!'
            wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, RKR]
            return tg.ConversationHandler.END
        else:
            response = 'Digite agora o valor ou clique em /cancelar:'
            wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, RKR]
            return PORTFOLIO_C
    
def atlz_portfolio_C(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')
    msg = update.message.text
    
    success = fc.func_port(msg, context.user_data['selection'], user, dbname)
    
    if success == 0:
        response = 'O portfolio foi atualizado com sucesso!'
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
        return tg.ConversationHandler.END
    elif success == 1:
        response = 'Tente colocar o valor neste formato (somente números): "1234,56" ou clique em /cancelar.'
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
        return PORTFOLIO_C
    elif success == 2:
        response = ('O portfolio não pode ficar negativo! Tente outro valor ou clique em /cancelar. Você também pode clicar em /info para consultar o valor de portfolio atual.')
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
        return PORTFOLIO_C

def atlz_hora_A(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')

    response = 'Digite a nova hora desejada (com acréscimo de 3 horas: se deseja 14:00, digite 17:00) ou clique em /cancelar.'
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
    return HORA_B

def atlz_hora_B(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')
    msg = update.message.text

    success = fc.func_hora(msg, user, dbname)
    
    if success:
        atualizar()
        response = 'A hora foi atualizada com sucesso!'
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
        return tg.ConversationHandler.END
    else:
        response = 'Tente colocar a hora neste formato: "06:18", "13:45" ou clique em /cancelar.'
        wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']
        return HORA_B

def unknown(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    if user in BLACK_LIST:
        response = 'User unauthorized.'
        send_msg(user, response, '', '')
        return
    message_id = update.message.message_id
    context.bot.sendChatAction(chat_id=user, action='typing')

    response = 'Comando inválido. Dê uma olhadinha na lista de /comandos !'
    wrapped_msg[len(wrapped_msg)+1] = [user, response, message_id, '']

def cancel(update: Update, context: tg.CallbackContext):
    response = 'Operação cancelada.'
    user = update.message.chat_id
    context.bot.sendChatAction(chat_id=user, action='typing')
    wrapped_msg[0] = [user, response, '', RKR]
    return tg.ConversationHandler.END

def trigger_donch(update: Update, context: tg.CallbackContext):
    user = update.message.chat_id
    context.bot.sendChatAction(chat_id=user, action='typing')
    manual = True
    donchian_channel(user, manual)

# ------- handlers -------

admin_handler = tg.CommandHandler('admin', admin_A)
start_handler = tg.CommandHandler('start', start_)
help_handler = tg.CommandHandler('help', help_)
commands_handler = tg.CommandHandler('comandos', commands)
info_handler = tg.CommandHandler('info', info)
carteira_handler = tg.CommandHandler('carteira', carteira)
donchian_handler = tg.CommandHandler('donchian', trigger_donch)
#cancel_handler = tg.CommandHandler('cancelar', cancel)

add_ativo_handler = tg.ConversationHandler(
    entry_points = [tg.CommandHandler('adicionar_ativo', add_ativo_A)],
    states = {ADD_ATIVO_B: [tg.CommandHandler('adicionar_ativo', add_ativo_A), 
                            tg.MessageHandler(~tg.Filters.command, add_ativo_B)]},
    fallbacks = [tg.MessageHandler(tg.Filters.command, cancel)]
)

rem_ativo_handler = tg.ConversationHandler(
    entry_points = [tg.CommandHandler('remover_ativo', rem_ativo_A)],
    states = {REM_ATIVO_B: [tg.CommandHandler('remover_ativo', rem_ativo_A), 
                            tg.MessageHandler(~tg.Filters.command, rem_ativo_B)]},
    fallbacks = [tg.MessageHandler(tg.Filters.command, cancel)]
)

atlz_hora_handler = tg.ConversationHandler(
    entry_points = [tg.CommandHandler('hora', atlz_hora_A)],
    states = {HORA_B: [tg.CommandHandler('hora', atlz_hora_A), 
                       tg.MessageHandler(~tg.Filters.command, atlz_hora_B)]},
    fallbacks = [tg.MessageHandler(tg.Filters.command, cancel)]
)

atlz_portfolio_handler = tg.ConversationHandler(
    entry_points = [tg.CommandHandler('portfolio', atlz_portfolio_A)],

    states = {
        PORTFOLIO_B: [tg.CommandHandler('portfolio', atlz_portfolio_A),
                      tg.MessageHandler(tg.Filters.regex('^(Aumentar o valor|Subtrair do valor|Zerar|Substituir o portfolio)$'),
                                        atlz_portfolio_B, pass_user_data=True)],

        PORTFOLIO_C: [tg.CommandHandler('portfolio', atlz_portfolio_A),
                      tg.MessageHandler(~tg.Filters.command, atlz_portfolio_C, pass_user_data=True)],
    },

    fallbacks = [tg.MessageHandler(tg.Filters.command, cancel)]
)

unkn_handler = tg.MessageHandler(tg.Filters.command, unknown)

def send_all_msg(update: Update, context: tg.CallbackContext):
    global wrapped_msg
    i = 0
    #ciro: se 'i' e 'wrapped_msg' não forem alterados em nenhuma iteração, é melhor usar for i in range (len(wrapped_msg)+1)
    while i <= len(wrapped_msg):
        #ciro: dict com key do tipo int? faz sentido nesse contexto?
        #sugestão: revisar o uso de dict aqui, tenta mudar pra list ou setar keys do tipo string
        #onde tiver: wrapped_msg[len(wrapped_msg)+1] talvez usar append
        if i in wrapped_msg:
            send_msg(wrapped_msg[i][0], wrapped_msg[i][1], wrapped_msg[i][2], wrapped_msg[i][3])
        i += 1
    wrapped_msg = {}

send_msg_handler = tg.MessageHandler(tg.Filters.all, send_all_msg)

dispatcher.add_handler(admin_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(commands_handler)
dispatcher.add_handler(info_handler)
dispatcher.add_handler(carteira_handler)
dispatcher.add_handler(donchian_handler)
#dispatcher.add_handler(cancel_handler)

dispatcher.add_handler(add_ativo_handler, group=5)
dispatcher.add_handler(rem_ativo_handler, group=4)
dispatcher.add_handler(atlz_portfolio_handler, group=3)
dispatcher.add_handler(atlz_hora_handler, group=2)

dispatcher.add_handler(send_msg_handler, group=500)
#dispatcher.add_handler(unkn_handler)

# ------- fim -------

updater.start_polling()

while True:
    schedule.run_pending()
    time.sleep(1)
