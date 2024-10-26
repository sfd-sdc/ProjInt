from flask import Flask, redirect, render_template, request, url_for 
from supabase_client import supabase

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

@app.route('/dashboard/<id>', methods=['GET'])
def dashboard(id):
    try:
        data = getUser(id)
        return render_template('user_dashboard.html', data=data)
    except:
        data = {
            'title' : 'Login',
            'navTitle' : 'SDC Bank',
            'message': 'You need to login'
        }
        return redirect('../signin')

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
        print(session.session)
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
    data = {'user_email': request.form['email'],
            'user_fullname': request.form['fullname'],
            'user_address': request.form['address'],
            'user_doc_num': request.form['num'],
            'user_birthdate': request.form['date'],
            'user_phone': request.form['phone']
            }

    response = (
    supabase.table("users")
        .insert(data)
        .execute()
)

    #TODO: construct a page with information to user go to email for confirmation
    return render_template('index.html', data='HomePage')

def getUser(id):
    response = supabase.table('users') \
    .select('user_fullname, user_birthdate, user_address, user_phone, user_email') \
    .eq('id', id) \
    .execute()
    return response.data[0]


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
