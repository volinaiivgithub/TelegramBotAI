import telegram
import openai
import logging
import os
from telegram import InputMediaPhoto
from openai import Image
from telegram.ext import CommandHandler, Updater


# Установка API-ключей и модели
telegram_token = '' # токен бота в телеге - https://t.me/BotFather
api_key = '' # ключ в chatgpt - https://platform.openai.com/account/api-keys
openai_model = 'text-davinci-003' # тип чата - https://platform.openai.com/examples
max_length = 2048
save_dialog = True
count_images_create = 4

# 
openai.api_key = api_key

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# Создание экземпляра бота
bot = telegram.Bot(token=telegram_token)


# Показать список команд
def help_command(update, context):
    help_message = '''
    <b>Список команд:</b>
    /help - показать список команд
    /chat - Открытый разговор с помощником ИИ.
    /qanda - Отвечайте на вопросы, исходя из имеющихся знаний.
    /sarcasm - саркастичный чат-бот
    /image - создание изображения с помощью GPT-3
    '''
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_message, parse_mode='HTML')

# Функция для сохранения диалога в файл
def save_dialogue(fileName, update, user_message, bot_response):
    file_dir = f"{fileName}/{update.effective_chat.title}"
    file_name = f"{file_dir}/{update.effective_user.id}.txt"
    os.makedirs(file_dir, exist_ok=True)
    with open(file_name, 'a', encoding='utf-8') as f: f.write(f"Human: {user_message}\nAI: {bot_response}\n")


# Функция для загрузки предыдущего диалога из файла
def load_dialogue(fileName, update):
    file_dir = f"{fileName}/{update.effective_chat.title}"
    file_name = f"{file_dir}/{update.effective_user.id}.txt"
    if os.path.isfile(file_name):
        with open(file_name, 'r', encoding='utf-8') as f: previous_dialogue = f.read()
    else: previous_dialogue = ""
    return previous_dialogue


# Функция для очистки файла диалога
def clear_dialogue(fileName, update):
    file_dir = f"{fileName}/{update.effective_chat.title}"
    file_name = f"{file_dir}/{update.effective_user.id}.txt"
    os.makedirs(file_name, exist_ok=True)
    with open(file_name, 'w', encoding='utf-8') as f: f.write("")


# Проверить макс диалог
def is_clear_dialogue(context, prompt, fileName, update):
    if len(prompt) > max_length: # Если длина контекста превышает максимально допустимое значение, то очищаем диалог
        clear_dialogue(fileName, update)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Очищен диалог из-за превышения максимальной длины контекста модели OpenAI.")
        return True
    else: return False


# Функция для генерации ответов с помощью OpenAI
def generate_response(model, user_message, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, stop):
    response = openai.Completion.create(
        model=model,
        prompt=user_message,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=stop
    )

    bot_response = response.choices[0].text.strip()
    return bot_response


# Открытый разговор с помощником ИИ.
def chat_command(update, context):
    user_message = " ".join(context.args)
    if not user_message.strip(): context.bot.send_message(chat_id=update.effective_chat.id, text="Введите текст сообщения, пожалуйста.")
    else:
        file_name = update.message.text.split()[0][1:]
        if save_dialog: previous_dialogue = load_dialogue(file_name, update)
        else: previous_dialogue = ''

        prompt = f"The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\n{previous_dialogue}\nHuman: {user_message}\nAI:"
        
        if save_dialog and is_clear_dialogue(context, prompt, file_name, update): return
        else: bot_response = generate_response('text-davinci-003', prompt, 0, 2000, 1, 0.0, 0.0, None)
        
        if not bot_response.strip(): context.bot.send_message(chat_id=update.effective_chat.id, text="Ой! Произошла ошибка.")
        else:
            if save_dialog: save_dialogue(file_name, update, user_message, bot_response)
            context.bot.send_message(chat_id=update.effective_chat.id, text=bot_response)


# Отвечайте на вопросы, исходя из имеющихся знаний.
def qanda_command(update, context):
    user_message = " ".join(context.args)
    if not user_message.strip(): context.bot.send_message(chat_id=update.effective_chat.id, text="Введите текст сообщения, пожалуйста.")
    else:
        prompt = f"I am a highly intelligent question answering bot. If you ask me a question that is rooted in truth, I will give you the answer. If you ask me a question that is nonsense, trickery, or has no clear answer, I will respond with \"Я понимаю, что вы не знаете, как на это ответить. Может быть, я могу помочь с какой-то другой информацией?\".\n\nQ: {user_message}\nA:"
        bot_response = generate_response('text-davinci-003', prompt, 0, 2000, 1, 0.0, 0.0, None)
        
        if not bot_response.strip(): context.bot.send_message(chat_id=update.effective_chat.id, text="Ой! Произошла ошибка.")
        else: context.bot.send_message(chat_id=update.effective_chat.id, text=bot_response)


# саркастичный чат-бот
def sarcasm_command(update, context):
    user_message = " ".join(context.args)
    if not user_message.strip(): context.bot.send_message(chat_id=update.effective_chat.id, text="Введите текст сообщения, пожалуйста.")
    else:
        file_name = update.message.text.split()[0][1:]
        if save_dialog: previous_dialogue = load_dialogue(file_name, update)
        else: previous_dialogue = ''

        prompt = f"{previous_dialogue}\nHuman: {user_message} Oh cool. Let me just drop everything and come up with a sarcastic response...\nAI:"
        
        if save_dialog and is_clear_dialogue(context, prompt, file_name, update): return
        else: bot_response = generate_response('text-davinci-003', prompt, 0.7, 2000, 1, 0.0, 0.0, None)
        
        if not bot_response.strip(): context.bot.send_message(chat_id=update.effective_chat.id, text="Ой! Произошла ошибка.")
        else:
            if save_dialog: save_dialogue(file_name, update, user_message, bot_response)
            context.bot.send_message(chat_id=update.effective_chat.id, text=bot_response)


# создание изображения с помощью GPT-1
def image_command(update, context):
    user_message = ' '.join(context.args)
    if not user_message.strip(): context.bot.send_message(chat_id=update.effective_chat.id, text = f"Введите текст сообщения, пожалуйста. Пример: /{update.message.text.split()[0][1:]} Привет!")
    else:
        response = Image.create(
            prompt=user_message,
            n=count_images_create,
            size="512x512",
            model="image-alpha-001"
        )
        media = [InputMediaPhoto(item['url']) for item in response['data']]
        context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)


# Запуск бота
def main():
    # Создание и настройка экземпляра Updater
    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher

    # Добавление обработчиков команд и сообщений
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('chat', chat_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('qanda', qanda_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('image', image_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('sarcasm', sarcasm_command, pass_args=True))

    # Запуск бота
    updater.start_polling()
    updater.idle()


# Запуск бота
if __name__ == '__main__': main()