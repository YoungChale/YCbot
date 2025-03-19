import telebot
from telebot import types
import config
import database
import yookassa_integration as yookassa
from datetime import datetime

bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("Админ меню"))
    welcome_text = ("👋 <b>Привет! Отправь ссылку на бит или напиши его название, чтобы найти его в базе данных.</b>\n"
                    "- Этот бот был создан для облегчения покупки битов, без лишних диалогов. "
                    "Но если у тебя остались вопросы пиши их мне в лс <a href='https://t.me/prodyoungchale'>сюда</a>")
    try:
        with open('starphoto.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, parse_mode='HTML', reply_markup=markup)
    except FileNotFoundError:
        bot.send_message(message.chat.id, "Изображение не найдено.\n\n" + welcome_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Админ меню")
def admin_menu(message):
    if str(message.from_user.id) == str(config.ADMIN_USER_ID):
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton("Загрузить бит"), types.KeyboardButton("Статистика пользователей"), types.KeyboardButton("Удалить бит"), types.KeyboardButton("Назад"))
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этому меню.")

@bot.message_handler(func=lambda message: message.text == "Удалить бит")
def admin_delete_beat(message):
    if str(message.from_user.id) == str(config.ADMIN_USER_ID):
        beats = database.get_all_beats()
        if beats:
            markup = types.InlineKeyboardMarkup()
            for beat in beats:
                markup.add(types.InlineKeyboardButton(beat[1], callback_data=f"delete_{beat[0]}"))
            bot.send_message(message.chat.id, "Выберите бит для удаления:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Нет доступных битов для удаления.")
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этому меню.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def confirm_delete_beat(call):
    beat_id = call.data.split('_')[1]
    beat = database.get_beat_by_id(beat_id)
    if beat:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Да", callback_data=f"confirm_delete_{beat_id}"))
        markup.add(types.InlineKeyboardButton("Нет", callback_data="cancel_delete"))
        bot.send_message(call.message.chat.id, f"Вы уверены, что хотите удалить бит '{beat[1]}'?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
def delete_beat(call):
    beat_id = call.data.split('_')[2]
    database.delete_beat_by_id(beat_id)
    bot.send_message(call.message.chat.id, "Бит успешно удалён!")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
def cancel_delete_beat(call):
    bot.send_message(call.message.chat.id, "Удаление бита отменено.")

@bot.message_handler(func=lambda message: message.text == "Загрузить бит")
def admin_upload_beat(message):
    if str(message.from_user.id) == str(config.ADMIN_USER_ID):
        bot.send_message(message.chat.id, "Отправь ссылку на бит.")
        bot.register_next_step_handler(message, get_beat_link)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этому меню.")

def get_beat_link(message):
    link = message.text
    bot.send_message(message.chat.id, "Отправь название бита.")
    bot.register_next_step_handler(message, get_beat_name, link)

def get_beat_name(message, link):
    name = message.text
    bot.send_message(message.chat.id, "Отправь ссылку на .wav файл.")
    bot.register_next_step_handler(message, get_wav_link, name, link)

def get_wav_link(message, name, link):
    wav_link = message.text
    bot.send_message(message.chat.id, "Отправь ссылку на Trackout файл.")
    bot.register_next_step_handler(message, get_trackout_link, name, link, wav_link)

def get_trackout_link(message, name, link, wav_link):
    trackout_link = message.text
    database.add_beat(name, link, wav_link, trackout_link)
    bot.send_message(message.chat.id, "🆗 Бит успешно загружен! Переход в главное меню.")
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == "Статистика пользователей")
def show_statistics(message):
    if str(message.from_user.id) == str(config.ADMIN_USER_ID):
        transactions = database.get_last_transactions()
        response = "Последние 10 покупок:\n"
        for t in transactions:
            response += f"User: {t[1]}, Beat ID: {t[2]}, License: {t[3]}, Amount: {t[4]}, Date: {t[5]}\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этому меню.")

@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    beat = database.find_beat_by_link(message.text)
    if beat:
        bot.send_chat_action(message.chat.id, 'typing')
        markup = types.InlineKeyboardMarkup()
        wav_payment_url, wav_payment_id = yookassa.create_payment(999, f"wav_{beat[0]}", config.YOOKASSA_REDIRECT_URI)
        trackout_payment_url, trackout_payment_id = yookassa.create_payment(2499, f"trackout_{beat[0]}", config.YOOKASSA_REDIRECT_URI)
        exclusive_payment_url, exclusive_payment_id = yookassa.create_payment(6999, f"exclusive_{beat[0]}", config.YOOKASSA_REDIRECT_URI)
        database.update_payment_ids(beat[0], wav_payment_id, trackout_payment_id, exclusive_payment_id)
        markup.add(types.InlineKeyboardButton("Wav – 999₽", url=wav_payment_url))
        markup.add(types.InlineKeyboardButton("Trackout – 2499₽", url=trackout_payment_url))
        markup.add(types.InlineKeyboardButton("Exclusive – 6999₽", url=exclusive_payment_url))
        markup.add(types.InlineKeyboardButton("Проверить оплату", callback_data=f"check_{beat[0]}"))
        try:
            with open('thisbeat.jpg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=f"<b>{beat[1]}</b>\n\n<i>При успешной оплате ты получишь ссылку на скачивание нужного тебе файла ❤️</i>", parse_mode='HTML', reply_markup=markup)
        except FileNotFoundError:
            bot.send_message(message.chat.id, f"<b>{beat[1]}</b>\n\n<i>При успешной оплате ты получишь ссылку на скачивание нужного тебе файла ❤️</i>", parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "🚫 Упс! Не нашёл такого бита или ссылка неправильная 😔. Попробуй найти бит по названию.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_payment(call):
    beat_id = call.data.split('_')[1]
    beat = database.get_beat_by_id(beat_id)

    if len(beat) < 8:
        bot.send_message(call.message.chat.id, "Ошибка: данные о платеже отсутствуют.")
        return

    # Проверяем платежи для всех типов лицензий
    wav_status, wav_description = yookassa.check_payment_status(beat[5]) if beat[5] else (None, None)
    trackout_status, trackout_description = yookassa.check_payment_status(beat[6]) if beat[6] else (None, None)
    exclusive_status, exclusive_description = yookassa.check_payment_status(beat[7]) if beat[7] else (None, None)

    if wav_status == "succeeded":
        bot.send_message(call.message.chat.id, f"🥳 Оплата успешно проведена! Вот ваша ссылка для скачивания WAV файла:\n{beat[3]}")
    elif trackout_status == "succeeded":
        bot.send_message(call.message.chat.id, f"🥳 Оплата успешно проведена! Вот ваша ссылка для скачивания Trackout файла:\n{beat[4]}")
    elif exclusive_status == "succeeded":
        database.delete_beat_by_id(beat_id)
        bot.send_message(call.message.chat.id, f"🥳 Оплата успешно проведена! Вот ваши ссылки для скачивания:\nWAV: {beat[3]}\nTrackout: {beat[4]}\n\nЭтот бит был продан и удален из базы данных.")
    else:
        bot.send_message(call.message.chat.id, "😤 Ожидается оплата.")

if __name__ == '__main__':
    database.initialize_db()
    database.migrate_db()
    bot.polling(none_stop=True)