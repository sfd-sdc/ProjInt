from flask import Flask, redirect, render_template, request, url_for 
from supabase_client import supabase
from random import randint

app = Flask(__name__)

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
    global idData
    try:
        user_acc = getUserAcc(id)
        idData = getUser(id)
        return render_template('user_dashboard.html', data=[idData, user_acc])
    except:
        data = {
            'title' : 'Login',
            'navTitle' : 'SDC Bank',
            'message': 'You need to login'
        }
        return redirect('../signin')


#-------------------------------Definir número de utilizador-----------------------------
def create_user_number():
    bank_code = "8226"
    # Gera o número de utilizador
    user_number = randint(0, 999999)
    user_final_number = f"{bank_code}{user_number:06}"
    return user_final_number

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
    # criacao conta bancaria default
    return res.data[0]['id']
def createBankAcc(id):
    acc = {
        'acc_type': 'Conta à ordem',
        'acc_amount': 0.00,
        'user_id': id,
    }
    response = (
        supabase.table("user_bank_acc")
        .insert(acc)
        .execute()
    )
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
        createBankAcc(userId)
    except Exception as e:
        print ("An error occurred:", str(e))

    #TODO: construct a page with information to user go to email for confirmation
    return render_template('index.html', data='HomePage')

@app.route('/create_accout')
def createAcc():
    data = {
        'acc_type': request.form['account_type'],
        'acc_amount': request.form['account_amout'],
        'user_id': idData
    }
    response = (
        supabase.table('user_bank_acc')
        .insert(data)
        .execute()
    )
    return redirect('/user_dashboard')

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
    return response.data[0]

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')