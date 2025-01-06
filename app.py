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
    session.pop('kosik', None)
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
            return redirect(url_for('sprava_restaurace', restaurace_id=id, produkty_podsekce=''))

    conn.close()
    return redirect(url_for('sprava_restauraci'))

@app.route('/sprava_restaurace/<int:restaurace_id>/', defaults={'info': ''})
@app.route('/sprava_restaurace/<int:restaurace_id>/<string:info>')
def sprava_restaurace(restaurace_id, info):
    if session.get('user_role') not in ['Administrátor', 'Restaurace']:
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    produkty_podsekce = ''
    produkt = None
    if info == 'novy_produkt':
        produkty_podsekce = 'novy'
    if info == 'zpet':
        produkty_podsekce = 'zpet'
    if 'uprava_produkt_' in info:
        idcko = int(info.replace("uprava_produkt_", ""))
        produkt= conn.execute('SELECT p.*, n.castka AS castka FROM produkty p LEFT JOIN nabidka_produktu n ON p.id_produktu = n.id_produktu AND n.platna_do IS NULL WHERE p.id_produktu = ?', (idcko,)).fetchone()
        produkty_podsekce = 'uprava'

    
    restaurace = conn.execute('SELECT * FROM restaurace WHERE id_restaurace = ?', (restaurace_id,)).fetchone()
    produkty = conn.execute('SELECT p.*, n.castka AS castka FROM produkty p LEFT JOIN nabidka_produktu n ON p.id_produktu = n.id_produktu AND n.platna_do IS NULL WHERE p.id_restaurace = ?', (restaurace_id,)).fetchall()
    conn.close()
    return render_template('sprava_restaurace.html', restaurace=restaurace, restaurace_id=restaurace_id, produkty=produkty, produkt=produkt, produkty_podsekce=produkty_podsekce, msgs=get_flashed_messages(with_categories=True))


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
            cursor = conn.execute('INSERT INTO produkty (nazev, popis, id_restaurace, dostupnost, image_url) VALUES (?, ?, ?, ?, ?)',
                         (nazev, popis, restaurace_id, prodej_povolen, url))
            conn.commit()
            id_produktu = cursor.lastrowid
            print(id_produktu)
            print('ID ^')
            flash('Produkt byl úspěšně přidán!', 'Úspěch')
            if prodej_povolen == '1':
                conn.execute('INSERT INTO nabidka_produktu (id_produktu, castka, platna_od) VALUES (?, ?, CURRENT_TIMESTAMP)',(id_produktu, cena))
                conn.commit()
                flash('Nabídka pro produkt byla úspěšně vytvořena s požadovanou cenou! Nyní je v prodeji.', 'Úspěch')
            conn.close()
            return redirect(url_for('sprava_restaurace', restaurace_id=restaurace_id, produkty_podsekce='novy'))

    return render_template('sprava_restaurace.html', pridavani=True, restaurace_id=restaurace_id, produkty_podsekce='', msgs=get_flashed_messages(with_categories=True))


@app.route('/upravit_produkt/<int:produkt_id>', methods=['GET', 'POST'])
def upravit_produkt(produkt_id):
    if session.get('user_role') != 'Administrátor' and session.get('user_role') != 'Restaurace':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    produkt = conn.execute('SELECT p.*, n.castka AS castka FROM produkty p LEFT JOIN nabidka_produktu n ON p.id_produktu = n.id_produktu AND n.platna_do IS NULL WHERE p.id_produktu = ?', (produkt_id,)).fetchone()
    restaurace_id = produkt['id_restaurace']
    if not produkt:
        flash('Produkt nebyl nalezen!', 'Chyba')
        return redirect(url_for('index'))

    if request.method == 'POST':
        nazev = request.form['nazev']
        url = request.form['url']
        prodej_povolen = request.form['prodej_povolen']
        cena = request.form['cena']
        popis = request.form['popis']

        if not nazev or not cena or not url or not prodej_povolen:
            flash('Chybí ti povinné údaje!', 'Chyba')
        else:
            conn.execute(
                'UPDATE produkty SET nazev = ?, popis = ?, dostupnost = ?, image_url = ? WHERE id_produktu = ?',
                (nazev, popis, prodej_povolen, url, produkt_id)
            )
            conn.commit()

            if prodej_povolen == '1':
                nabidka = conn.execute(
                    'SELECT * FROM nabidka_produktu WHERE id_produktu = ? AND platna_do IS NULL',
                    (produkt_id,)
                ).fetchone()

                if nabidka:
                    if float(nabidka['castka']) != float(cena):
                        conn.execute(
                            'UPDATE nabidka_produktu SET platna_do = CURRENT_TIMESTAMP WHERE id_produktu = ? AND platna_do IS NULL',
                            (produkt_id,)
                        )
                        conn.execute(
                            'INSERT INTO nabidka_produktu (id_produktu, castka, platna_od) VALUES (?, ?, CURRENT_TIMESTAMP)',
                            (produkt_id, cena)
                        )
                        conn.commit()
                        flash('Cena byla aktualizována.', 'Úspěch')
                else:
                    conn.execute(
                        'INSERT INTO nabidka_produktu (id_produktu, castka, platna_od) VALUES (?, ?, CURRENT_TIMESTAMP)',
                        (produkt_id, cena)
                    )
                    conn.commit()
                    flash('Produkt byl přidán do nabídky.', 'Úspěch')
            else:
                conn.execute(
                    'UPDATE nabidka_produktu SET platna_do = CURRENT_TIMESTAMP WHERE id_produktu = ? AND platna_do IS NULL',
                    (produkt_id,)
                )
                conn.commit()
                flash('Produkt byl odebrán z nabídky.', 'Úspěch')

            flash('Produkt byl úspěšně upraven!', 'Úspěch')
            conn.close()
            return redirect(url_for('sprava_restaurace', restaurace_id=restaurace_id, produkty_podsekce='zpet'))

    return render_template('sprava_restaurace.html', pridavani=True, restaurace_id=restaurace_id, produkty_podsekce='zpet', msgs=get_flashed_messages(with_categories=True))



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
        conn.execute('DELETE FROM nabidka_produktu WHERE id_produktu = ?', (produkt_id,))
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
        produkty = conn.execute('SELECT id_produktu FROM produkty WHERE id_restaurace = ?', (restaurace_id,)).fetchall()
        for produkt in produkty:
            produkt_id = produkt['id_produktu']
            conn.execute('DELETE FROM nabidka_produktu WHERE id_produktu = ?', (produkt_id,))
        conn.commit()
        flash('Nabídka byla úspěšně smazána!', 'Úspěch')
        conn.execute('DELETE FROM produkty WHERE id_restaurace = ?', (restaurace_id,))
        flash('Produkty byly úspěšně smazány!', 'Úspěch')
        conn.commit()
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

@app.route('/nastaveni/', defaults={'info': ''})
@app.route('/nastaveni/<string:info>')
def nastaveni(info):
    conn = get_db_connection()
    adresy = conn.execute("SELECT * FROM adresy_uzivatele WHERE id_uzivatele = ?", (session.get('user_id'),)).fetchall()
    objednavky = conn.execute("SELECT * FROM objednavky WHERE id_uzivatele = ?", (session.get('user_id'),)).fetchall()
    return render_template('nastaveni.html', msgs=get_flashed_messages(with_categories=True), get_user_by_id=get_user_by_id, adresy=adresy, objednavky=objednavky, info=info)   

@app.route('/zmena_hesla', methods=['POST'])
def zmena_hesla():
    if 'user_id' not in session:
        flash('Musíte být přihlášeni, abyste mohli změnit heslo.', 'Chyba')
        return redirect(url_for('prihlaseni'))

    stare_heslo = request.form['heslo']
    nove_heslo = request.form['heslo_nove']

    if not stare_heslo or not nove_heslo:
        flash('Všechna pole jsou povinná.', 'Chyba')
        return redirect(url_for('nastaveni'))

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM uzivatele WHERE id_uzivatele = ?', (session['user_id'],)).fetchone()

    if not user:
        conn.close()
        flash('Uživatel nebyl nalezen.', 'Chyba')
        return redirect(url_for('prihlaseni'))

    if not check_password_hash(user['heslo'], stare_heslo):
        conn.close()
        flash('Staré heslo není správné.', 'Chyba')
        return redirect(url_for('nastaveni'))

    nove_heslo_hash = generate_password_hash(nove_heslo)
    conn.execute('UPDATE uzivatele SET heslo = ? WHERE id_uzivatele = ?', (nove_heslo_hash, session['user_id']))
    conn.commit()
    conn.close()

    flash('Heslo bylo úspěšně změněno.', 'Úspěch')
    return redirect(url_for('nastaveni'))

@app.route('/pridat_adresu', methods=['GET', 'POST'])
def pridat_adresu():
    if 'user_id' not in session:
        flash('Musíte být přihlášeni, abyste mohli přidat adresu.', 'Chyba')
        return redirect(url_for('prihlaseni'))

    if request.method == 'POST':
        nazev = request.form['nazev']
        ulice = request.form['ulice']
        cp = request.form['cp']
        psc = request.form['psc']
        mesto = request.form['mesto']

        if not ulice or not cp or not psc or not mesto:
            flash('Všechna pole jsou povinná.', 'Chyba')
        else:
            conn = get_db_connection()
            existujici_adresy = conn.execute(
                'SELECT COUNT(*) FROM adresy_uzivatele WHERE id_uzivatele = ?',
                (session['user_id'],)
            ).fetchone()[0]

            hlavni_adresa = 1 if existujici_adresy == 0 else 0

            conn.execute('''
                INSERT INTO adresy_uzivatele (id_uzivatele, nazev_adresy, adresa_ulice, adresa_cislo_domu, adresa_psc, adresa_mesto, hlavni_adresa)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], nazev, ulice, cp, psc, mesto, hlavni_adresa))
            conn.commit()
            conn.close()

            flash('Adresa byla úspěšně přidána.', 'Úspěch')
            return redirect(url_for('nastaveni'))

    return render_template('nastaveni.html', user=user, msgs=get_flashed_messages(with_categories=True), get_user_by_id=get_user_by_id)

@app.route('/nastavit_hlavni/<int:id_adresy>', methods=['GET'])
def nastavit_hlavni_adresu(id_adresy):
    if 'user_id' not in session:
        flash('Musíte být přihlášeni, abyste mohli nastavit hlavní adresu.', 'Chyba')
        return redirect(url_for('prihlaseni'))

    conn = get_db_connection()
    adresa = conn.execute(
        'SELECT * FROM adresy_uzivatele WHERE id_adresy = ? AND id_uzivatele = ?',
        (id_adresy, session['user_id'])
    ).fetchone()

    if not adresa:
        conn.close()
        flash('Adresa nebyla nalezena nebo nepatří tomuto uživateli.', 'Chyba')
        return redirect(url_for('nastaveni'))

    conn.execute(
        'UPDATE adresy_uzivatele SET hlavni_adresa = 0 WHERE id_uzivatele = ?',
        (session['user_id'],)
    )
    conn.execute(
        'UPDATE adresy_uzivatele SET hlavni_adresa = 1 WHERE id_adresy = ?',
        (id_adresy,)
    )
    conn.commit()
    conn.close()

    flash('Hlavní adresa byla úspěšně nastavena.', 'Úspěch')
    return redirect(url_for('nastaveni'))



@app.route('/smazat_adresu/<int:id_adresy>', methods=['GET'])
def smazat_adresu(id_adresy):
    if 'user_id' not in session:
        flash('Musíte být přihlášeni, abyste mohli mazat adresy.', 'Chyba')
        return redirect(url_for('prihlaseni'))

    conn = get_db_connection()
    adresa = conn.execute('SELECT * FROM adresy_uzivatele WHERE id_adresy = ? AND id_uzivatele = ?', 
                          (id_adresy, session['user_id'])).fetchone()

    if not adresa:
        conn.close()
        flash('Adresa nebyla nalezena nebo nepatří tomuto uživateli.', 'Chyba')
        return redirect(url_for('nastaveni'))

    conn.execute('DELETE FROM adresy_uzivatele WHERE id_adresy = ?', (id_adresy,))
    conn.commit()
    conn.close()

    flash('Adresa byla úspěšně smazána.', 'Úspěch')
    return redirect(url_for('nastaveni'))


@app.route('/zmena_udaju', methods=['GET', 'POST'])
def zmena_udaju():
    if 'user_id' not in session:
        flash('Musíte být přihlášeni, abyste mohli změnit své údaje.', 'Chyba')
        return redirect(url_for('prihlaseni'))

    user_id = session['user_id']
    user = get_user_by_id(user_id)

    if not user:
        flash('Uživatel nenalezen!', 'Chyba')
        return redirect(url_for('prihlaseni'))

    if request.method == 'POST':
        jmeno = request.form['jmeno']
        prijmeni = request.form['prijmeni']
        email = request.form['email']
        telefon = request.form['telefon']

        if not jmeno or not prijmeni or not email or not telefon:
            flash('Všechna pole jsou povinná.', 'Chyba')
        else:
            conn = get_db_connection()
            conn.execute('''
                UPDATE uzivatele
                SET jmeno = ?, prijmeni = ?, email = ?, telefon = ?
                WHERE id_uzivatele = ?
            ''', (jmeno, prijmeni, email, telefon, user_id))
            conn.commit()
            conn.close()

            flash('Údaje byly úspěšně změněny.', 'Úspěch')
            return redirect(url_for('nastaveni'))

    return render_template('nastaveni.html', user=user, msgs=get_flashed_messages(with_categories=True), get_user_by_id=get_user_by_id)


# Nutná oprava - kód z teams
@app.route('/restaurace')
def restaurace2():
    conn = get_db_connection()
    restaurace = conn.execute("SELECT * FROM restaurace").fetchall()
    return render_template('restaurace.html', restaurace=restaurace, msgs=get_flashed_messages(with_categories=True))    

@app.route('/restaurace/<int:restaurace_id>', methods=['GET'])
def restaurace_nahled(restaurace_id):
    conn = get_db_connection()
    restaurace = conn.execute("SELECT * FROM restaurace WHERE id_restaurace = ?", (restaurace_id,)).fetchone()
    produkty = conn.execute("SELECT p.*, n.castka AS castka FROM produkty p LEFT JOIN nabidka_produktu n ON p.id_produktu = n.id_produktu AND n.platna_do IS NULL WHERE p.id_restaurace = ? AND p.dostupnost = '1'", (restaurace_id,)).fetchall()
    conn.close()

    kosik = session.get('kosik', [])
    if not isinstance(kosik, list):
        kosik = []

    total = sum(produkt.get('castka', 0) for produkt in kosik if isinstance(produkt, dict) and 'castka' in produkt)

    return render_template(
        'restaurace_nahled.html',
        restaurace_promenna=restaurace,
        produkty_promenna=produkty,
        kosik=kosik,
        total=total, msgs=get_flashed_messages(with_categories=True)
    )

@app.route('/pridat_do_kosiku/<int:produkt_id>', methods=['GET'])
def pridat_do_kosiku(produkt_id):
    if not produkt_id:
        flash('Nebyl zadán žádný produkt k přidání.', 'Chyba')
        return redirect(request.referrer or url_for('home'))
    
    conn = get_db_connection()
    nas_produkt = conn.execute('''
        SELECT p.*, n.castka AS castka
        FROM produkty p
        LEFT JOIN nabidka_produktu n ON p.id_produktu = n.id_produktu AND n.platna_do IS NULL
        WHERE p.id_produktu = ? AND p.dostupnost = '1'
        LIMIT 1
    ''', (produkt_id,)).fetchone()
    conn.close()

    if nas_produkt is None:
        flash('Produkt neexistuje nebo není dostupný.', 'Chyba')
        return redirect(request.referrer or url_for('home'))

    kosik = session.get('kosik', [])
    if not isinstance(kosik, list):
        kosik = []

    kosik.append(dict(nas_produkt))
    session['kosik'] = kosik
    session.modified = True

    flash('Produkt přidán do košíku.', 'Úspěch')
    return redirect(request.referrer or url_for('restaurace'))


@app.route('/odebrat_z_kosiku/<int:index>', methods=['GET'])
def odebrat_z_kosiku(index):
    kosik = session.get('kosik', [])
    if not isinstance(kosik, list):
        kosik = []

    if 0 <= index < len(kosik):
        del kosik[index]
        session['kosik'] = kosik
        session.modified = True
        flash('Produkt byl odebrán z košíku.', 'Úspěch')
    else:
        flash('Neplatný index produktu.', 'Chyba')

    return redirect(request.referrer or url_for('restaurace'))

 
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
            INSERT INTO objednavky_produkty (id_objednavky, id_produktu, cena)
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

@app.route('/nastavit_roli/<int:user_id>/<string:role>', methods=['GET'])
def nastavit_roli(user_id, role):
    if session.get('user_role') != 'Administrátor':
        flash('Přístup zamítnut!', 'Chyba')
        return render_template('index.html', msgs=get_flashed_messages(with_categories=True))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM uzivatele WHERE id_uzivatele = ?", (user_id,)).fetchone()

    if not user:
        flash('Uživatel nenalezen!', 'Chyba')
    else:
        conn.execute("UPDATE uzivatele SET role = ? WHERE id_uzivatele = ?", (role, user_id))
        conn.commit()
        flash(f'Role uživatele {user["jmeno"]} {user["prijmeni"]} byla úspěšně změněna na "{role}"!', 'Úspěch')

    conn.close()
    return redirect('/sprava_uzivatelu')


@app.errorhandler(404)
def nenalezeno(e):
    return render_template('error404.html', msgs=get_flashed_messages(with_categories=True)), 404

if __name__ == '__main__':
    app.run(debug=True)

