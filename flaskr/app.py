from flask import Flask, redirect, render_template, request, url_for, session, jsonify
import requests
from supabase_client import supabase
from fpdf import FPDF
import resend
import os
from users import *

app = Flask(__name__)
app.secret_key = 'SupaSecret'

@app.route('/')
def Home():
    message = 'Welcome to SDC Bank'
    data = {
        'title' : 'Home',
        'navTitle' : 'SDC Bank',
        'message': message
    }
    return render_template('index.html', data=data)

@app.route('/testEmail')
def testEmail():
    data = generatePDF()
    return render_template('email.html', data=data)

@app.route('/signup')
def singup():
    return render_template('signup.html', data='Novo Utilizador')

@app.route('/signin')
def signin():
    return render_template('login.html', data='Login')

@app.route('/createAccount', methods=['GET'])
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
        .select('acc_amount, user_id(id)')
        .eq('acc_type', 'Conta à Ordem')
        .execute()
    )

    if value == '':
        value = 0

    if float(accountAmount.data[0]["acc_amount"]) < float(value):
        data = {
            'message' : "Saldo da conta a ordem insuficiente para abertura de nova conta"
        }
        #TODO : ISTO TA TUDO FODIDO
        return redirect(url_for('../createAccount', data = data))


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
                        .select('id', 'acc_amount , acc_type') \
                        .eq('user_id', id) \
                        .execute()


            for acc in accBalance.data:
                if acc['acc_type'] == 'Conta à ordem':
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
        #TODO: falta fazer o registo do pagamento na base de dados
        'amount': session['amount'],
        }

    newAmount = float(session['acc_amount']) - float(session['amount'])

    updateAcc = supabase.table('user_bank_acc') \
                .update({'acc_amount': newAmount}) \
                .eq('id', session['acc_id']) \
                .execute()
    #TODO: redirecionar para dashboard
    return redirect(f'dashboard/{session["user_id"]}')

@app.route('/transfer', methods=['POST'])
def verifyTranfer():
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
                        .select('id', 'acc_amount, acc_type')\
                        .eq('user_id', id)\
                        .execute()

            for acc in accBalance.data:
                if acc['acc_type'] == 'Conta à ordem':
                    if float(acc['acc_amount']) >= float(transferData['amount']):
                        session['acc_amount'] = float(acc['acc_amount'])
                        session['acc_id'] = acc['id']
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

    updateAcc = supabase.table('user_bank_acc') \
                .update({'acc_amount': newAmountOrig}) \
                .eq('id', session['acc_id']) \
                .execute()

    response = supabase.table('user_bank_acc') \
        .select('acc_amount') \
        .eq('acc_iban', session['iban']) \
        .execute()

    newAmountDest = float(response.data[0]['acc_amount']) + float(session['amount'])

    updateAcc = supabase.table('user_bank_acc') \
        .update({'acc_amount': newAmountDest}) \
        .eq('acc_iban', session['iban']) \
        .execute()

    #TODO: redirecionar para dashboard
    return redirect(f'dashboard/{session["user_id"]}')

GO_APP_URL = 'http://localhost:8080/send-email'

@app.route("/sendAccMovements", methods=['POST'])
def sendAccMovements():
    #create a pdf with account movements
    generatePDF()

    data = {
        "to": request.form["to"],
        "subject": request.form["subject"],
        "html": request.form["content"]
    }
    try:
        sendEmail()
        # response = requests.post(GO_APP_URL, json=data)
        # response.raise_for_status()
        return jsonify('Email Sent')
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

# ------------------------------------------------------------------------
def getPaymentData():
    paymentData = {
        'entity': request.form['entity'],
        'amount': request.form['amount']
    }
    return paymentData

def getTransferData():
    transferData = {
        'iban': request.form['iban'],
        'amount': request.form['amount']
    }
    return transferData

def generatePDF():
    f = open("files/movimentos.txt", "w")

    f.write("Movimentos\n")
    f.write("Conta Origem - Conta Destino/Entidade - Valor - Data\n")
    f.write("------------------------------------------------------------------------------------\n")

    f.close()

    data = supabase.table('payments_history') \
        .select('users(user_fullname), entitys(name), amount, date') \
        .eq('user_id', '1a8c52f2-423c-46dc-b7f4-93ca663a2316') \
        .execute()

    f = open("files/movimentos.txt", "a")

    for i in range(len(data.data[0]) - 3):
        fDataPayments = {'name': data.data[i]['users']['user_fullname'],
             'entity': data.data[i]['entitys']['name'],
             'paymentAmount': data.data[i]['amount'],
             'paymentDate': data.data[i]['date']}
        for key, value in fDataPayments.items():
            f.write(f"{value}   ")
        f.write("\n")

    data = supabase.table('transfers_history') \
        .select('users(user_fullname), receiver_acc_id(user_id(user_fullname)), amount, date') \
        .eq('user_id', '1a8c52f2-423c-46dc-b7f4-93ca663a2316') \
        .execute()

    for i in range(len(data.data[0]) - 1):
        fDataTransfers = {'sender_name': data.data[i]['users']['user_fullname'],
                 'receiver_name': data.data[i]['receiver_acc_id']['user_id']['user_fullname'],
                 'transferAmount': data.data[i]['amount'],
                 'transferDate': data.data[i]['date']}
        for key, value in fDataTransfers.items():
            f.write(f"{value}   ")
        f.write("\n")


    f.close()

    #TODO: Need to change this 
    txt_file = "files/movimentos.txt"
    pdf_file = "files/movimentos.pdf"

# Criação do objeto PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

# Leitura do arquivo de texto
    with open(txt_file, 'r', encoding='utf-8') as file:
        for line in file:
            pdf.multi_cell(0, 10, line)

# Salvando o arquivo PDF
    pdf.output(pdf_file)
    return(f"Arquivo PDF '{pdf_file}' criado com sucesso.")

def sendEmail():
    resend.api_key = "re_9cJvnsx4_NYH1LWM7VW4hgdWGcpzYB5cg"

    f: bytes = open(
        #Change path acording to your os. This is for linux
        os.path.join(os.path.dirname(__file__), "../files/movimentos.pdf"), "rb"
    ).read()

    attachment: resend.Attachment = {"content": list(f), "filename": "movimentos.pdf"}

    params: resend.Emails.SendParams = {
        "from": "pedro.santo@pedrosanto.pt",
        "to": "pedro.bb.90@gmail.com",
        "subject": "SDC Bank",
        "html": "<strong>SDC Bank</strong>\n \
      <p>Aqui está o estrato das suas contas</p> \
      <p>Obrigado por usar o SDC Bank</p>",
        "attachments": [attachment],

    }

    email: resend.Email = resend.Emails.send(params)
    return email

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
