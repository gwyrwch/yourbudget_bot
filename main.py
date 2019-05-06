import io

import telebot
from PIL import Image
import requests
import json

with open('settings.json') as sett:
    all_settings = json.loads(sett.read())

backend_url = all_settings['backend_url']
token = all_settings['token']
bot = telebot.TeleBot(token)


@bot.message_handler(content_types=['photo'])
def get_photo_messages(message):
    photo_id = bot.get_file(message.photo[-1].file_id)
    photo_in_bytes = bot.download_file(photo_id.file_path)

    resp = requests.post(
        url=backend_url + '/save_receipt',
        data={
            'telegram_username': message.from_user.username
        },
        files={
            photo_id.file_path: photo_in_bytes
        }
    )

    if resp.status_code == 200:
        bot.reply_to(message, 'Ваш чек успешно сохранен')
    else:
        bot.reply_to(message, 'Извините, что-то пошло не так:\n' + resp.text)


@bot.message_handler(content_types=['document'])
def get_document_from_message(message):
    # todo: end with files  
    # doc_id = bot.get_file(message.file_id)
    pass


@bot.message_handler(commands=['start'])
def start(message):
    print(message)
    try:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Добро пожаловать в yourbudget — твой финансовый помощник.\n\n'
                 'С помощью этого бота ты сможешь сохранять свои походы в магазины, кафе, кинотеатры и так далее. '
                 'Не забудь указать свой профиль в telegram в профиле yourbudget, чтобы мы могли найти информацию о тебе!\n\n'
                 'Чтобы добавить свой новый чек, просто отправь нам фотографию или воспользуйся командой /newtrip, чтобы ввести данные вручную.\n\n'
                 'Постарайся, чтобы на фотографии не было ничего лишнего, а текст был хорошо виден. '
                 'Но не волнуйся, если я что-то не разгляжу, ты сможешь исправить это в своем личном кабинете.'
        )
    except:
        pass


#         markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
#         markup.add('Male', 'Female')
#         msg = bot.reply_to(message, 'What is your gender', reply_markup=markup)

# bot.register_next_step_handler(msg, process_age_step)


bot.polling(none_stop=True, interval=0)

