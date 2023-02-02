import sqlite3
from os import path
import random

def get_script_dir():
    abs_path = path.abspath(__file__) # полный путь к файлу скрипта
    return path.dirname(abs_path)

DB_FILE = get_script_dir() + path.sep + 'base.db'
#Коннект к базе
db = sqlite3.connect(DB_FILE,  check_same_thread=False)
sql = db.cursor()
db.commit()

#Функция создания базы
def create_base():
    sql.execute(f"""CREATE TABLE IF NOT EXISTS users(
        user_id BIGINT,
        balance BIGINT,
        name TEXT,
        first_name TEXT,
        tasks TEXT,
        group_id BIGINT,
        count_task BIGINT,
        admin BIGINT
    )""")
    sql.execute(f"""CREATE TABLE IF NOT EXISTS tasks(
        task_id BIGINT ,
        name TEXT,
        description TEXT,
        owner TEXT,
        executor TEXT,
        group_id TEXT,
        urgency TEXT,
        deadline TEXT,
        bonus TEXT, 
        status BIGINT
    )""")
    sql.execute(f"""CREATE TABLE IF NOT EXISTS groups(
        group_id BIGINT,
        name TEXT,
        participants TEXT
    )""")
    db.commit()

def check_user(message):
    if sql.execute(f"SELECT user_id FROM users WHERE user_id = {message.chat.id}").fetchone() is None:
        return None
    else:
        return 1
def get_group_names():
    return sql.execute(f"SELECT name FROM groups").fetchall()

def get_group_name(name):
    return sql.execute(f"SELECT name FROM groups WHERE group_id = '{name}'")



def get_group_id(name):
    return sql.execute(f"SELECT group_id FROM groups WHERE name = '{name}'").fetchone()
    

def create_user(callback):
    try:
        group_id = sql.execute(f"SELECT group_id FROM groups WHERE name = '{callback.data}'").fetchone()
        user_id = ((callback.message.text).split(' | '))[1]
        sql.execute(f"INSERT INTO users VALUES({user_id}, 0, '0', '0', '0', {group_id[0]}, 0, 0)")
        db.commit()
    except:
        pass

def get_group_name(group_id):
    return (sql.execute(f"SELECT name FROM groups WHERE group_id = {group_id}").fetchone())[0]


def get_user(message):
    return sql.execute(f"SELECT * FROM users WHERE user_id = {message.chat.id}").fetchone()

def get_user2(callback):
    return sql.execute(f"SELECT name, first_name FROM users WHERE user_id = {callback.from_user.id}").fetchone()
    
def update_name(message):
    sql.execute(f'UPDATE users SET name = "{message.text}" WHERE user_id = {message.chat.id}')
    db.commit()

def update_last_name(message):
    sql.execute(f'UPDATE users SET first_name = "{message.text}" WHERE user_id = {message.chat.id}')
    db.commit()

def get_admin_list():
    list_admins = []
    for i in sql.execute(f"SELECT user_id FROM users WHERE admin = 1").fetchall():
        list_admins.append(i[0])
    return list_admins

def create_tasks(message):
    id_task = random.randint(11111111111111, 9999999999999999)
    sql.execute(f"INSERT INTO tasks VALUES({id_task}, '{message.text}', '0','{message.chat.id}','0','0','0','0', '0', 0)")
    db.commit()
    return id_task

def change_task(task_id, element, key):
    sql.execute(f"UPDATE tasks SET {element} = '{key}' WHERE task_id = {task_id}")
    db.commit()

def add_groups():
    a = 'PRO'
    list_groups = ['Культ', 'Политех', 'Дело']
    for i in list_groups:
        sql.execute(f"INSERT INTO groups VALUES({random.randint(11111,999999999)}, '{a+i}', '0')")
    db.commit()

def get_groups_task(callback):
    group_id = sql.execute(f"SELECT group_id FROM users WHERE user_id = {callback.from_user.id}").fetchone()
    print(group_id)
    list_tasks = []
    for i in sql.execute(f"SELECT task_id, name FROM tasks WHERE group_id = '{group_id[0]}' AND executor = '0'").fetchall():
        print(i)
        list_tasks.append({'task_id' : i[0], 'name' : i[1]})
    print(list_tasks)
    return list_tasks

def get_groups_task_id(callback):
    group_id = sql.execute(f"SELECT group_id FROM users WHERE user_id = {callback.from_user.id}").fetchone()
    print(group_id)
    list_tasks = []
    for i in sql.execute(f"SELECT task_id FROM tasks WHERE group_id = '{group_id[0]}'").fetchall():
        print(i)
        list_tasks.append(i[0])
    print(list_tasks)
    return list_tasks

def get_take_task(callback):
    a = callback.data
    a = a.replace('ok', '')
    a = a.replace('take', '')
    print(a)
    task = sql.execute(f"SELECT name, description, bonus, status, deadline FROM tasks WHERE task_id = {int(a)} AND status = 0").fetchone()
    if task:
        list_param = {
            'name' : task[0],
            'descript' : task[1],
            'bonus' : task[2],
            'status' : task[3],
            'deadline' : task[4]
        }
        return list_param
    else:
        return False
def take_task(callback):
    task_id = (callback.data).replace('take', '')
    task = sql.execute(f"SELECT task_id FROM tasks WHERE task_id = {task_id} AND executor = '0'").fetchone()
    if task:
        sql.execute(f"UPDATE tasks SET executor = '{callback.from_user.id}' WHERE task_id = {task_id} AND executor = '0'")
        db.commit()
        return True

    else:
        return False

def get_my_tasks(callback):
    tasks = sql.execute(f"SELECT name, task_id FROM tasks WHERE executor = {callback.from_user.id} AND status = '0'").fetchall()
    list_tasks = []
    for i in tasks:
        list_tasks.append({'task_id' : int(i[1]), 'name': i[0]})
    return list_tasks

def get_task_take(callback, task_id):
    executor = sql.execute(f"SELECT executor FROM tasks WHERE task_id = {task_id.replace('ok', '')}").fetchone()
    if callback.from_user.id == int(executor[0]):
        return True
    else:
        return False

def ok_task(callback, bonus):
    print(callback.data)
    sql.execute(f"UPDATE users SET balance = balance + {bonus} WHERE user_id = {callback.from_user.id}")
    sql.execute(f"UPDATE tasks SET status = 1 WHERE task_id = {callback.data.replace('ok', '')}")
    print('отмечено выполенным')
    db.commit()

def get_groups():
    groups = sql.execute(f"SELECT group_id, name FROM groups").fetchall()
    list_groups = []
    for i in groups:
        list_groups.append({'name': i[1], 'group_id' : i[0]})
    return list_groups

def get_users_in_group(group_id):
    print(group_id)
    user = sql.execute(f"SELECT name, first_name, user_id FROM users WHERE group_id = {group_id}").fetchall()
    list_users = []
    print(user)
    for i in user:
        print(i)
        list_users.append({
            'name' : i[0]+ ' ' + i[1], 
            'user_id' : i[2]
        })
    return list_users

def give_task(user_id, task_id):
    sql.execute(f"UPDATE tasks SET executor = '{user_id}' WHERE task_id = {task_id}")
    db.commit()

def rate_users():
    users = sql.execute(f'SELECT name, balance FROM users').fetchall()
    rate = []
    for i in users:
        rate.append({'name' : i[0], 'balance': i[1]})
    print(rate)
    return rate



def get_task(task_id):
    task = sql.execute(f"SELECT name, description, bonus FROM tasks WHERE task_id = {task_id}").fetchone()
    return {'name' : task[0], 'desc': task[1], 'bonus' : task[2]}

create_base()
#add_groups()

