import os
import re
import logging
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота (замените на ваш)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Ключевые слова для активации бота
KEYWORDS = ["фт", "финтетрис", "ФТ", "финансовый тетрис"]

# Состояния разговора
STEP0, STEP1, STEP2, STEP3, STEP4, GET_PHONE, GET_NAME = range(7)

# Тексты сообщений
hello = "Хотите получить бесплатный чек лист 7 вопросов себе для создания капитала или узнать подробнее о курсе Финансовый тетрис Кликните на подходящую кнопку ниже:"
book = "Чек лист 7 вопросов себе для создания капитала поможет вам научиться:- создавать капитал 💰;- получать доход от капитала;- грамотно управлять им;- и защищать капитал.Чтобы его получить, кликните на кнопку ниже 👇"
message = "Наверняка после прочтения у вас в мыслях уже начинает потихоньку зарождаться личный инвестиционный план.Чтобы выстроить свою правильную финансовую модель и обеспечить комфортную жизнь себе и своим потомкам, нужно погрузиться в эту тему с головой. 👨‍💻📝Об этом максимально подробно и попунктам мы рассказываем на курсеФинансовый тетрис- находим дополнительные источники дохода;- выбираем стратегии финансового роста;- создаём систему планомерных накоплений- выстраиваем щит от потерь.Хотите получить бесплатнуюконсультацию от эксперта?"
refuseMessage = "Хорошо, нажмите кнопку ниже, как только прочитаете его 👇Я дам вам еще немного информации в дополнение к нему."
beginQuiz = "Ответьте на 3 вопроса ниже и эксперт, работающий по технологии «Финансовый тетрис» проконсультирует вас 👇"
firstQuestion = "Выберите ответы, которые подходят вам:"
firstAnswer = [
    "Есть план финансового развития на 5 лет",
    "Я не планирую долгосрочно",
    "Моих ресурсов хватает только на месяц",
    "Действую по обстоятельствам",
]
secondQuestion = "Укажите то, что лучше всего вас описывает:"
secondAnswer = [
    "принимаю решения",
    "завишу от чужого мнения",
    "не говорю нет, внутренний негатив",
    "пугают перемены",
]
lidMessage = 'С вами свяжется мой помощник и расскажет все о курсе. Напишите ваш номер телефона'

# Настройка Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1XGtu4pbTz75uhgivzU5Udne6Nnm5RcnHKy0TxU8JbeI'

# Глобальные переменные
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start"""
    user_id = update.message.from_user.id
    user_data[user_id] = {'step': 0}
    
    keyboard = [
        ['Получить чек-лист', 'Узнать о курсе']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(hello, reply_markup=reply_markup)
    
    # Запланировать следующий вопрос через 10 секунд
    context.job_queue.run_once(ask_if_read, 10, chat_id=update.message.chat_id, name=str(user_id))
    
    return STEP0

async def ask_if_read(context: ContextTypes.DEFAULT_TYPE):
    """Спросить, прочитал ли пользователь чек-лист"""
    job = context.job
    keyboard = [['Да', 'Нет']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(job.chat_id, "Ну как? Вы уже изучили чек-лист?", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик текстовых сообщений"""
    user_id = update.message.from_user.id
    text = update.message.text
    current_step = user_data.get(user_id, {}).get('step', 0)
    
    if text in KEYWORDS:
        return await start(update, context)
    
    if current_step == STEP0 and text == "Получить чек-лист":
        keyboard = [[
            InlineKeyboardButton(
                "Забрать пособие",
                url='https://drive.google.com/file/d/1UbQDHiwee8A2s94zO-61SEtYZdg50iYz/view'
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(book, reply_markup=reply_markup)
        user_data[user_id]['step'] = STEP1
        return STEP1
        
    elif current_step == STEP1 and text == "Да":
        keyboard = [['Да', 'Нет']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup)
        user_data[user_id]['step'] = STEP2
        return STEP2
        
    elif current_step == STEP1 and text == "Нет":
        keyboard = [['Да, я прочитал']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(refuseMessage, reply_markup=reply_markup)
        user_data[user_id]['step'] = STEP2
        return STEP2
        
    elif current_step == STEP2 and text in ["Да", "Да, я прочитал"]:
        keyboard = [['Начать']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(beginQuiz, reply_markup=reply_markup)
        user_data[user_id]['step'] = STEP3
        return STEP3
        
    elif current_step == STEP3 and text == "Начать":
        keyboard = [[ans] for ans in firstAnswer]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(firstQuestion, reply_markup=reply_markup)
        user_data[user_id]['step'] = STEP4
        return STEP4
        
    elif current_step == STEP4 and text in firstAnswer:
        keyboard = [[ans] for ans in secondAnswer]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(secondQuestion, reply_markup=reply_markup)
        user_data[user_id]['step'] = GET_PHONE
        return GET_PHONE
        
    elif current_step == GET_PHONE:
        # Проверка номера телефона
        if not re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', text):
            await update.message.reply_text('Напишите номер в формате 8(XXX)-XXX-XX-XX')
            return GET_PHONE
        
        user_data[user_id]['phone'] = text
        await update.message.reply_text('Как вас зовут?')
        user_data[user_id]['step'] = GET_NAME
        return GET_NAME
        
    elif current_step == GET_NAME:
        user_data[user_id]['name'] = text
        name = user_data[user_id]['name']
        
        # Сохранение в Google Sheets
        await save_to_google_sheets(user_data[user_id]['name'], user_data[user_id]['phone'])
        
        await update.message.reply_text(f'До скорой встречи {name}, с вами свяжется наш специалист')
        
        # Очистка данных пользователя
        if user_id in user_data:
            del user_data[user_id]
            
        return ConversationHandler.END
    
    return current_step

async def save_to_google_sheets(name: str, phone: str):
    """Сохранение данных в Google Sheets"""
    try:
        creds = Credentials.from_service_account_file('keys.json', scopes=SCOPES)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Data')
        
        # Добавление новой строки
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([name, phone, current_time])
        
    except Exception as e:
        logging.error(f"Ошибка при сохранении в Google Sheets: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена разговора"""
    user_id = update.message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text('Диалог прерван. Напишите /start чтобы начать заново.')
    return ConversationHandler.END

def main() -> None:
    """Запуск бота"""
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Создание обработчика разговора
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            STEP0: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            STEP1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            STEP2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            STEP3: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            STEP4: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Добавление обработчиков
    application.add_handler(conv_handler)
    
    # Обработчик ключевых слов
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'(?i)(фт|финтетрис|финансовый тетрис)'), start))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
