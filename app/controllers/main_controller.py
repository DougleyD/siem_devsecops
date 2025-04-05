from flask import Blueprint, render_template, redirect

app = Blueprint('main', __name__)

@app.route('/', methods=['GET'])
def root():
    return redirect('/login')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html', title='Login')

@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html', title='Register')

@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html', title='Home')