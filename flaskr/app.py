from flask import Flask, render_template, request
from supabase_client import supabase
app = Flask(__name__)

#TODO: save user`s data in our database
@app.route('/')
def Home():
    message = 'Welcome to SDC Bank'
    data = {
        'title' : 'Home',
        'navTitle' : 'SDC Bank',
        'message': message
    }
    return render_template('index.html', data=data)

@app.route('/user')
def user():
    # os dados a serem mostrados no frontend vao ser obtidos atraves de querys a base de dados
    
    user = {
        'page': 'Dashboard',
        'name' : 'Pedro Santo',
        'email' : 'pedro@pedrosanto.pt',
        'saldo' : '2000'
    }
    return render_template('user.html', data=user)

@app.route('/signup')
def singup():
    return render_template('signup.html', data='Novo Utilizador')

@app.route('/signin')
def signin():
    return render_template('login.html', data='Login')

@app.route('/login', methods=['POST'])
def login():
    # data = request.get_json()
    email = request.form["email"]
    password = request.form["password"]
    response = supabase.auth.sign_in_with_password({
        'email': email,
        'password': password,
    })
    #TODO: redirect to user`s dashboard
    return render_template('index.html', data='HomePage')

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

    #TODO: construct a page with information to user go to email for confirmation
    return render_template('index.html', data='HomePage')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
