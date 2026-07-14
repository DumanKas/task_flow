from aiogram import Dispatcher, types, Router
from aiogram.types import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from keyboards import start_keyboard,category_keyboard,priority_keyboard,mark_done_keyboard
from aiogram import F
from database import add_task,add_user,get_user_categories,get_pending_tasks,mark_task_done
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

class AddTask(StatesGroup):
    title = State()
    deadline = State()
    description = State()
    category = State()
    priority = State()

@router.message(Command("start"))
async def start_hendler(message: Message):
    await message.answer('Добро пожаловать в бот TaskFlow, выберите варианты из списка', reply_markup= start_keyboard())


@router.callback_query(F.data == 'register')
async def register_command(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Как вас зовут?: ')
    await state.set_state(AddUser.name)
    await callback.answer()

@router.message(AddUser.name)
async def add_name(message: Message,state: FSMContext,dp_pool):
    name =  str(message.text)
    user_id = message.from_user.id
    add = await add_user(dp_pool, user_id, name)
    await message.answer(f'Пользователь добавлен{add}')
    await state.clear()
    

@router.callback_query(F.data == 'add_task_c')
async def add_task_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer('Напишите название задачи: ')
    await state.set_state(AddTask.title) 
    await callback.answer()

@router.message(AddTask.title)
async def add_task_title(message: Message, state: FSMContext):
    await state.update_data(title = message.text)
    await message.answer('Отлично! Теперь напишите дедлайн')
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
    await callback.message.answer('Выберите приоритет: ',reply_markup = pr_k)
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
    await callback.message.answer(f"Задача успешно добавлена{add}")
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
    await callback.message.answer(f'Успех! \n\nСтатус изменен')
    await callback.answer()