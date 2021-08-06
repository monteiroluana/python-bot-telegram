import os, sys, logging, django, requests, datetime

from decouple import config

from telegram import (Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler )


# Django env
os.environ['DJANGO_SETTINGS_MODULE'] = 'djproject.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true" # jupyter bug
django.setup()
from djproject.core import models

# Logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token
BOT_TOKEN = config('BOT_TOKEN')
OPENWEATHERMAP_TOKEN = config('OPENWEATHERMAP_TOKEN')
###

def start(update: Update, context: CallbackContext) -> None:
    if update.callback_query: 
        update = update.callback_query
    
    user = update.message.from_user
    logger.info(f"name of user is {user.first_name}")
    obj, created = models.Notification.objects.get_or_create( chat_id=update.message.chat.id, first_name=user.first_name, last_name=user.last_name)


    update.message.reply_text('Envie a sua localização e veja como está a temperatura.')


def about(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('''
        Esse é um projeto experimental de iniciação ao Telegram Chat Bot\n\nAutor: Luana Monteiro\n[Github](https://github.com/monteiroluana)\n[Linkedin](https://www.linkedin.com/in/luana-monteiro-8040519b/)\nEmail: monteiro.lpereira@gmail.com\n\nFonte dos dados climáticos: openweathermap
    ''',  parse_mode= 'Markdown')


def location(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    location = update.message.location
    logger.info(f"Location of {user.first_name}:  {location.latitude} / {location.longitude}")
    
    obj, created = models.Notification.objects.get_or_create( chat_id=update.effective_user.id )
    obj.latitude = location.latitude
    obj.longitude = location.longitude
    obj.last_message_id = update.message.message_id
    obj.save()   

    # delete message
    context.bot.delete_message(chat_id=obj.chat_id, message_id=obj.last_message_id)

    options(update, context)


def options(update: Update, context: CallbackContext) -> None:
    if update.callback_query: 
        update = update.callback_query

    user = update.message.from_user
    logger.info(f"user {user.first_name} choose option")
    # obj, created = models.Notification.objects.get_or_create( chat_id=update.effective_user.id, first_name=user.first_name, last_name=user.last_name)

    keyboard = [
        [
            InlineKeyboardButton("Temperatura", callback_data='temp'),
            InlineKeyboardButton("Chuva", callback_data='rain'),
            InlineKeyboardButton("Mais", callback_data='more'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('A sua localização foi enviada com sucesso\n\nEscolha uma das opções:', reply_markup=reply_markup)


def options_rain(update: Update, context: CallbackContext) -> None:
    if update.callback_query: 
        update = update.callback_query

    user = update.message.from_user
    logger.info(f"user {user.first_name} choose option to rain")
  
    keyboard = [
        [
            InlineKeyboardButton("Diária", callback_data='daily'),
            InlineKeyboardButton("Acumulado", callback_data='aggragate'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Escolha uma das opções:', reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    query.answer()
    choice = query.data

    obj = models.Notification.objects.get( chat_id=query.message.chat.id )
    url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}".format(obj.latitude, obj.longitude, OPENWEATHERMAP_TOKEN)
    data = requests.get(url)
    response = data.json()

    city = response['name']
    contry = response['sys']['country']
    temp = round(response['main']['temp'] - 273.15, 2)
    humidity = response['main']['humidity']
    clouds = response['clouds']['all']
    

    if choice == 'more':
        query.edit_message_text(text=f'''*Cidade*: {city}\n*País*: {contry}\n*Temp*: {temp}ºC\n*Nuvem*: {clouds}%\n*Humididade*: {humidity}%
        ''',  parse_mode='Markdown')
        options(update, context)
            
    if choice == 'temp':
        query.edit_message_text(text=f"A temperatura atual é:  {temp}ºC")
        options(update, context)

    if choice == 'rain':
        context.bot.delete_message(chat_id=obj.chat_id, message_id=query.message.message_id)
        options_rain(update, context)

    if choice == 'daily':
        query.edit_message_text(text=f"Digite uma data no formato DD/MM/AAAA")
        obj.last_command= 'daily-rain'
        obj.last_message_id = query.message.message_id
        obj.save()
        
    if choice == 'aggragate':
        query.edit_message_text(text=f"Digite uma data no formato DD/MM/AAAA")
        obj.last_command= 'aggragate-rain'
        obj.last_message_id = query.message.message_id
        obj.save()


def daily_rain(update: Update, context: CallbackContext, date) -> None:
    user = update.message.from_user    
    obj = models.Notification.objects.get( chat_id=update.effective_user.id )
    print(type(date), date)
    body = {
        "date_range":{
            "from": date,
            "to":date,
        },
        "poi":{
            "lat":obj.latitude,
            "lon":obj.longitude,
        }
    }

    data = requests.post("http://127.0.0.1:8000/api/data/weather/rain/daily")
    response = data.json()
    print(data)

    update.message.reply_text(date)



def only_text(update: Update, context: CallbackContext) -> None:   
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    print('only_text >> ', update.message.message_id,'\t',  update.message.text)
    # user = update.message.from_user
    obj = models.Notification.objects.get( chat_id=update.effective_user.id )
    obj.last_command
   

    text = update.message.text

    if obj.last_command in ('daily-rain', 'aggregate-rain'):
        try:
            date = datetime.datetime.strptime(text, "%d/%m/%Y").strftime("%Y-%m-%d")
            
            if obj.last_command == 'daily-rain': daily_rain(update, context, date)
            

            options(update, context) 

        except ValueError as e:
            update.message.reply_text(f'Ops, alguma coisa não está certa!\nVocê digitou: *{text}*\n\nPor favor sertifique-se que as datas informadas seguem o formato DD-MM-AAAA.\n\n Exemplo: 01/02/2021', parse_mode= 'Markdown')
            print('value error >> ', update.message.message_id,'\t',  update.message.text)
            print(update)
            print()

            obj.last_message_id = update.message.message_id
            obj.save()    
    
            

def main():
    # Create the Updates and pass it your bot's token 
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    # Commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('about', about))
    dispatcher.add_handler(MessageHandler(Filters.location, location))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, only_text))

    
    # Start the Bot
    updater.start_polling()
    updater.idle()
 

if __name__ == '__main__':
    main()