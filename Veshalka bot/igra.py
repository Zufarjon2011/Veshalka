import logging
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.exceptions import BotBlocked, ChatNotFound
from aiogram.dispatcher.filters import Text
import time
from collections import defaultdict

# Замените на свой токен бота
API_TOKEN = '6568445010:AAEMrkTOPFvkl2nMYDu3I-04AGbChjsdQhc'  # Вставьте ваш токен бота Telegram

# Загрузка переменных среды
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Данные игры
games = defaultdict(lambda: {
    'word': None,
    'attempts': 6,
    'letters_guessed': set(),
    'players': [],
    'current_player': None,
    'game_started': False,
})

# Словарь с возможными словами
words = ["python", "javascript", "programming", "computer", "science", "artificial", "intelligence"]

# Функции игры
def get_word():
    """Возвращает случайное слово из списка."""
    return random.choice(words)

def display_hangman(attempts):
    """Отображает виселицу в зависимости от количества попыток."""
    stages = [  # Финальный этап
                """
                   --------
                   |      |
                   |      O
                   |     \\|/
                   |      |
                   |     / \\
                   -
                """,
                # Предпоследний этап
                """
                   --------
                   |      |
                   |      O
                   |     \\|/
                   |      |
                   |     / 
                   -
                """,
                # Третий этап
                """
                   --------
                   |      |
                   |      O
                   |     \\|/
                   |      |
                   |      
                   -
                """,
                # Второй этап
                """
                   --------
                   |      |
                   |      O
                   |     \\|
                   |      |
                   |     
                   -
                """,
                # Первый этап
                """
                   --------
                   |      |
                   |      O
                   |      |
                   |      |
                   |     
                   -
                """,
                # Начальный этап
                """
                   --------
                   |      |
                   |      
                   |      
                   |      
                   |     
                   -
                """
    ]
    return stages[attempts]

def get_current_player(chat_id):
    """Возвращает имя текущего игрока."""
    return games[chat_id]['players'][games[chat_id]['current_player']]

def next_player(chat_id):
    """Переключает текущего игрока."""
    current_player = games[chat_id]['current_player']
    games[chat_id]['current_player'] = (current_player + 1) % len(games[chat_id]['players'])

# Команды бота
@dp.message_handler(commands=['start'])
async def start_game(message: types.Message):
    """Начинает новую игру."""
    chat_id = message.chat.id
    games[chat_id]['game_started'] = False
    games[chat_id]['players'].append(message.from_user.first_name)
    await message.answer(f"Привет, {message.from_user.first_name}! 👋\n"
                        f"Хочешь сыграть в Вешалку? 🕹\n"
                        f"Напиши /new чтобы начать новую игру или /join чтобы присоединиться к существующей.")

@dp.message_handler(commands=['new'])
async def new_game(message: types.Message):
    """Создает новую игру."""
    chat_id = message.chat.id
    if games[chat_id]['game_started']:
        await message.answer("Игра уже началась! 🎮")
        return

    games[chat_id]['word'] = get_word()
    games[chat_id]['attempts'] = 6
    games[chat_id]['letters_guessed'] = set()
    games[chat_id]['current_player'] = 0
    games[chat_id]['game_started'] = True

    await message.answer(f"Новая игра началась! 🎲\n"
                         f"Слово: {'*' * len(games[chat_id]['word'])} \n"
                         f"Попыток: {games[chat_id]['attempts']} \n"
                         f"Ходит {get_current_player(chat_id)}.")


@dp.message_handler(commands=['join'])
async def join_game(message: types.Message):
    """Присоединяется к существующей игре."""
    chat_id = message.chat.id
    if not games[chat_id]['game_started']:
        await message.answer("Игра еще не началась! ⏳")
        return
    if message.from_user.first_name not in games[chat_id]['players']:
        games[chat_id]['players'].append(message.from_user.first_name)
        await message.answer(f"Вы успешно присоединились к игре! 👍\n"
                             f"Слово: {'*' * len(games[chat_id]['word'])} \n"
                             f"Попыток: {games[chat_id]['attempts']} \n"
                             f"Ходит {get_current_player(chat_id)}.")
    else:
        await message.answer("Вы уже в игре! 😉")


@dp.message_handler(Text(equals='да'), state='*')
async def continue_game(message: types.Message):
    """Продолжает игру после паузы."""
    chat_id = message.chat.id
    if not games[chat_id]['game_started']:
        await message.answer("Игра еще не началась! ⏳")
        return

    hidden_word = ''.join([letter if letter in games[chat_id]['letters_guessed'] else '*'
                           for letter in games[chat_id]['word']])
    await message.answer(f"Продолжаем! 🎮\n"
                         f"Слово: {hidden_word} \n"
                         f"Попыток: {games[chat_id]['attempts']} \n"
                         f"Ходит {get_current_player(chat_id)}.")


@dp.message_handler(Text(equals='нет'), state='*')
async def end_game(message: types.Message):
    """Заканчивает игру."""
    chat_id = message.chat.id
    await message.answer("Хорошо, игра окончена! 🏁")
    games[chat_id]['game_started'] = False


@dp.message_handler()
async def handle_message(message: types.Message):
    """Обрабатывает сообщения от игроков."""
    chat_id = message.chat.id
    if not games[chat_id]['game_started']:
        await message.answer("Игра еще не началась! ⏳")
        return
    if message.from_user.first_name != get_current_player(chat_id):
        await message.answer("Сейчас не ваш ход! 🙅")
        return
    if message.text.lower() in games[chat_id]['letters_guessed']:
        await message.answer("Эта буква уже была названа! 🤔")
        return
    if message.text.lower() in games[chat_id]['word']:
        games[chat_id]['letters_guessed'].add(message.text.lower())
        await message.answer("Правильно! 👍")

        hidden_word = ''.join([letter if letter in games[chat_id]['letters_guessed'] else '*'
                               for letter in games[chat_id]['word']])

        if all(letter in games[chat_id]['letters_guessed'] for letter in games[chat_id]['word']):
            await message.answer(f"Поздравляем, {get_current_player(chat_id)}, вы выиграли! 🎉\n"
                                 f"Слово: {games[chat_id]['word']}")
            games[chat_id]['game_started'] = False
            return

        await message.answer(f"Слово: {hidden_word} \n"
                             f"Попыток: {games[chat_id]['attempts']} \n"
                             f"Ходит {get_current_player(chat_id)}.")
        next_player(chat_id)

    else:
        games[chat_id]['attempts'] -= 1
        await message.answer(f"Неверно! 😔\n"
                             f"Осталось попыток: {games[chat_id]['attempts']}\n"
                             f"{display_hangman(games[chat_id]['attempts'])}")

        if games[chat_id]['attempts'] == 0:
            await message.answer(f"Вы проиграли! 😭\n"
                                 f"Слово было: {games[chat_id]['word']}"
                                 f"/start")
            games[chat_id]['game_started'] = False
            return


        await message.answer(f"Слово: {[words]} \n"
                            f"Попыток: {games[chat_id]['attempts']} \n"
                            f"Ходит {get_current_player(chat_id)}.")
        next_player(chat_id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


