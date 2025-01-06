from flask import Flask, redirect, url_for, render_template, request, session, flash, get_flashed_messages
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import logging


app = Flask(__name__)
app.secret_key = "a7823468234732n234489cb233257823"

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

def get_user_by_id(idu):
    conn = get_db_connection()
    uziv = conn.execute('SELECT * FROM uzivatele WHERE id_uzivatele = ?', (idu,)).fetchone()
    return uziv



@app.route('/')
def home1():
    return redirect(url_for('domu'))

@app.route('/domu')
def domu():
    return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

@app.route('/registrace', methods=['GET', 'POST'])
def registrace():
    if request.method == 'POST':
        jmeno = request.form['jmeno']
        prijmeni = request.form['prijmeni']
        email = request.form['email']
        telefon = request.form['telefon']
        heslo = request.form['heslo']
        heslo_znova = request.form['heslo_znova']
        role = 'Uživatel'

        if heslo != heslo_znova:
            flash('Hesla se neshodují. Zkuste to znovu.', 'Chyba')
            return render_template('registrace.html', msgs=get_flashed_messages(with_categories=True))

        hashed_password = generate_password_hash(heslo)

        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO uzivatele (jmeno, prijmeni, email, telefon, heslo, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (jmeno, prijmeni, email, telefon, hashed_password, role))
            conn.commit()
            flash('Registrace byla úspěšná! Můžete se přihlásit.', 'Úspěch')
            return render_template('registrace.html', msgs=get_flashed_messages(with_categories=True))
        except sqlite3.IntegrityError:
            flash('E-mail je již registrován. Zkuste jiný e-mail.', 'Chyba')
            return render_template('registrace.html', msgs=get_flashed_messages(with_categories=True))
        finally:
            conn.close()

    return render_template('registrace.html', msgs=get_flashed_messages(with_categories=True))

@app.route('/odhlaseni')
def odhlaseni():
    session.pop('user_id', None)
    session.pop('user_email', None)
    flash('Byli jste úspěšně odhlášeni.', 'Úspěch')
    return redirect(url_for('prihlaseni'))


@app.route('/sprava_restauraci')
def sprava_restauraci():
    if session.get('user_role') != 'Administrátor' and session.get('user_role') != 'Restaurace':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    restaurace = conn.execute('SELECT * FROM restaurace').fetchall()
    conn.close()
    return render_template('sprava_restauraci.html', restaurace=restaurace, msgs=get_flashed_messages(with_categories=True), get_user_by_id=get_user_by_id)

@app.route('/upravit_restauraci/<int:id>', methods=['GET', 'POST'])
def upravit_restauraci(id):
    if session.get('user_role') != 'Administrátor' and session.get('user_role') != 'Restaurace':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    restaurace = conn.execute('SELECT * FROM restaurace WHERE id_restaurace = ?', (id,)).fetchone()

    if not restaurace:
        flash('Restaurace nenalezena!', 'Chyba')
        return redirect(url_for('sprava_restauraci'))

    if request.method == 'POST':
        nazev = request.form['nazev']
        popis = request.form['popis']
        email2 = request.form['email']
        image_url = request.form['url']
        telefon2 = request.form['telefon']
        adresa = request.form['adresa']
        adresa_casti = adresa.split()
        adresa_ulice = adresa_casti[0]
        adresa_ulice_cislo = adresa_casti[1]
        adresa_psc = adresa_casti[2]
        adresa_mesto = " ".join(adresa_casti[3:])

        if not nazev or not adresa:
            flash('Všechna pole jsou povinná!', 'Chyba')
        else:
            conn.execute('''UPDATE restaurace 
                            SET nazev = ?, popis = ?, email = ?, telefon = ?, 
                                adresa_ulice = ?, adresa_cislo_domu = ?, adresa_psc = ?, 
                                adresa_mesto = ?, image_url = ?
                            WHERE id_restaurace = ?''',
                         (nazev, popis, email2, telefon2, adresa_ulice, adresa_ulice_cislo, 
                          adresa_psc, adresa_mesto, image_url, id))
            conn.commit()
            conn.close()
            flash('Restaurace byla úspěšně upravena!', 'Úspěch')
            return redirect(url_for('sprava_restaurace', restaurace_id=id))

    conn.close()
    return redirect(url_for('sprava_restauraci'))


@app.route('/sprava_restaurace/<int:restaurace_id>')
def sprava_restaurace(restaurace_id):
    if session.get('user_role') != 'Administrátor' and session.get('user_role') != 'Restaurace':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    restaurace = conn.execute('SELECT * FROM restaurace WHERE id_restaurace = ?', (restaurace_id,)).fetchone()
    conn.close()
    return render_template('sprava_restaurace.html', restaurace=restaurace, restaurace_id=restaurace_id, msgs=get_flashed_messages(with_categories=True))

@app.route('/pridat_restauraci', methods=['GET', 'POST'])
def pridat_restauraci():
    if session.get('user_role') != 'Administrátor' and session.get('user_role') != 'Restaurace':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    if request.method == 'POST':
        nazev = request.form['nazev']
        popis = request.form['popis']
        email2 = request.form['email']
        image_url = request.form['url']
        telefon2 = request.form['telefon']
        spravce = session.get('user_id')
        adresa = request.form['adresa']
        adresa_casti = adresa.split()
        adresa_ulice = adresa_casti[0]
        adresa_ulice_cislo = adresa_casti[1]
        adresa_psc = adresa_casti[2]
        adresa_mesto = " ".join(adresa_casti[3:])

        if not nazev or not adresa or not spravce:
            flash('Všechna pole jsou povinná!', 'Chyba')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO restaurace (nazev, popis, email, telefon, adresa_ulice, adresa_cislo_domu, adresa_psc, adresa_mesto, image_url, id_spravce) VALUES (? , ? , ? , ? , ? , ? , ? , ? , ? , ?)',
                         (nazev, popis, email2, telefon2, adresa_ulice, adresa_ulice_cislo, adresa_psc, adresa_mesto, image_url, spravce))
            conn.commit()
            conn.close()
            flash('Restaurace byla úspěšně přidána!', 'Úspěch')
            return redirect(url_for('sprava_restauraci'))

    return render_template('sprava_restauraci.html', pridavani=True)

@app.route('/pridat_produkt/<int:restaurace_id>', methods=['GET', 'POST'])
def pridat_produkt(restaurace_id):
    if session.get('user_role') != 'Administrátor' and session.get('user_role') != 'Restaurace':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    if request.method == 'POST':
        nazev = request.form['nazev']
        url = request.form['url']
        prodej_povolen = request.form['prodej_povolen']
        cena = request.form['cena']
        popis = request.form['popis']

        if not nazev or not cena or not url or not prodej_povolen:
            flash('Chybí ti povinné údaje!', 'Chyba')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO produkty (nazev, cena, popis, restaurace_id) VALUES (?, ?, ?, ?)',
                         (nazev, cena, popis, restaurace_id))
            conn.commit()
            flash('Produkt byl úspěšně přidán!', 'Úspěch')
            if prodej_povolen == '1':
                flash('Nabídka pro produkt byla úspěšně vytvořena s požadovanou cenou! Nyní je v prodeji.', 'Úspěch')
                conn.execute('INSERT INTO nabidka (nazev, cena, popis, restaurace_id) VALUES (?, ?, ?, ?)',
                         (nazev, cena, popis, restaurace_id))
                conn.commit()
            conn.close()
            return redirect(url_for('sprava_restaurace', restaurace_id=restaurace_id))

    return render_template('sprava_restaurace.html', pridavani=True, restaurace_id=restaurace_id, msgs=get_flashed_messages(with_categories=True))


@app.route('/smazat_produkt/<int:produkt_id>', methods=['GET'])
def smazat_produkt(produkt_id):
    if session.get('user_role') != 'Administrátor' and session.get('user_role') != 'Restaurace':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    produkt = conn.execute('SELECT id_restaurace FROM produkty WHERE id_produktu = ?', (produkt_id,)).fetchone()
    if produkt:
        conn.execute('DELETE FROM produkty WHERE id_produktu = ?', (produkt_id,))
        conn.commit()
        flash('Produkt byl úspěšně smazán!', 'Úspěch')
    else:
        flash('Produkt nebyl nalezen.', 'Chyba')
    conn.close()
    return redirect(url_for('sprava_restaurace', restaurace_id=produkt['id_restaurace']))

@app.route('/smazat_restauraci/<int:restaurace_id>', methods=['GET'])
def smazat_restauraci(restaurace_id):
    if session.get('user_role') != 'Administrátor' and session.get('user_role') != 'Restaurace':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    res = conn.execute('SELECT id_restaurace FROM restaurace WHERE id_restaurace = ?', (restaurace_id,)).fetchone()
    if res:
        conn.execute('DELETE FROM restaurace WHERE id_restaurace = ?', (restaurace_id,))
        conn.commit()
        flash('Restaurace byla úspěšně smazána!', 'Úspěch')
    else:
        flash('Produkt nebyl nalezen.', 'Chyba')
    conn.close()
    return redirect(url_for('sprava_restauraci'))

@app.route('/prihlaseni', methods=['GET', 'POST'])
def prihlaseni():
    if request.method == 'POST':
        email = request.form['email']
        heslo = request.form['heslo']

        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM uzivatele WHERE email = ? LIMIT 1", (email,)).fetchone()

        if user is None:
            flash('Tento e-mail není registrován.', 'Chyba')
            return render_template('prihlaseni.html', msgs=get_flashed_messages(with_categories=True))

        if not check_password_hash(user[5], heslo):
            flash('Nesprávné heslo.', 'Chyba')
            return render_template('prihlaseni.html', msgs=get_flashed_messages(with_categories=True))

        try:
            session['user_id'] = user[0]
            session['user_role'] = user[6]
            session['user_cele_jmeno'] = user[1] + ' ' + user[2]


            flash('Přihlášení bylo úspěšné!', 'Úspěch')
            conn.close()
            return redirect(url_for('domu'))
        except Exception as e:
            flash(f'Neznámá chyba: {str(e)}', 'Chyba')
            conn.close()
            return render_template('prihlaseni.html', msgs=get_flashed_messages(with_categories=True))

        finally:
            conn.close()

    return render_template('prihlaseni.html', msgs=get_flashed_messages(with_categories=True))

# Nutná oprava - kód z teams
@app.route('/restaurace')
def restaurace2():
    return render_template('restaurace.html', msgs=get_flashed_messages(with_categories=True))    

@app.route('/restaurace/<int:restaurace_id>', methods=['GET'])
def restaurace_nahled(restaurace_id):
    conn = get_db_connection()
    restaurace = conn.execute("SELECT * FROM restaurace",(restaurace_id)).fetchone()
    produkty = conn.execute("SELECT * FROM produkty",(restaurace_id)).fetchall()
    
    return render_template('restaurace_nahled.html', restaurace_promenna=restaurace, produkty_promenna=produkty)

@app.route('/pridat_do_kosiku', methods=['POST'])
def pridat_do_kosiku():
    produkt_id = request.form['produkt_id']
    nazev = request.form['produkt_nazev']
    cena = float(request.form['produkt_cena'])
    restaurace_id = request.form['restaurace_id']
    if 'kosik' not in session:
        session['kosik'] = []
    session['kosik'].append({
        'id': produkt_id,
        'nazev': nazev,
        'cena': cena,
        'restaurace_id': restaurace_id
    })
    session.modified = True
    flash('Produkt přidán do košíku.', 'success')
    return redirect(request.referrer)
@app.route('/odeslat_objednavku', methods=['POST'])
def odeslat_objednavku():
    if 'kosik' not in session or not session['kosik']:
        flash('Košík je prázdný.', 'error')
        return redirect(url_for('restaurant_page'))
    poznamka = request.form.get('poznamka', '')
    kosik = session['kosik']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO objednavky (poznamka, celkova_cena)
        VALUES (?, ?)
    """, (poznamka, sum([p['cena'] for p in kosik])))
    objednavka_id = cursor.lastrowid
    for produkt in kosik:
        cursor.execute("""
            INSERT INTO polozky_objednavky (id_objednavky, id_produktu, cena)
            VALUES (?, ?, ?)
        """, (objednavka_id, produkt['id'], produkt['cena']))
    conn.commit()
    conn.close()
    session.pop('kosik', None)
    flash('Objednávka byla úspěšně odeslána.', 'success')
    return redirect(url_for('restaurant_page'))    


@app.route('/sprava_uzivatelu', methods=['GET', 'POST'])
def sprava_uzivatelu():
    if session.get('user_role') != 'Administrátor':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    search_query = request.form.get('search', '').strip()
    conn = get_db_connection()

    if search_query:
        query = "SELECT * FROM uzivatele WHERE jmeno LIKE ? OR email LIKE ?"
        users = conn.execute(query, (f"%{search_query}%", f"%{search_query}%")).fetchall()
    else:
        users = conn.execute("SELECT * FROM uzivatele").fetchall()

    conn.close()
    return render_template('sprava_uzivatelu.html', uzivatele=users, search_query=search_query, msgs=get_flashed_messages(with_categories=True))

@app.route('/smazat_uzivatele/<int:user_id>', methods=['GET'])
def smazat_uzivatele(user_id):
    if session.get('user_role') != 'Administrátor':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM uzivatele WHERE id_uzivatele = ?", (user_id,)).fetchone()

    if not user:
        flash('Uživatel nenalezen!', 'Chyba')
    else:
        conn.execute("DELETE FROM uzivatele WHERE id_uzivatele = ?", (user_id,))
        conn.commit()
        flash(f'Uživatel {user["jmeno"]} {user["prijmeni"]} byl úspěšně smazán!', 'Úspěch')

    conn.close()
    return redirect('/sprava_uzivatelu')


@app.errorhandler(404)
def nenalezeno(e):
    return render_template('error404.html', msgs=get_flashed_messages(with_categories=True)), 404

if __name__ == '__main__':
    app.run(debug=True)

