from random import randint
from supabase_client import supabase
from flask import request
from datetime import datetime

def getUser(id):
    response = supabase.table('users') \
    .select('user_fullname, user_birthdate, user_address, user_phone, user_email') \
    .eq('id', id) \
    .execute()

    date = datetime.strptime(response.data[0]['user_birthdate'], '%Y-%m-%d')

    data = {
        'user_fullname': response.data[0]['user_fullname'],
        'user_birthdate': date.strftime('%d/%m/%Y'),
        'user_address': response.data[0]['user_address'],
        'user_phone': response.data[0]['user_phone'],
        'user_email': response.data[0]['user_email']
    }
    return data

def getUserAcc(id):
    response = supabase.table('user_bank_acc') \
    .select('acc_type, acc_amount, acc_iban') \
    .eq('user_id', id) \
    .execute()
    return response.data

def create_user_number():
    def generate_number():
        bank_code = "8226"
        user_number = randint(0, 999999)
        return f"{bank_code}{user_number:06}"
    def is_unique_user_number(user_number):
        # Verifica se o número já existe na tabela
        response = supabase.table('users').select('user_num').eq('user_num', user_number).execute()
        return len(response.data) == 0
    def generate_unique_number():
        number = generate_number()
        if is_unique_user_number(number):
            return number
        return generate_unique_number()  # Chamada recursiva até encontrar um número único

    return generate_unique_number()

def createIban(user_num):
    randNum = randint(0, 999)
    iban = f'{user_num}{randNum:03}'
    return iban

def insert_user():
    number = create_user_number()
    data = {'user_email': request.form['email'],
            'user_fullname': request.form['fullname'],
            'user_address': request.form['address'],
            'user_doc_num': request.form['num'],
            'user_birthdate': request.form['date'],
            'user_phone': request.form['phone'],
            'user_num': number,
            }
    print(data)

    res = (
        supabase.table("users")
        .insert(data)
        .execute()
    )
    return res.data[0]['id']

    # criacao conta bancaria default
def createBankAcc(id, create_user_number):
    acc = {
        'acc_type': 'Conta à Ordem',
        'acc_amount': 250.00,
        'user_id': id,
        'acc_iban': createIban(create_user_number),
    }
    response = (
        supabase.table("user_bank_acc")
        .insert(acc)
        .execute()
    )
