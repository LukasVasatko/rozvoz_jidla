from flask import Flask, redirect, url_for, render_template
import sqlite3
import os

app = Flask(__name__)

zakladni_cesta = os.path.dirname(os.path.abspath(__file__))
cesta = os.path.join(zakladni_cesta, "databaze.db")
conn = sqlite3.connect(cesta)
cursor = conn.cursor()

@app.route('/')
def home1():
    return redirect(url_for('domu'))

@app.route('/domu')
def domu():
    return render_template('index.html')

@app.route('/registrace')
def registrace():
    return render_template('registrace.html')

@app.route('/prihlaseni')
def prihlaseni():
    return render_template('prihlaseni.html') 

@app.route('/restaurace')
def restaurace():
    return render_template('restaurace.html')    

@app.errorhandler(404)
def nenalezeno(e):
    return render_template('error404.html')

if __name__ == '__main__':
    app.run(debug=True)

