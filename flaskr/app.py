from flask import Flask, redirect, render_template, request, url_for, session, jsonify, flash
import requests
from supabase_client import supabase

from emails import sendEmail
from users import *
from genPdf import *
from movements import *

app = Flask(__name__)
app.secret_key = 'SupaSecret'


# definição de rotas de view(frontend)
@app.route('/')
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

@app.route('/confirmPayment')
def confirmPayment():
    data = {
        'title': 'Pagamentos',
        'page': 'Confirmar Pagamento',
        'entity_name': session['entity_name'],
        'amount': session['amount'],
        }
    return render_template('confirm_payment.html', data=data)

@app.route('/transfer')
def transfer():
    data = {
        'title': 'Transferências',
        'page': 'Nova Transferência',
        'message': request.args.get('message')
    }
    return render_template('transfers.html', data=data)

@app.route('/confirmTransfer')
def confirmTransfer():
    data = {
        'title': 'Transferências',
        'page': 'Confirmar Transferência',
        'iban': session['iban'],
        'amount': session['amount'],
        }
    return render_template('confirm_transfer.html', data=data)

@app.route('/sendEmail')
def SendEmail():
    return render_template('confirm_email.html', data='Email Enviado')

# API routes(backend)
@app.route('/login', methods=['POST'])
def login():
    # limpa os dados de sessao
    session.clear()
    try:
        # vai buscar os dados que foram introduzidos no forma do frontend
        email = request.form["email"]
        password = request.form["password"]
        #guarda o email nos dados da sessao
        session['email'] = email

        # faz login do utilizador com os metodos do supabase
        res = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password,
        })
        
        # verifica se o login foi bem sucedido e guarda o id numa variavel 
        # para redirecionar para dashboard do utilizador
        if res.session:
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
    #logout com os metodos do supabase
    response = supabase.auth.sign_out()
    # limpa os dados da sessao
    session.clear()
    return redirect('../')

@app.route('/createUser', methods=['POST'])
def createUser():

    # vai buscar os dados do form de registo para fazer o registo no supabase
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

    return render_template('index.html', data='HomePage')

@app.route('/create_account', methods=['POST'])
def createAcc():
    iban = createIban(create_user_number())
    id = session['user_id']
    getAccountType = request.form['account_type']
    value = request.form['account_amount']

    accountType = ''

    if getAccountType == 'conta_poupanca':
        accountType = 'Conta Poupança'
    elif getAccountType == 'conta_universitarios':
        accountType = 'Conta para Universitários'
    elif getAccountType == 'conta_empresarial':
        accountType = 'Conta Bancária Empresarial'
    elif getAccountType == 'conta_jovem':
        accountType = 'Conta Jovem (para menores)'

    accountAmount = (
        supabase.table('user_bank_acc')
        .select('acc_amount')
        .eq('acc_type', 'Conta à Ordem')
        .eq('user_id', id)
        .execute()
    )
    print(accountAmount)

    if value == '':
        value = 0

    if float(accountAmount.data[0]["acc_amount"]) < float(value):
        message = "Saldo da conta a ordem insuficiente para abertura de nova conta"
        #TODO : ISTO TA TUDO FODIDO
        
        flash(message)
        return render_template('create_account.html', data='data')



    data = {
        'acc_amount' : float(accountAmount.data[0]["acc_amount"]) - float(value)
    }

    response = (supabase.table('user_bank_acc') \
        .update(data)
        .match({'user_id': id, 'acc_type': 'Conta à Ordem'})
        .execute())
                

    data = {
        'acc_type': accountType,
        'acc_amount': value,
        'user_id': id, 
        'acc_iban': iban, 
    }
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
        .select('name, entity_number, id') \
        .eq('entity_number', paymentData['entity']) \
        .execute()

    session['entity_name'] = entity.data[0]['name']
    session['entity_number'] = entity.data[0]['entity_number']
    session['entity_id'] = entity.data[0]['id']
    session['amount'] = paymentData['amount']

    try:
        if int(entity.data[0]['entity_number']) == int(paymentData['entity']):
            # verificar saldo da conta do utilizador
            accBalance = supabase.table('user_bank_acc') \
                        .select('id', 'acc_amount , acc_type') \
                        .eq('user_id', id) \
                        .execute()


            for acc in accBalance.data:
                if acc['acc_type'] == 'Conta à Ordem':
                    if float(acc['acc_amount']) >= float(paymentData['amount']):
                        session['acc_amount'] = float(acc['acc_amount'])
                        session['acc_id'] = acc['id']
                        return redirect('/confirmPayment')
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

@app.route('/executePayment', methods=['POST'])
def executePayment():
    #TODO: falta fazer o registo do pagamento na base de dados
    data = {
        'title': 'Pagamentos',
        'page': 'Confirmar Pagamento',
        'entity_name': session['entity_name'],
        'entity_number': session['entity_number'],
        'amount': session['amount'],
        }

    newAmount = float(session['acc_amount']) - float(session['amount'])

    supabase.table('user_bank_acc') \
                .update({'acc_amount': newAmount}) \
                .eq('id', session['acc_id']) \
                .execute()

    supabase.table('payments_history') \
        .insert({
            'user_bank_acc_id': session['acc_id'],
            'user_id': session['user_id'],
            'entity_id': session['entity_id'],
            'amount': session['amount'],
            'date': datetime.now().isoformat(),
            })\
        .execute()

    #TODO: redirecionar para dashboard
    return redirect(f'dashboard/{session["user_id"]}')

@app.route('/transfer', methods=['POST'])
def verifyTransfer():
    id = session['user_id']
    transferData = getTransferData()
    iban = supabase.table('user_bank_acc')\
        .select('acc_iban')\
        .eq('acc_iban', transferData['iban'])\
        .execute()

    session['amount'] = transferData['amount']
    session['iban'] = transferData['iban']

    try:
        if int(transferData['iban']) == iban.data[0]['acc_iban']:
            accBalance = supabase.table('user_bank_acc')\
                        .select('id', 'acc_amount, acc_type, acc_iban')\
                        .eq('user_id', id)\
                        .execute()

            for acc in accBalance.data:
                if acc['acc_type'] == 'Conta à Ordem':
                    if float(acc['acc_amount']) >= float(transferData['amount']):
                        # guarda os valores nos dados da sessão
                        session['acc_amount'] = float(acc['acc_amount'])
                        session['sender_iban'] = float(acc['acc_iban'])
                        session['acc_id'] = acc['id']
                        print(session['acc_id'])
                        print(session['acc_amount'])
                        return redirect('/confirmTransfer')
                    else:
                        data = {
                            'balance': 'Saldo Insuficiente'
                        }
                        return redirect(url_for('transfer', message=data['balance']))
    except:
        data = {
            'iban': 'Iban incorreto'
        }
        return redirect(url_for('transfer', message=data['iban']))

@app.route('/executeTransfer', methods=['POST'])
def executeTransfer():
    #TODO: falta fazer o registo da transferancia na base de dados
    data = {
        'title': 'Transferências',
        'page': 'Confirmar Transferência',
        'iban': session['iban'],
        'amount': session['amount'],
        }

    newAmountOrig = float(session['acc_amount']) - float(session['amount'])

    supabase.table('user_bank_acc') \
                .update({'acc_amount': newAmountOrig}) \
                .eq('id', session['acc_id']) \
                .execute()

    response = supabase.table('user_bank_acc') \
        .select('acc_amount') \
        .eq('acc_iban', session['iban']) \
        .execute()

    newAmountDest = float(response.data[0]['acc_amount']) + float(session['amount'])

    supabase.table('user_bank_acc') \
        .update({'acc_amount': newAmountDest}) \
        .eq('acc_iban', session['iban']) \
        .execute()

    sender_id = supabase.table('user_bank_acc') \
        .select('id')\
        .eq('acc_iban', session['sender_iban'])\
        .execute()

    receiver_id = supabase.table('user_bank_acc') \
        .select('id') \
        .eq('acc_iban', session['iban']) \
        .execute()

    supabase.table('transfers_history')\
        .insert({
            'amount': session['amount'],
            'date': datetime.now().isoformat(),
            'sender_acc_id': sender_id.data[0]['id'],
            'receiver_acc_id': receiver_id.data[0]['id'],
            'user_id': session['user_id'],
    })\
    .execute()

    #TODO: redirecionar para dashboard
    return redirect(f'dashboard/{session["user_id"]}')

@app.route("/sendAccMovements", methods=['POST'])
def sendAccMovements():

    #TODO: grab email to send email
    accIban = request.form['acc_iban']

    #create a pdf with account movements
    generatePDF(accIban)
    data = {
        "to": session['email'],
        "subject": accIban,
    }
    try:
        sendEmail(data)
        return redirect('/sendEmail')

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route("/voltar", methods=['POST'])
def voltar():
    return redirect(f'dashboard/{session["user_id"]}')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
