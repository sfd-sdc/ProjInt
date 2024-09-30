from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    data = {
        'title': 'Projecto Inegrado',
        'header': 'Home Page do Projecto Integrado',
        'page': 'My Page'
    }
    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
