from flask import Flask, render_template, request, jsonify
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

@app.route('/login')
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    response = supabase.auth.sign_in_with_password({
        'email': email,
        'password': password,
    })
    return jsonify({"message": "User Loged In succesfully"}), 201

@app.route('/createUser', methods=['POST'])
def createUser():
    data = request.get_json()

    # Extract email and password from the data
    email = data.get('email')
    password = data.get('password')

    response = supabase.auth.sign_up({
        'email': email,
        'password': password,
    })

    return jsonify({"message": "User created successfully"}), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
