import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove,
)

BOT_TOKEN = "" #ваш токен

# ---------- Вопросы теста ----------
QUESTIONS = [
    {
        "question": "Вопрос 1: Какое число продолжит ряд: 2, 4, 8, 16, ...?",
        "options": ["24", "30", "32", "64"],
        "answer": "32",
    },
    {
        "question": "Вопрос 2: Сколько будет 7 × 8?",
        "options": ["48", "50", "56", "64"],
        "answer": "56",
    },
    {
        "question": "Вопрос 3: Если 5 машин красят 5 стен за 5 часов, сколько часов нужно 100 машинам, чтобы покрасить 100 стен?",
        "options": ["5", "20", "100", "500"],
        "answer": "5",
    },
    {
        "question": "Вопрос 4: Какое число лишнее: 3, 5, 7, 9, 11?",
        "options": ["3", "5", "7", "9", "11"],
        "answer": "9",
    },
    {
        "question": "Вопрос 5: Продолжи ряд: 2, 4, 8, 16, …",
        "options": ["24", "30", "32", "36"],
        "answer": "32",
    },
    {
        "question": "Вопрос 6: Какое слово лишнее?",
        "options": ["Яблоко", "Груша", "Морковь", "Персик"],
        "answer": "Морковь",
    },
    {
        "question": "Вопрос 7: «Птица» относится к «гнезду», как «человек» относится к …",
        "options": ["Дереву", "Пещере", "Дому", "Машине"],
        "answer": "Дому",
    },
    {
        "question": "Вопрос 8: Если все кошки умеют мяукать, а Барсик — кошка, то…",
        "options": ["Барсик не умеет мяукать", "Барсик умеет мяукать", "Неизвестно", "Барсик лает"],
        "answer": "Барсик умеет мяукать",
    },
    {
        "question": "Вопрос 9: Продолжи ряд: 1, 1, 2, 3, 5, 8, …",
        "options": ["12", "13", "14", "15"],
        "answer": "13",
    },
]


# ---------- Состояния (FSM) ----------
class Quiz(StatesGroup):
    answering = State()

bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(storage=MemoryStorage())

# ---------- Главное меню ----------
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Начать IQ тест"), KeyboardButton(text="Рестарт")]
    ],
    resize_keyboard=True,
)

def question_keyboard(index: int) -> InlineKeyboardMarkup:
    options = QUESTIONS[index]["options"]
    rows = [
        [InlineKeyboardButton(text=opt, callback_data=f"ans:{index}:{opt}")]
        for opt in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def send_question(message: Message, state: FSMContext, index: int):
    if index == 0:
        await state.update_data(current=0, score=0)
    else:
        await state.update_data(current=index)
    await message.answer(
        QUESTIONS[index]["question"],
        reply_markup=ReplyKeyboardRemove(),  # старые кнопки исчезают
    )
    await message.answer("Выбери ответ или напиши его текстом 👇",
                         reply_markup=question_keyboard(index))

@dispatcher.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"Приветствую, {message.from_user.first_name}! \nЭто бот по IQ тесту. \n\nВыбери, что хочешь сделать:",
        reply_markup=kb
    )

@dispatcher.message(F.text == "Начать IQ тест")
async def start_iq_test_handler(message: Message, state: FSMContext):
    await state.set_state(Quiz.answering)
    await message.answer("Отлично! Начинаем тест.\n")
    await send_question(message, state, 0)

@dispatcher.message(F.text == "Рестарт")
async def restart_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Тест перезапущен. Нажми «Начать IQ тест», чтобы стартовать заново.",
                         reply_markup=kb)


async def check_answer(message: Message, state: FSMContext, user_answer: str):
    data = await state.get_data()
    index = data["current"]
    score = data.get("score", 0)

    if user_answer.strip() == QUESTIONS[index]["answer"]:
        score += 1
        await message.answer("✅ Верно!")
    else:
        await message.answer(
            f"❌ Неправильно. Правильный ответ: {QUESTIONS[index]['answer']}"
        )

    next_index = index + 1
    if next_index < len(QUESTIONS):
        await state.update_data(current=next_index, score=score)
        await send_question(message, state, next_index)
    else:
        await state.clear()
        await message.answer(
            f"🏁 Тест завершён!\nТвой результат: {score} из {len(QUESTIONS)}.\n\n"
            "Нажми «Начать IQ тест», чтобы пройти заново.",
            reply_markup=kb,  # возвращаем главное меню
        )


@dispatcher.callback_query(StateFilter(Quiz.answering), F.data.startswith("ans:"))
async def answer_button_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # убираем «часики» на кнопке
    _, _, option = callback.data.split(":")
    await check_answer(callback.message, state, option)


@dispatcher.message(StateFilter(Quiz.answering), F.text)
async def answer_text_handler(message: Message, state: FSMContext):
    await check_answer(message, state, message.text)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
