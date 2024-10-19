import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from dotenv import load_dotenv
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

TOKEN = os.getenv('BOT_API_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

guess_number_states = {}
tic_tac_toe_states = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Задание 1: Отправка файлов"),
            types.KeyboardButton(text="Задание 2: Угадай число")
        ],
        [
            types.KeyboardButton(text="Задание 3: Крестики-нолики")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите задание"
    )
    await message.answer("Выберите задание:", reply_markup=keyboard)

# Task 1: Sending files
@dp.message(F.text == "Задание 1: Отправка файлов")
async def task_1(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="Отправить изображение"),
            types.KeyboardButton(text="Отправить файл")
        ],
        [
            types.KeyboardButton(text="Назад")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    await message.answer("Что вы хотите сделать?", reply_markup=keyboard)

@dp.message(F.text == "Отправить изображение")
async def send_image(message: types.Message):
    image_path = "assets/pizza.jpg"  
    if os.path.exists(image_path):
        await bot.send_photo(message.chat.id, photo=FSInputFile(image_path))
    else:
        await message.answer("Изображение не найдено")

@dp.message(F.text == "Отправить файл")
async def send_file(message: types.Message):
    file_path = "assets/video.mp4"  
    if os.path.exists(file_path):
        await bot.send_document(message.chat.id, document=FSInputFile(file_path))
    else:
        await message.answer("Файл не найден")

# Task 2: Guess the Number
@dp.message(F.text == "Задание 2: Угадай число")
async def task_2(message: types.Message):
    user_id = message.from_user.id
    guess_number_states[user_id] = random.randint(1, 10)
    await message.answer("Я загадал число от 1 до 10. Попробуйте угадать!")

@dp.message(lambda message: message.text.isdigit())
async def process_number_answer(message: types.Message):
    user_id = message.from_user.id
    if user_id not in guess_number_states:
        await message.answer("Сначала начните игру 'Угадай число'")
        return

    user_number = int(message.text)
    target_number = guess_number_states[user_id]

    if user_number == target_number:
        await message.answer(f"Поздравляю! Вы угадали число {target_number}!")
        del guess_number_states[user_id]
    elif user_number < target_number:
        await message.answer("Мое число больше. Попробуйте еще раз!")
    else:
        await message.answer("Мое число меньше. Попробуйте еще раз!")

# Task 3: Tic-Tac-Toe
@dp.message(F.text == "Задание 3: Крестики-нолики")
async def task_3(message: types.Message):
    user_id = message.from_user.id
    tic_tac_toe_states[user_id] = [" " for _ in range(9)]
    await send_tic_tac_toe_board(message.chat.id, user_id)

async def send_tic_tac_toe_board(chat_id, user_id):
    board = tic_tac_toe_states[user_id]
    buttons = []
    for i in range(9):
        buttons.append(InlineKeyboardButton(
            text=board[i] if board[i] != " " else "·",
            callback_data=f"ttt:{i}"
        ))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+3] for i in range(0, 9, 3)])
    await bot.send_message(chat_id, "Ваш ход (X):", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('ttt:'))
async def process_tic_tac_toe_move(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in tic_tac_toe_states:
        await callback_query.answer("Игра не начата")
        return

    board = tic_tac_toe_states[user_id]
    move = int(callback_query.data.split(':')[1])

    if board[move] != " ":
        await callback_query.answer("Эта клетка уже занята!")
        return

    board[move] = "X"
    if check_winner(board, "X"):
        await bot.edit_message_text("Вы победили!", chat_id=str(callback_query.message.chat.id), message_id=callback_query.message.message_id)
        del tic_tac_toe_states[user_id]
        return

    if " " not in board:
        await bot.edit_message_text("Ничья!", chat_id=str(callback_query.message.chat.id), message_id=callback_query.message.message_id)
        del tic_tac_toe_states[user_id]
        return

    # Bot's move
    bot_move = make_bot_move(board)
    board[bot_move] = "O"
    if check_winner(board, "O"):
        await bot.edit_message_text("Бот победил!", chat_id=str(callback_query.message.chat.id), message_id=callback_query.message.message_id)
        del tic_tac_toe_states[user_id]
        return

    buttons = [InlineKeyboardButton(
        text=board[i] if board[i] != " " else "·",
        callback_data=f"ttt:{i}"
    ) for i in range(9)]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+3] for i in range(0, 9, 3)])

    await bot.edit_message_text(
        "Ваш ход (X):",
        chat_id=str(callback_query.message.chat.id),
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )

def check_winner(board, player):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]  # Diagonals
    ]
    return any(all(board[i] == player for i in combo) for combo in winning_combinations)

def make_bot_move(board):
    empty_cells = [i for i, cell in enumerate(board) if cell == " "]
    return random.choice(empty_cells)

@dp.message(F.text == "Назад")
async def go_back(message: types.Message):
    await cmd_start(message)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())