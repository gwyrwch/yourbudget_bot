import io

import telebot
from PIL import Image
import requests
import json
from datetime import datetime

with open('settings.json') as sett:
    all_settings = json.loads(sett.read())

backend_url = all_settings['backend_url']
token = all_settings['token']
bot = telebot.TeleBot(token)



@bot.message_handler(content_types=['photo', 'document'])
def get_photo_messages(message):
    if message.content_type == 'document':
        photo_id = bot.get_file(message.document.file_id)
    else:
        photo_id = bot.get_file(message.photo[-1].file_id)
    photo_in_bytes = bot.download_file(photo_id.file_path)

    resp = requests.post(
        url=backend_url + '/save_receipt',
        data={
            'telegram_username': message.from_user.username,
            'save': False
        },
        files={
            photo_id.file_path: photo_in_bytes
        }
    )

    if resp.status_code == 200:
        bot.reply_to(message, 'Ваш чек успешно сохранен')
    else:
        bot.reply_to(message, 'Извините, что-то пошло не так:\n' + resp.text)


# @bot.message_handler(content_types=['document'])
# def get_document_from_message(message):
#     # todo: end with files
#
#     doc_id = bot.get_file(message.document.file_id)
#     photo_in_bytes = bot.download_file(doc_id.file_path)
#
#     pass


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


trip = {}


def save_trip(telegram_username, uid):
    data = {
        'telegram_username': telegram_username,
        'trip': trip
    }

    resp = requests.post(
        url=backend_url + '/save_trip_manual',
        json=data
    )
    trip.clear()

    if resp.status_code == 200:
        bot.send_message(chat_id=uid, text='Ваш чек успешно сохранен')
    else:
        bot.send_message(chat_id=uid, text='Извините, что-то пошло не так:\n' + resp.text)


@bot.message_handler(commands=['newtrip'])
def get_name_of_shop(message):
    try:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Сейчас тебе необходимо будет ввести все необходимое, чтобы зарегистрировать твой поход в магазин.\n'
                 'Если ты что-то ввел неправильно,'
                 'Введите название магазина:'
        )
        bot.register_next_step_handler(message, get_trip_date)
    except:
        pass


def get_trip_date(message):
    trip['name_of_shop'] = message.text
    try:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Введите дату похода в магазин в формате yyyy-mm-dd:'
        )
        bot.register_next_step_handler(message, get_receipt_amount)
    except:
        pass


def get_receipt_amount(message):
    try:
        datetime.strptime(message.text, '%Y-%m-%d')
    except ValueError:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Дата введена неверно. Введите дату похода в магазин в формате yyyy-mm-dd:'
        )
        bot.register_next_step_handler(message, get_receipt_amount)
        return

    trip['trip_date'] = message.text
    try:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Введите сумму в чеке:'
        )
        bot.register_next_step_handler(message, get_receipt_discount)
    except:
        pass


def get_receipt_discount(message):
    try:
        trip['receipt_amount'] = float(message.text)
    except ValueError:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Сумма в чекке введена неверно. Попробуйте ещё раз:'
        )
        bot.register_next_step_handler(message, get_receipt_discount)
        return

    try:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Введите полученную скидку:'
        )
        bot.register_next_step_handler(message, get_address)
    except:
        pass


def get_address(message):
    try:
        trip['receipt_discount'] = float(message.text)
    except ValueError:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Скидка введена неверно. Попробуйте ещё раз:'
        )
        bot.register_next_step_handler(message, get_address)
        return

    try:
        chat_id = message.from_user.id
        bot.send_message(
            chat_id=chat_id,
            text='Введите адрес магазина:'
        )
        bot.register_next_step_handler(message, get_category)
    except:
        pass


CATEGORIES = (
    'Общепит',
    'Продукты',
    'Техника',
    'Одежда',
    'Развлечения',
    'Здоровье',
    'Транспорт',
    'Услуги',
    'Иное'
)


def get_category(message):
    trip['address'] = message.text

    try:
        chat_id = message.from_user.id

        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(*CATEGORIES)

        bot.send_message(
            chat_id=chat_id,
            text='Выберите категорию из предложенных:',
            reply_markup=markup
        )
        bot.register_next_step_handler(message, ask_full_list)
    except:
        pass
        #
        # markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        # markup.add('Male', 'Female')
#         msg = bot.reply_to(message, 'What is your gender', reply_markup=markup)

# bot.register_next_step_handler(msg, process_age_step)


def ask_full_list(message):
    trip['category'] = message.text

    try:
        chat_id = message.from_user.id

        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Да', 'Нет')

        bot.send_message(
            chat_id=chat_id,
            text='Желаете ли вы добавить полный список покупок?',
            reply_markup=markup
        )
        bot.register_next_step_handler(message, fork_full_list)
    except:
        pass

def fork_full_list(message):
    resp = message.text
    if resp == 'Да':
        try:
            chat_id = message.from_user.id

            bot.send_message(
                chat_id=chat_id,
                text='В таком случае отправьте мне полный список покупок в формате:\n'
                     'наименование_1 цена_1\n'
                     'наименование_2 цена_2\n'
                     '...\n'
                     'наименование_n цена_n'
            )
            bot.register_next_step_handler(message, get_full_list)
        except:
            pass
    else:
        save_trip(message.from_user.username, message.from_user.id)


def get_full_list(message):
    text = message.text
    lines = text.splitlines()

    list_of_purchases = []

    for l in lines:
        try:
            name_of_product, price = l.rsplit(' ', 1)
            price = float(price)

            list_of_purchases.append(
                {
                    'name_of_product': name_of_product,
                    'price': price
                }
            )
        except:
            chat_id = message.from_user.id
            bot.send_message(
                chat_id=chat_id,
                text='С форматом в этой строке - {}, что-то не так. Попробуйте ещё раз:'.format(l)
            )
            bot.register_next_step_handler(message, get_full_list)
            return

    trip['list_of_purchases'] = list_of_purchases
    save_trip(message.from_user.username, message.from_user.id)


bot.polling(none_stop=True, interval=0)

