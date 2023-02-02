import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from datetime import datetime
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
import aiogram.types
from aiogram_broadcaster import MessageBroadcaster
from database import *
from config import *
from itertools import zip_longest, chain, islice
import matplotlib.pyplot as plt


def plot_rating(users):
    names = [user['name'] for user in users]
    balances = [user['balance'] for user in users]
    fig, ax = plt.subplots()
    
    plt.bar(names, balances)
    plt.xlabel('Работники')
    plt.ylabel('Количество баллов')
    plt.title('Рейтинг пользователей')

    plt.xticks(rotation=90)
    
    plt.tight_layout()
    plt.savefig('graph.png')

#Инициализация хранилища и бота
bot = Bot(token=token, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

def chunked(iterable, size):
    iterator = iter(iterable)
    for first in iterator:
        yield chain([first], islice(iterator, size - 1))

class Form(StatesGroup):  # Will be represented in storage as 'Form:age'
    change_name = State()
    change_last_name = State()
    create_task = State()
    create_task1 = State()
    create_task2 = State()
    create_task3 = State()
    create_task4 = State()
    give_task = State()


main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Задачи📆').add('Рейтинг📈').add('Настройки⚙️')
stop_kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена❌')
otmena = InlineKeyboardButton('Отмена🤕', callback_data='stop')

async def send_all(list_users, task_id, task_name, task_descript, bonus):
    for i in list_users:
        await bot.send_message(int(i), f'Новая задача! <b>{task_name}</b>\n{task_descript}\nБонус: {bonus}', reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Взять задачу', callback_data='take'+ str(task_id))))

@dp.message_handler(commands=['start'])
async def start(message):
    if check_user(message) is None:
        await message.reply('Мы отправили вашу заявку администратору, как только ее рассмотрят, вас добавят в рабочую группу')
        await bot.send_message(admin, f'Новый пользователь | {message.chat.id} | t.me/{message.chat.username} | {message.from_user.first_name}', reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Добавить', callback_data='add')))
    else:
        await message.reply('Вы в главном меню', reply_markup=main_kb)


@dp.message_handler(text='Задачи📆')
async def tasks(message):
    admins = get_admin_list()
    task_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Мои задачи', callback_data='my_task'), InlineKeyboardButton('Задачи направления', callback_data='group_task'))
    if message.chat.id in admins:
        task_kb.add(InlineKeyboardButton('Создать задачу', callback_data='create_task'))
    await bot.send_message(message.chat.id, '<b>Задачи🗓</b>', reply_markup=task_kb)

@dp.message_handler(text='Рейтинг📈')
async def rate(message):
    rate = rate_users()
    plot_rating(rate)
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=open('graph.png', 'rb')
    )
@dp.message_handler(text='Настройки⚙️')
async def settings(message):
    user = get_user(message)
    
    await message.reply(f'''
<b>Настройки⚙️</b>

Ваш балланс баллов: <code>{user[1]}</code>
Имя: <code>{user[2]}</code>
Фамилия: <code>{user[3]}</code>
Направление: <b>{get_group_name(user[5])}</b>''', reply_markup=(InlineKeyboardMarkup()).add(InlineKeyboardButton('Изменить ФИ', callback_data='changefi')))


@dp.callback_query_handler(lambda c: c.data == 'add')
async def add(callback_query: types.CallbackQuery):
    strings = get_group_names()
    print(strings)
    
    keyboard = InlineKeyboardMarkup()
    for button_group in chunked(strings, 2):
        row = []
        for button_name in button_group:
            row.append(InlineKeyboardButton(button_name[0], callback_data=button_name[0]))
        keyboard.add(*row)
    await bot.edit_message_reply_markup(chat_id = callback_query.from_user.id, message_id=callback_query.message.message_id, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data[0:4] == 'give')
async def give_taske(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    groups = get_groups()
    print(groups)
    keyboard = InlineKeyboardMarkup()
    for button_group in chunked(groups, 2):
        row = []
        for button_name in button_group:
            row.append(InlineKeyboardButton(button_name['name'], callback_data='gv' + str(button_name['group_id'])))
        keyboard.add(*row)
    keyboard.add(otmena)
    task_id = (callback_query.data).replace("give", "")
    await bot.send_message(callback_query.from_user.id, f'<code>task_id: {task_id}</code>\nВыберите группу, которой хотите передать задачу', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data[0:2] == 'gv')
async def give_taske(callback_query: types.CallbackQuery):
    
    task_id = int(((callback_query.message.text).split('\n'))[0].replace('task_id: ', ''))
    group_id = (callback_query.data).replace('gv', '')
    users = get_users_in_group(group_id)
    print(users)
    keyboard = InlineKeyboardMarkup()
    for button_group in chunked(users, 2):
        row = []
        for button_name in button_group:
            row.append(InlineKeyboardButton(button_name['name'], callback_data='gd' + str(button_name['user_id'])))
        keyboard.add(*row)
    keyboard.add(otmena)
    await bot.edit_message_text(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        text=f"<code>task_id: {task_id}</code>\n<b>Выберите человека, которому хотите передать задачу👇</b>",
        reply_markup= keyboard
    )
    print(task_id)

@dp.callback_query_handler(lambda c: c.data[0:2] == 'gd')
async def gd_taske(callback_query: types.CallbackQuery):
    task_id = int(((callback_query.message.text).split('\n'))[0].replace('task_id: ', ''))
    give_task((callback_query.data).replace('gd', ''), task_id=task_id)
    await callback_query.message.delete()
    await bot.send_message((callback_query.data).replace('gd', ''), 'Вам передали новую задачу')
    await bot.send_message(callback_query.from_user.id, 'Задача передана другому человеку')
    
@dp.callback_query_handler(lambda c: c.data == 'changefi')
async def change(callback_query: types.CallbackQuery):
    print(callback_query.message.from_user.id)
    await callback_query.message.delete()
    await bot.send_message(callback_query.from_user.id, 'Ваше <b>имя:</b> ', reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отмена❌')))
    await Form.change_name.set()


@dp.callback_query_handler(lambda c: c.data == 'create_task')
async def create_task(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.send_message(callback_query.from_user.id, 'Название задачи:', reply_markup=stop_kb)
    await Form.create_task.set()


@dp.callback_query_handler(lambda c: c.data == 'group_task')
async def group_tasks(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    tasks = get_groups_task(callback_query)
    print(tasks)
    keyboard = InlineKeyboardMarkup()
    for button_group in chunked(tasks, 2):
        row = []
        for button_name in button_group:
            row.append(InlineKeyboardButton((button_name['name']), callback_data=button_name['task_id']))
        keyboard.add(*row)
    keyboard.add(otmena)
    await bot.send_message(callback_query.from_user.id, '<b>Задачи</b>💪', reply_markup=keyboard)



@dp.callback_query_handler(lambda c: c.data == 'my_task')
async def my_tasks(callback_query: types.CallbackQuery):
    strings = get_my_tasks(callback_query)
    keyboard = InlineKeyboardMarkup()
    await callback_query.message.delete()
    for button_group in chunked(strings, 2):
        row = []
        for button_name in button_group:
            row.append(InlineKeyboardButton(button_name['name'], callback_data=button_name['task_id']))
        keyboard.add(*row)
    
    keyboard.add(otmena)
    await bot.send_message(callback_query.from_user.id, '<b>Ваши личные задачи</b>📆', reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'stop')
async def stop(callback_query: types.CallbackQuery):
    admins = get_admin_list()
    task_kb = InlineKeyboardMarkup().add(InlineKeyboardButton('Мои задачи', callback_data='my_task'), InlineKeyboardButton('Задачи направления', callback_data='group_task'))
    if int(callback_query.from_user.id) in admins:
        task_kb.add(InlineKeyboardButton('Создать задачу', callback_data='create_task'))
    await bot.send_message(callback_query.from_user.id, '<b>Задачи🗓</b>', reply_markup=task_kb)
    await callback_query.message.delete()

@dp.callback_query_handler(lambda c: c.data[0:3] == 'PRO')
async def pro(callback_query: types.CallbackQuery):
    create_user(callback_query)
    await callback_query.message.delete()
    print(callback_query)
@dp.callback_query_handler(lambda c: c.data[0:2] == 'ok')
async def ok(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    task = get_take_task(callback_query)
    user = get_user2(callback_query)
    await bot.send_message(callback_query.from_user.id, f"{task['name']}\nБонус: {task['bonus']}\n\nЗадача отмечена <b>выполненной</b>")
    await bot.send_message(-775689944, f"<b>{task['name']}</b>\n<b>Бонус:</b> {task['bonus']}\n\nЗадача отмечена <b>выполненной</b> пользователем {user[0]+ ' ' + user[1]}")
    ok_task(callback_query, int(task['bonus']))

@dp.callback_query_handler(lambda c: c.data[0:4] == 'take')
async def take(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    task = take_task(callback_query)
    if task is True:
        await bot.send_message(callback_query.from_user.id, 'Вы взяли задачу')
    else:
        await bot.send_message(callback_query.from_user.id, 'Ошибка! Задачу <b>взял другой человек</b>😬')

@dp.callback_query_handler()
async def add_group(callback_query: types.CallbackQuery):
    create_user(callback_query)
    task = get_take_task(callback_query)
    keyboard_take = InlineKeyboardMarkup()
    if get_task_take(callback_query, callback_query.data) is True:
        keyboard_take.add(InlineKeyboardButton('Отдать задачу другому', callback_data='give' + callback_query.data))
        keyboard_take.add(InlineKeyboardButton('Задача выполнена', callback_data='ok' + callback_query.data))

    else:
        keyboard_take.add(InlineKeyboardButton('Взять задачу', callback_data='take' + callback_query.data))
        keyboard_take.add(otmena)

    if task is False:
        print('таска не найдена')
    else:
        await callback_query.message.delete()
        await bot.send_message(callback_query.from_user.id, f'''<b>Задача🗓:</b> 

<b>{task['name']}</b>
{task['descript']}
Дедлайн: {task['deadline']}
<b>Бонус за выполнение: </b>{task['bonus']}
''', reply_markup=keyboard_take)
    

    

#Состояния
@dp.message_handler(state=Form.create_task)
async def create_task(message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == 'Отмена❌':
            await bot.send_message(message.chat.id, '<b>Вы в главном меню👨‍💻</b>', reply_markup=main_kb)
            await state.finish()
        else:
            data['id_task'] = create_tasks(message)
            
            await message.reply('Описание задачи:', reply_markup=stop_kb)
            await Form.create_task1.set()

@dp.message_handler(state=Form.create_task1)
async def create_task1(message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == 'Отмена❌':
            await bot.send_message(message.chat.id, '<b>Вы в главном меню👨‍💻</b>', reply_markup=main_kb)
            await state.finish()
        else:
            change_task(data['id_task'], 'description', message.text)
            await message.reply('Укажите дедлайн:', reply_markup=stop_kb)
            await Form.create_task2.set()

@dp.message_handler(state=Form.create_task2)
async def create_task(message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == 'Отмена❌':
            await bot.send_message(message.chat.id, '<b>Вы в главном меню👨‍💻</b>', reply_markup=main_kb)
            await state.finish()
        else:
            change_task(data['id_task'], 'deadline', message.text)
            strings = get_group_names()
            print(strings)
            
            keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
            for button_group in chunked(strings, 2):
                row = []
                for button_name in button_group:
                    row.append(KeyboardButton(button_name[0]))
                keyboard.add(*row)
            keyboard.add('Отмена❌')
            await message.reply('Выберите исполнителя: ', reply_markup=keyboard)
            await Form.create_task3.set()


@dp.message_handler(state=Form.create_task3)
async def create_task(message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == 'Отмена❌':
            await bot.send_message(message.chat.id, '<b>Вы в главном меню👨‍💻</b>', reply_markup=main_kb)
            await state.finish()
        else:
            data['group'] = get_group_id(message.text)[0]
            change_task(data['id_task'], 'group_id', data['group'])
            
            await message.reply('Введите бонус за задачу(Только число баллов, не более 3):', reply_markup=stop_kb)
            await Form.create_task4.set()


@dp.message_handler(state=Form.create_task4)
async def create_task4(message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == 'Отмена❌':
            await bot.send_message(message.chat.id, '<b>Вы в главном меню👨‍💻</b>', reply_markup=main_kb)
            await state.finish()
        else:
            if int(message.text) > 3:
                await message.reply('Количество бонусов <b>не должно быть</b> больше 3')
            else:
                users = get_users_in_group(data['group'])
                list_us = []
                for i in users:
                    list_us.append(i['user_id'])
                
                print('бонус')
                await message.reply('<b>Задача создана</b>👌', reply_markup=main_kb)
                taska = get_task(data['id_task'])
                await send_all(list_us, data['id_task'], taska['name'], taska['desc'], taska['bonus'])
                change_task(data['id_task'], 'bonus', message.text)


                await state.finish()


@dp.message_handler(state=Form.change_name)
async def change_name(message, state: FSMContext):
    if message.text == 'Отмена❌':
        await bot.send_message(message.chat.id, '<b>Вы в главном меню👨‍💻</b>', reply_markup=main_kb)
        await state.finish()
    else:
        update_name(message)
        await message.reply('Ваша <b>фамилия:</b>')
        await Form.change_last_name.set()

@dp.message_handler(state=Form.change_last_name)
async def change_last_name(message, state: FSMContext):
    if message.text == 'Отмена❌':
        await bot.send_message(message.chat.id, '<b>Вы в главном меню👨‍💻</b>', reply_markup=main_kb)
        await state.finish()
    else:
        update_last_name(message)
        await message.reply('Ваши имя и фамилия <b>изменены🤖</b>', reply_markup=main_kb)
        await state.finish()

    

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

