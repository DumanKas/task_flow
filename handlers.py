from aiogram import Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from keyboards import start_keyboard,category_keyboard,priority_keyboard,mark_done_keyboard,delete_category_keyboard,stats_period_keyboard
from aiogram import F
from database import add_task,add_user,get_pending_tasks,mark_task_done,add_category,get_user_category,get_user_categories,delete_category,get_stats
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime
router = Router()

class AddUser(StatesGroup):
    name = State()
class DbSessionMiddleware(BaseMiddleware):
    def __init__(self,pool):
        self.pool = pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data:Dict[str,Any]       
    ) -> Any:
        data['dp_pool'] = self.pool

        return await handler(event,data)


class AddCategory(StatesGroup):
    name = State()
class AddTask(StatesGroup):
    title = State()
    deadline = State()
    description = State()
    category = State()
    priority = State()

@router.message(Command("start"))
async def start_hendler(message: Message):
    await message.answer('Добро пожаловать в бот TaskFlow, выберите варианты из списка', reply_markup= start_keyboard())


@router.callback_query(F.data == 'categories')
async def categories_command(callback: types.CallbackQuery, dp_pool):
    user_id = callback.from_user.id
    cat = await get_user_category(dp_pool, user_id)
    if not cat:
        await callback.message.answer("У тебя пока нет категорий")
        return
    text = "\n".join([f"• {c['name']}" for c in cat])
    await callback.message.answer(f"Твои категории:\n\n{text}")
    await callback.answer()
@router.callback_query(F.data == 'register')
async def register_command(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Как вас зовут? ')
    await state.set_state(AddUser.name)
    await callback.answer()

@router.callback_query(F.data == "del_category")
async def delete_cat_command(callback: types.CallbackQuery, dp_pool):
    user_id = callback.from_user.id
    categories = await get_user_category(dp_pool, user_id)
    kb = delete_category_keyboard(categories)
    await callback.message.answer('Выберите категорию которую хотите удалить', reply_markup= kb)
    await callback.answer()
@router.callback_query(F.data.startswith('del_cat_'))
async def del_category_handler(callback: types.CallbackQuery, dp_pool):
    parts = callback.data.split('_')
    category_id = int(parts[2])
    user_id = callback.from_user.id
    await delete_category(dp_pool, category_id, user_id)
    await callback.message.answer("Категория успешна удалена")
    await callback.answer()
@router.message(AddUser.name)
async def add_name(message: Message,state: FSMContext,dp_pool):
    name =  str(message.text)
    user_id = message.from_user.id
    add = await add_user(dp_pool, user_id, name)
    await message.answer(f'Пользователь добавлен {add}')
    await state.clear()
    
@router.callback_query(F.data == 'stats')
async def stats_command(callback: types.CallbackQuery):
    await callback.message.edit_text('За какой период?', reply_markup=stats_period_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith('stats_'))
async def stats_result(callback: types.CallbackQuery, dp_pool):
    days = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    result = await get_stats(dp_pool, user_id, days)
    period_text = "день" if days == 1 else "неделю"
    await callback.message.edit_text(
        f"Статистика за {period_text}:\n\nВыполнено: {result['completed']}\nВ процессе: {result['pending']}"
    )
    await callback.answer()
@router.callback_query(F.data == 'add_category')
async def add_category_callback(callback: types.CallbackQuery,state: FSMContext):
    await callback.message.answer('Напишите название категории')
    await state.set_state(AddCategory.name)
    await callback.answer()
    

@router.message(AddCategory.name)
async def add_category_class(message: Message, state: FSMContext, dp_pool):
    user_id = message.from_user.id
    name = str(message.text)
    add = await add_category(dp_pool, user_id, name)
    await message.answer(f'Категория добавлена {add}')
    await state.clear()


@router.callback_query(F.data == 'add_task_c')
async def add_task_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Напишите название задачи: ')
    await state.set_state(AddTask.title) 
    await callback.answer()

@router.message(AddTask.title)
async def add_task_title(message: Message, state: FSMContext):
    await state.update_data(title = message.text)
    await message.answer('Отлично! Теперь напишите дедлайн пример: 15.07.2026 18:30')
    await state.set_state(AddTask.deadline)

@router.message(AddTask.deadline)
async def add_task_deadline(message: Message, state: FSMContext):
    try:
        deadline = message.text 
        deadline = datetime.strptime(deadline, "%d.%m.%Y %H:%M")
        
    except ValueError:
        await message.answer("Ошибка")
        return
    await state.update_data(deadline = deadline)
    await message.answer("Введите описание: ")
    await state.set_state(AddTask.description)

@router.message(AddTask.description)
async def add_task_description(message: Message, state: FSMContext,dp_pool):
    await state.update_data(description = message.text)
    user_id = message.from_user.id
    categories = await get_user_categories(dp_pool,user_id)
    kb = category_keyboard(categories)
    await message.answer("Выберите категорию: ", reply_markup=kb)
    await state.set_state(AddTask.category)

@router.callback_query(F.data.startswith('cat_'))
async def add_task_category(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split('_')
    category_id = int(parts[1])
    pr_k = priority_keyboard()
    await state.update_data(category = category_id)
    await callback.message.edit_text('Выберите приоритет: ',reply_markup = pr_k)
    await callback.answer()
@router.callback_query(F.data.in_(['low_prority', 'medium_priority', 'high_priority']))
async def add_task_priority(callback: CallbackQuery, state: FSMContext,dp_pool):
    priority = callback.data.split('_')[0]
    data = await state.get_data()
    user_id = callback.from_user.id
    title = data['title']
    deadline = data['deadline']
    description = data['description']
    category = data['category']


    add = await add_task(dp_pool,user_id,title,description,category,deadline,priority)
    await callback.message.edit_text(f"Задача успешно добавлена {add}")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == 'mark_done')
async def mark_done_command(callback: CallbackQuery, dp_pool):
    user_id = callback.from_user.id
    mark_done = await get_pending_tasks(dp_pool, user_id)
    if not mark_done:
        await callback.message.answer("Незавершенных задач нет. Можно выдохнуть")
        return
    kb = mark_done_keyboard(mark_done)
    await callback.message.answer('Выберите задачу из списка', reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith('finish_'))
async def mark_done_callback(callback: CallbackQuery, dp_pool):
    part = callback.data.split('_')
    task_id = int(part[1])
    await mark_task_done(dp_pool, task_id)
    await callback.message.edit_text(f'Успех! \n\nСтатус изменен')
    await callback.answer()