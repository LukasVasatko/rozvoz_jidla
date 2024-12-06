from flask import Flask, redirect, url_for, render_template, request, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import logging


app = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)
app.logger.debug('Flash volán')

zakladni_cesta = os.path.dirname(os.path.abspath(__file__))
cesta = os.path.join(zakladni_cesta, "databaze.db")
conn = sqlite3.connect(cesta)
cursor = conn.cursor()

def get_db_connection():
    conn = sqlite3.connect(cesta)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home1():
    return redirect(url_for('domu'))

@app.route('/domu')
def domu():
    return render_template('index.html')

@app.route('/registrace', methods=['GET', 'POST'])
def registrace():
    if request.method == 'POST':
        jmeno = request.form['jmeno']
        prijmeni = request.form['prijmeni']
        email = request.form['email']
        telefon = request.form['telefon']
        heslo = request.form['heslo']
        heslo_znova = request.form['heslo_znova']
        role = 'Uzivatel'

        if heslo != heslo_znova:
            flash('Hesla se neshodují. Zkuste to znovu.', 'error')
            return render_template('registrace.html')

        hashed_password = generate_password_hash(heslo)

        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO uzivatele (jmeno, prijmeni, email, telefon, heslo, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (jmeno, prijmeni, email, telefon, hashed_password, role))
            conn.commit()
            flash('Registrace byla úspěšná! Můžete se přihlásit.', 'success')
            return redirect(url_for('prihlaseni'))
        except sqlite3.IntegrityError:
            flash('E-mail je již registrován. Zkuste jiný e-mail.', 'error')
        finally:
            conn.close()

    return render_template('registrace.html')

@app.route('/prihlaseni')
def prihlaseni():
    return render_template('prihlaseni.html') 

@app.route('/restaurace')
def restaurace():
    return render_template('restaurace.html')    

@app.errorhandler(404)
def nenalezeno(e):
    return render_template('error404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)

