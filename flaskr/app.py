from flask import Flask, render_template

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

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
