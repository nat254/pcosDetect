from flask import Flask, render_template, request, redirect, session, flash, url_for
import pickle
from sqlite3 import *
import sqlite3
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import create_engine, text
from flask_mysqldb import MySQL
from functools import wraps
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_DB'] = 'pcos'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost:3306/pcos'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)
#
# connection_string = "mysql+mysqlconnector://root:''@localhost:3306/pcos"
# engine = create_engine(connection_string, echo=True)

app.secret_key = 'pcos'

FLASK_ENV = 'development'
FLASK_DEBUG = True

# def get_db_connection():
#     conn = sqlite3.connect('pcos.db')
#     conn.row_factory = sqlite3.Row
#     return conn


pcos_detect = pickle.load(open('cat_model.pkl', 'rb'))

db = MySQL(app)


def fetch_user_id(email):
    cur = db.connection.cursor()
    cur.execute("""SELECT user_id FROM db.users WHERE email = %s""", (email,))
    row = cur.fetchone()
    return row[0]


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Register', 'danger')
            return redirect(url_for('registration'))

    return wrap


@app.route('/')
@is_logged_in
def home():
    return render_template('homepage.html')


@app.route('/history')
@is_logged_in
def history():
    user_id = session.get('user_id')
    cur = db.connection.cursor()
    cur.execute('SELECT * FROM symptoms WHERE user_id = %s', (user_id,))
    data = cur.fetchall()
    return render_template("history.html", data=data)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    status = False
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pass']
        username = request.form['username']
        cur = db.connection.cursor()
        cur.execute("INSERT INTO users (email, password, username) VALUES (%s, %s,%s)", (email, password, username))
        db.connection.commit()
        cur.close()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('registration.html', status=status)


@app.route('/login', methods=['GET', 'POST'])
def login():
    status = True
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pass']
        cur = db.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s and password =%s", (email, password))
        data = cur.fetchone()
        if data:
            session['logged_in'] = True
            session['user_id'] = data['user_id']
            session['username'] = data['username']
            session['email'] = data['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/symptoms', methods=['GET', 'POST'])
@is_logged_in
def symptoms():
    msg = None
    if request.method == "POST" and request.form.get('action') == 'detect':
        folliclenor = int(request.form['folliclenor'])
        weightgainyn = int(request.form['weightgainyn'])
        hairgrowthyn = int(request.form['hairgrowthyn'])
        skindarkeningyn = int(request.form['skindarkeningyn'])

        user_id = session['user_id']
        inputfeatures = [folliclenor, skindarkeningyn, hairgrowthyn, weightgainyn]

        res = pcos_detect.predict([inputfeatures])

        cur = db.connection.cursor()
        cur.execute(
            "INSERT INTO symptoms(user_id,folliclenor, skindarkeningyn, hairgrowthyn, weightgainyn, res) values(%s,%s,%s,%s,%s,%s)",
            (user_id, folliclenor, skindarkeningyn, hairgrowthyn, weightgainyn, res))
        db.connection.commit()
        cur.close()

        msg = res

    return render_template('symptoms.html', msg=msg)


@app.route("/logout")
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
