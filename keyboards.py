from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery

def start_keyboard():
    st_k = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Регистрация', callback_data='register')],
        [InlineKeyboardButton(text='Категории', callback_data='categories')],
        [InlineKeyboardButton(text='Отметка выполнения', callback_data='mark_done')],
        [InlineKeyboardButton(text='Статистика за день/неделю', callback_data='stats')],
        [InlineKeyboardButton(text = 'Добавить задачу', callback_data = 'add_task_c')],
        [InlineKeyboardButton(text= 'Добавить категорию', callback_data = 'add_category')],
        [InlineKeyboardButton(text= 'Удалить категорию', callback_data = 'del_category')]
    ])
    return st_k

def priority_keyboard():
    pr_k = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='low',callback_data='low_priority')],
        [InlineKeyboardButton(text='medium',callback_data='medium_priority')],
        [InlineKeyboardButton(text='high', callback_data='high_priority')]
    ])

    return pr_k
def category_keyboard(categories):
    buttons = []
    for cat in categories:
        buttons.append(
        [InlineKeyboardButton(text=f'{cat["name"]}', callback_data=f"cat_{cat['id']}")])


    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return kb
    
def mark_done_keyboard(tasks):
    buttons = []
    for tas in tasks:
        buttons.append(
            [InlineKeyboardButton(text = f"{tas['title']} | {tas['deadline']}",callback_data= f"finish_{tas['id']}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return kb


def delete_category_keyboard(categories):
    buttons = []
    for dell in categories:
        buttons.append(
            [InlineKeyboardButton(text = f"del {dell['name']}", callback_data= f"del_cat_{dell['id']}")]
        )
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return kb

def stats_period_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='За день', callback_data='stats_1')],
        [InlineKeyboardButton(text='За неделю', callback_data='stats_7')]
    ])