from flask import Flask, redirect, render_template, request, url_for, session 
from supabase_client import supabase
from random import randint

app = Flask(__name__)
app.secret_key = 'SupaSecret'

def Home():
    message = 'Welcome to SDC Bank'
    data = {
        'title' : 'Home',
        'navTitle' : 'SDC Bank',
        'message': message
    }
    return render_template('index.html', data=data)

@app.route('/signup')
def singup():
    return render_template('signup.html', data='Novo Utilizador')

@app.route('/signin')
def signin():
    return render_template('login.html', data='Login')

@app.route('/createAccount', methods=['POST'])
def createNewAcc():
    return render_template('create_account.html', data='data')

@app.route('/dashboard/<id>', methods=['GET'])
def dashboard(id):
    global idData
    try:
        user_acc = getUserAcc(id)
        idData = getUser(id)
        session['user_id'] = id
        return render_template('user_dashboard.html', data=[idData, user_acc])
    except:
        data = {
            'title' : 'Login',
            'navTitle' : 'SDC Bank',
            'message': 'You need to login'
        }
        return redirect('../signin')

@app.route('/pay')
def pay():
    data = {
        'title': 'Pagamentos',
        'page': 'Novo Pagamento',
        'message': request.args.get('message')
    }
    return render_template('payments.html', data=data)

@app.route('/confirm')
def confirm():
    data = {
        'title': 'Pagamentos',
        'page': 'Confirmar Pagamento',
        'entity_name': session['entity_name'],
        'amount': session['amount'],
        }
    return render_template('confirm_payment.html', data=data)


#-------------------------------Definir número de utilizador-----------------------------
# API routes
@app.route('/login', methods=['POST'])
def login():
    session = None
    try:
        email = request.form["email"]
        password = request.form["password"]
        session = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password,
        })

        if session.session:
            response = supabase.table('users') \
            .select('id') \
            .eq('user_email', email) \
            .execute()

            id = response.data[0]['id']
            return redirect(f'/dashboard/{id}')
        else:
            data = {
                'title' : 'Login',
                'navTitle' : 'SDC Bank',
                'message': 'You need to login'
            }
            return redirect(url_for('../login', data=data))
    except:
        data = {
            'title' : 'Login',
            'navTitle' : 'SDC Bank',
            'message': 'Email ou Password incorrectos'
        }
        return render_template('login.html', data=data)

@app.route('/logout', methods=['GET'])
def logout():
    response = supabase.auth.sign_out()
    session.clear()
    return redirect('../signin')
@app.route('/createUser', methods=['POST'])
def createUser():
    # data = request.get_json()

    # Extract email and password from the data
    email = request.form["email"]
    password = request.form["password"]

    response = supabase.auth.sign_up({
        'email': email,
        'password': password,
    })
    try:
        userId = insert_user()
        userNumber = create_user_number()
        createBankAcc(userId, userNumber)
    except Exception as e:
        print ("An error occurred:", str(e))

    #TODO: construct a page with information to user go to email for confirmation
    return render_template('index.html', data='HomePage')

@app.route('/create_account', methods=['POST'])
def createAcc():
    iban = createIban(create_user_number())
    id = session['user_id']
    getAccountType = request.form['account_type']

    accountType = ''

    if getAccountType == 'conta_ordem':
       accountType = 'Conta à Ordem'
    elif getAccountType == 'conta_base':
        accountType = 'Conta Base'
    elif getAccountType == 'conta_sevicos_minimos':
        accountType = 'Conta Serviços Mínimos Bancários'
    elif getAccountType == 'conta_poupanca':
        accountType = 'Conta Poupança'
    elif getAccountType == 'conta_ordenado':
        accountType = 'Conta Ordenado'
    elif getAccountType == 'conta_universitarios':
        accountType = 'Conta para Universitários'
    elif getAccountType == 'conta_empresarial':
        accountType = 'Conta Bancária Empresarial'
    elif getAccountType == 'conta_jovem':
        accountType = 'Conta Jovem (para menores)'

    data = {
        'acc_type': accountType,
        'acc_amount': request.form['account_amount'],
        'user_id': id, 
        'acc_iban': iban, 
    }
    print(data)
    try:
        response = (
            supabase.table('user_bank_acc')
            .insert(data)
            .execute()
        )
        return redirect(f'/dashboard/{id}')
    except Exception as e:
        print ("An error occurred:", str(e))
        return redirect(f'/dashboard/{id}')

@app.route('/payment', methods=['POST'])
def payment():
    id = session['user_id'] 

    # verificar entidade
    paymentData = getPaymentData()
    entity = supabase.table('entitys') \
        .select('name, entity_number') \
        .eq('entity_number', paymentData['entity']) \
        .execute()

    session['entity_name'] = entity.data[0]['name']
    session['entity_number'] = entity.data[0]['entity_number']
    session['amount'] = paymentData['amount']

    try:
        if entity.data[0]['entity_number'] == int(paymentData['entity']):
            # verificar saldo da conta do utilizador
            accBalance = supabase.table('user_bank_acc') \
                        .select('acc_amount , acc_type') \
                        .eq('user_id', id) \
                        .execute()


            for acc in accBalance.data:
                if acc['acc_type'] == 'Conta à ordem':
                    if float(acc['acc_amount']) >= float(paymentData['amount']):
                        session['acc_amount'] = float(acc['acc_amount'])
                        return redirect('/confirm')
                    else:
                        data = {
                            'balance': 'Saldo Insuficiente'
                        }
                    return redirect(url_for('pay', message=data['balance']))
    except:
        data = {
            'entity': 'Entidade não encontrada'
        }
        return redirect(url_for('pay', message=data['entity']))

@app.route('/confirmPayment', methods=['POST'])
def confirmPayment():
    data = {
        'title': 'Pagamentos',
        'page': 'Confirmar Pagamento',
        'entity_name': session['entity_name'],
        'entity_number': session['entity_number'],
        'amount': session['amount'],
        }

    newAmount = float(session['acc_amount']) - float(session['amount'])

    updateAcc = supabase.table('user_bank_acc') \
                .update({'acc_amount': newAmount}) \
                .eq('user_id', session['user_id']) \
                .execute()
    #TODO: redirecionar para dashboard
    return redirect(f'dashboard/{session["user_id"]}')

# ------------------------------------------------------------------------
def getUser(id):
    response = supabase.table('users') \
    .select('user_fullname, user_birthdate, user_address, user_phone, user_email') \
    .eq('id', id) \
    .execute()
    return response.data[0]

def getUserAcc(id):
    response = supabase.table('user_bank_acc') \
    .select('acc_type, acc_amount') \
    .eq('user_id', id) \
    .execute()
    return response.data

def create_user_number():
    bank_code = "8226"
    # Gera o número de utilizador
    user_number = randint(0, 999999)
    user_final_number = f"{bank_code}{user_number:06}"
    return user_final_number

def createIban(user_num):
    randNum = randint(0, 999)
    iban = f'{user_num}{randNum:03}'
    # print(iban) 
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

    res = (
        supabase.table("users")
        .insert(data)
        .execute()
    )
    return res.data[0]['id']

    # criacao conta bancaria default
def createBankAcc(id, create_user_number):
    acc = {
        'acc_type': 'Conta à ordem',
        'acc_amount': 0.00,
        'user_id': id,
        'acc_iban': createIban(create_user_number),
    }
    response = (
        supabase.table("user_bank_acc")
        .insert(acc)
        .execute()
    )

def getPaymentData():
    paymentData = {
        'entity': request.form['entity'],
        'amount': request.form['amount']
    }
    return paymentData

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
