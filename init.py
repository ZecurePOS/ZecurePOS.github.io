# -*- coding: utf-8 -*-
from flask import Flask, request
import pymongo
from pymongo import MongoClient
import flask
from flask import session
import re

# GLOBALS
db = None
app = Flask(__name__)

# UTILITY-FUNCTIONS
def readhtml(filename):
    data = open(filename, "r")
    string  = data.read()
    data.close()
    # nur wenn session gesetzt ist ansonsten error
    if (session.get('username')):
        string = re.sub('<span id="username"></span>', '<span id="username">'+session['username']+'</span>', string)
    return string

def connect_to_db():
    global db
    if db is None:
        CONNECTION_STRING = 'mongodb://Nagel:xL8NyJYnnKkuBM4WaVz8NVsGTg@149.172.144.70:27018'
        client            = MongoClient( CONNECTION_STRING )
        db                = client[ 'sse' ]
    return db

def hash_passwd(text):
    result = ""
    for i in range(len(text)):
        char = text[i]
        if (char.isupper()):
            result += chr((ord(char) + 1-65) % 26 + 65)
        else:
            result += chr((ord(char) + 1 - 97) % 26 + 97)
    return result

def format_date(date):
    #date  = re.split(' ', date)
    date  = re.split('-', date)
    year  = date[0]
    month = date[1]
    day   = date[2].split()[0]
    date  = str(day)+'.'+str(month)+'.'+str(year)
    return date

def check_auth():
    # check ob Nutzer angemeldet ist
    if session.get('logged_in') == True:
        return True
    return False

def check_role():
    # check ob Nutzer die richtige Rolle hat
    if session['role'] == 'Student':
        role = 'Student'
    elif session['role'] == 'Professor':
        role = 'Professor'
    elif session['role'] == 'Administrator':
        role = 'Administrator'
    return role

def check_status(user_role):
    # check ob Nutzer angemeldet ist und die richtige Rolle hat. Wenn nicht, sendet den entsprechenden Status-Code zurück
    if check_auth():
        if check_role() == user_role:
            answer = 200
        else:
            answer = flask.make_response(
                '''<h2>Sie sind kein ''' + user_role + '''. <a href="/">hier</a> können Sie sich anmelden.</h2>''', 403)
    else:
        answer = flask.make_response(
            '''<h2>Sie sind nicht angemeldet, melden Sie sich bitte <a href="/">hier</a> an.</h2>''', 401)
    return answer

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RThuifwebghweqijfgoew8tfuw2tr1t27&/)"ß9tg04'

# APP-ROUTING
@app.route("/")
def init():
    return readhtml('login.html')


@app.route("/validate", methods = ['POST'])
# login leitet weiter zu student oder prof
def validate():
    db = connect_to_db()
    if request.method=='POST':
        email   = request.form['email']
        pw      = hash_passwd( request.form['passwd'] )
        col     = db['user']
        find_db = col.find( {'email': email, 'passwd': pw} )
        for user in find_db:
            session['logged_in'] = True
            session['username'] = user['username']
            session['role'] = user['role']
            if(session['role'] == 'Student'):
                return flask.redirect("/student")
            elif(session['role'] == 'Professor'):
                return flask.redirect("/professor")
            elif(session['role'] == 'Administrator'):
                return flask.redirect("/administrator")
    return flask.redirect("/")


@app.route("/student")
def student():
    if check_status('Student') == 200:
        datei = readhtml('student.html')
    else:
        datei = check_status('Student')
    return datei


@app.route("/noteneinsicht")
def noteneinsicht():
    if check_status('Student') == 200:
        datei   = readhtml('student_noteneinsicht.html')
        db      = connect_to_db()
        col     = db['user']
        find_db = col.find( {'username': session['username']} ) #hole unseren eingeloggten user
        user    = find_db[0]
        find_db = db['noten'].find( {'stud_id': user['_id']} ) # nur die noten vom eingeloggten user
        string  = '' #für unsere tabelle die gefüllt wird
        for obj_note in find_db:
            if obj_note is None:
                break
            subject = str(obj_note['subject'])
            grade   = str(obj_note['mark'])
            date    = format_date(str(obj_note['date']))
            string += '<tr><td>' + subject + '</td><td>' + grade + '</td><td>' + date + '</td></tr>'
        datei = re.sub('</tr>', '</tr>' + string, datei) #fülle die tabelle mit inhalt
    else:
        datei = check_status('Student')
    return datei


@app.route("/klausuren")
def klausuren():
    if check_status('Student') == 200:
        checkbox = '<div><label for="scales">angemeldet: </label><input type="checkbox" id="scales" name="scales"></div>'
        db       = connect_to_db()
        usr_col  = db['user']
        user     = usr_col.find({'username' : session['username']})  #hole unseren eingeloggten user
        fak      = user[0]['faculty'] # welche fakultät hat der user
        col      = db['studiengang']
        find_db  = col.find( {'faculty': fak} ) #hole alle fächer von dieser fakulktät
        faecher  = find_db[0]['subjects']
        string   = ''
        for fach in faecher:
           string += '<tr><td>' + str(fach) + '</td><td>' + checkbox + '</td></tr>'
        datei = readhtml('student_klausuren.html')
        datei = re.sub('<span id="student_studiengang"></span>', '<span id="student_studiengang">'+fak+'</span>', datei)
        datei = re.sub('</tr>', '</tr>' + string, datei) #fülle die tabelle mit inhalt
    else:
        datei = check_status('Student')
    return datei


@app.route('/insert_grades', methods = ['POST'])
def insert_grades():
    #db = connect_to_db()
    if request.method=='POST':
        grades = request.form.getlist('grades[]')
        print(grades)
    return flask.redirect("/p_noten")


#@app.route("/save_subects_student", methods = ['POST'])
# login leitet weiter zu student oder prof
#def save_subects_student():
#    db = connect_to_db()
#    if request.method == 'POST':
#        checkboxes = request.form['scales']
#        col        = db['user']
#        print(checkboxes)
#    return flask.redirect("/klausuren")


@app.route("/register", methods = ['POST'])
def register():
    db = connect_to_db()
    if request.method=='POST':
        email         = request.form['email']
        benutzername  = request.form['user']
        pw            = hash_passwd( request.form['passwd'] )
        studiengang   = request.form['actions']
        result = {
            "email"   : email,
            "passwd"  : pw,
            "username": benutzername,
            "role"    : "Student",
            "faculty" : studiengang
        }
        col           = db['user']
        find_email    = col.find( {'email': email} )
        if len(list(find_email)) > 0: # check ob die E-mail-Adresse in der Datenbank bereits existiert
            return flask.make_response('''<h2>Diese E-Mail-Adresse ist bereits registriert, versuchen Sie bitte <a href="/">hier</a> nochmal mit einer anderen E-Mail-Adresse.</h2>''')
        find_username = col.find({'username': benutzername})
        if len(list(find_username)) > 0: # check ob der Benutzername in der Datenbank bereits existiert
            return flask.make_response(
                '''<h2>Dieser Benutzername ist bereits registriert, versuchen Sie bitte <a href="/">hier</a> nochmal mit einem anderen Benutzername.</h2>''')
        else:
            x = col.insert_one(result) # Ansonsten den neuen Nutzer hinzufügen
            return flask.make_response(
                '''<h2>Sie haben sich erfolgreich registriert, melden Sie sich bitte <a href="/">hier</a> an.</h2>''')
    return flask.redirect("/")


@app.route("/professor")
def professor():
    if check_status('Professor') == 200:
        datei = readhtml('professor.html')
    else:
        datei = check_status('Professor')
    return datei


@app.route("/p_noten")
def noten():
    if check_status('Professor') != 200: # if not logged in as professor
        return check_status('Professor')
    datei     = readhtml('professor_noten.html')
    db        = connect_to_db()
    myId      = db['user'].find({'username': session['username']})[0]['_id'] # get prof id
    klausuren = db['klausuren'].find({'prof_id': myId}) # get this prof's subjects
    subjects  = []
    table     = ''
    selected  = ''
    displayed = ''
    if (session.get('subject')): # if subject in the dropdown menu has been selected, only display such subjects 
        selected = str(session['subject'])
        datei = load_dropdown(datei, klausuren, selected)
    else:
        datei = load_dropdown(datei, klausuren)
        return datei
    # get the relevant data
    klausur = db['klausuren'].find({'prof_id': myId, 'subject': selected})[0]
    for reg_student_id in klausur['registered_students']:
        students = db['user'].find({'_id': reg_student_id}) # get the student object
        # this part is super dumb. i cant just 'student = students[0]' cause of some weird error
        student = {} 
        for stud in students:
            if stud is None:
                return datei
            student = stud
        if student == {}:
            return datei
        # not we are save and not causing errors
        noten = db['noten'].find({'stud_id': student['_id'], 'subject': klausur['subject']}) # get the grades
        print("len: ", len(list(noten)))
        if (len(list(noten)) < 1): # if grade not in db, display field to enter grade
            displayed = '<input type="number" step="0.1" id="grades" name="grades[]" min="1" max="5" required>'
        else: # else display the grade itself
            displayed = str(noten[0]['mark'])
            print("displayed: ", displayed)
        table += '<tr><td>' + selected + '</td><td>' + student['username'] + '</td><td>' + displayed + '</td></tr>'
    datei = re.sub('</tr>', '</tr>' + table, datei)
    return datei


def load_dropdown(datei, klausuren, selected = ''):
    subjects = []
    for klausur in klausuren:
        subjects.append(klausur['subject'])
    unique_subjects = set(subjects)
    subject_list = ''
    for unique_subject in unique_subjects:
        if unique_subject == selected:
            subject_list += '<option value="' + unique_subject + '" selected>' + unique_subject + '</option>'
        else:
            subject_list += '<option value="' + unique_subject + '">' + unique_subject + '</option>'
    datei = re.sub('<select id="select" name="faecher" onchange="/reload"></select>', '<select id="select" name="faecher" onchange="/reload">' + subject_list + '</select>', datei)
    return datei


@app.route("/reload", methods = ['POST'])
def reload():
    session['subject'] = request.form['faecher']
    return flask.redirect("/p_noten")


@app.route("/p_klausuren")
def klaus():
    if check_status('Professor') == 200:
        datei   = readhtml('professor_klausuren.html') # Suche nach Id des angemeldeten Prof
        db      = connect_to_db()
        find_db = db['user'].find({'username': session['username']})
        string  = ''
        for obj_user in find_db:
            if obj_user is None:
                break
            myId = obj_user['_id']
        find_klausuren = db['klausuren'].find({'prof_id': myId}) # Suche nach Klausuren, die dem angememldeten Prof zugewiesen sind
        for obj_klausur in find_klausuren:
            if obj_klausur is None:
                break
            subject = obj_klausur['subject']
            date    = format_date(str(obj_klausur['date']))
            string += '<tr><td>' + subject + '</td><td>' + date + '</td></tr>'
        datei = re.sub('</tr>', '</tr>' + string, datei)  # fülle die tabelle mit inhalt
    else:
        datei = check_status('Professor')
    return datei


@app.route("/administrator")
def administrator():
    if check_status('Administrator') == 200:
        datei = readhtml('administrator.html')
    else:
        datei = check_status('Administrator')
    return datei


@app.route("/benutzerverwaltung")
def benutzer():
    if check_status('Administrator') == 200:
        if request.method == 'GET':
            # checkbox = '<select name="actions" id="actions"><option value="" disabled selected hidden>Wählen Sie aus...</option><option value="rolle">Rolle zuweisen</option><option value="passwort">Passwort ersetzen</option><option value="loeschen">Löschen</option></select>'
            datei    = readhtml('administrator_benutzer.html')
            db       = connect_to_db()
            find_db  = db['user'].find() # hole alle Benutzer aus der Datenbank
            string   = ''
            zeile = 0
            for obj_user in find_db:
                if obj_user is None:
                    break
                zeile = zeile + 1
                username = str(obj_user['username'])
                email    = str(obj_user['email'])
                role     = str(obj_user['role'])
                string  += '<tr><td>' + str(zeile) + '</td><td>' + username + '</td><td>' + email + '</td><td>' + role + '</td></tr>'
            datei = re.sub('</tr>', '</tr>' + string, datei)  # fülle die tabelle mit inhalt
    else:
        datei = check_status('Administrator')
    return datei

@app.route("/benutzer_action", methods = ['POST'])
def benutzer_action():
    if request.method == 'POST':
        if request.form['submitButton'] == 'submit':
            db = connect_to_db()
            find_db = db['user'].find()  # hole alle Benutzer aus der Datenbank
            if int(request.form['nummer']) > len(list(find_db)):
                return flask.make_response(
                    '''<h2>Die Zeile existiert nicht, versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>''')
            else:
                request_number = int(request.form['nummer']) - 1
                if request.form['actions'] == 'rolle':
                    find_db = db['user'].find()  # hole alle Benutzer aus der Datenbank
                    if find_db[request_number]['role'] == 'Student':
                        userId = find_db[request_number]['_id']
                        db['user'].update_one({'_id': userId}, {'$set': {'role': 'Professor'}})
                    elif find_db[request_number]['role'] == 'Professor':
                        userId = find_db[request_number]['_id']
                        db['user'].update_one({'_id': userId}, {'$set': {'role': 'Student'}})
                    else:
                        return flask.make_response(
                            '''<h2>Rollenzuweisung ist für für neu registrierte Benutzer (Studenten) möglich, versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>''')
                elif request.form['actions'] == 'passwort':
                    find_db = db['user'].find()  # hole alle Benutzer aus der Datenbank
                    username = find_db[request_number]['username']
                    return flask.make_response(
                        '<form method="POST" action="passwort_ersetzen" name="passwort_ersetzen"><h2>Geben Sie bitte den Benutzername (' + username + ') und das neue Passwort ein:.</h2><input name="user" type="text" size="15" maxlength="20" placeholder="Benutzername" required=true><br><input name="passwd" type="password" size="15" maxlength="20" placeholder="Passwort" required=true><br><button name="submitButton" tpye="submit" id="passwordSubmit">bestätigen</button></form>')

                elif request.form['actions'] == 'loeschen':
                    find_db = db['user'].find()
                    userToDelete = find_db[request_number]
                    db['user'].delete_one(userToDelete)
    return flask.redirect("/benutzerverwaltung")

@app.route("/passwort_ersetzen", methods = ['POST'])
def passwort_ersetzen():
    if request.method == 'POST':
        db = connect_to_db()
        pw = hash_passwd(request.form['passwd'])
        db['user'].update_one({'username': request.form['user']}, {'$set': {'passwd': pw}})
        return flask.make_response(
            '''<h2>Das Passwort wurde erfolgreich aktualisiert. <a href="/benutzerverwaltung">hier</a> finden Sie die Benutzerverwaltung-Seite.</h2>''')
    return flask.make_response(
        '''<h2>Das Passwort konnte nicht aktualisiert werden. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>''')

@app.route("/notenverwaltung")
def notenverwaltung():
    if check_status('Administrator') == 200:
        checkbox = '<select name="actions" id="actions"><option value="" disabled selected hidden>Wählen Sie aus...</option><option>Note löschen</option><option>Note bearbeiten</option></select></select>'
        datei    = readhtml('administrator_noten.html')
        db       = connect_to_db()
        find_db  = db['noten'].find() # hole alle Noten aus der Datenbank
        string   = ''
        for obj_note in find_db:
            if obj_note is None:
                break
            subject = obj_note['subject']
            grade   = str(obj_note['mark'])
            date    = format_date(str(obj_note['date']))
            users   = db['user'].find({'_id': obj_note['stud_id']}) # hole Studentendaten anhand ihrer Id
            for user in users:
                if user is None:
                    break
                username = user['username']
                email    = user['email']
                faculty  = user['faculty']
            profs = db['user'].find({'_id': obj_note['prof_id']}) # hole Professorendaten anhand ihrer Id
            for prof in profs:
                if prof is None:
                    break
                prof_username = prof['username']
            string += '<tr><td>' + username + '</td><td>' + email + '</td><td>' + faculty + '</td><td>' + subject + '</td><td>' + grade + '</td><td>' + prof_username + '</td><td>' + date + '</td><td>' + checkbox + '</td></tr>'
        datei = re.sub('</tr>', '</tr>' + string, datei)  # fülle die tabelle mit inhalt
    else:
        datei = check_status('Administrator')
    return datei


@app.route("/faecherverwaltung")
def faecherverwaltung():
    if check_status('Administrator') == 200:
        datei    = readhtml('administrator_faecher.html')
        # checkbox = '<select name="actions" id="actions"><option value="" disabled selected hidden>Wählen Sie aus...</option><option>Professor zuweisen</option></select>'
        db       = connect_to_db()
        find_db  = db['klausuren'].find() # hole alle Klausuren aus der Datenbank
        string   = ''
        zeile = 0
        for obj_fach in find_db:
            if obj_fach is None:
                break
            zeile = zeile + 1
            subject = obj_fach['subject']
            profs   = db['user'].find({'_id': obj_fach['prof_id']}) # hole Professorendaten anhand ihrer Id
            for obj_user in profs:
                if obj_user is None:
                    break
                prof = obj_user['username']
            string += '<tr><td>' + str(zeile) + '</td><td>' + subject + '</td><td>' + prof + '</td></tr>'
        datei = re.sub('</tr>', '</tr>' + string, datei)  # fülle die tabelle mit inhalt
    else:
        datei = check_status('Administrator')
    return datei

@app.route("/faecher_action", methods = ['POST'])
def faecher_action():
    if request.method == 'POST':
        if request.form['submitButton'] == 'submit':
            db = connect_to_db()
            find_db = db['klausuren'].find()  # hole alle Klausuren aus der Datenbank
            if int(request.form['nummer']) > len(list(find_db)):
                return flask.make_response(
                    '''<h2>Die Zeile existiert nicht, versuchen Sie bitte <a href="/faecherverwaltung">hier</a> noch einmal.</h2>''')
            else:
                request_number = int(request.form['nummer']) - 1
                if request.form['actions'] == 'zuweisen':
                    find_fach = db['klausuren'].find()  # hole alle Klausuren aus der Datenbank
                    fach = find_fach[request_number]['subject']
                    find_db = db['user'].find({'role': 'Professor'})  # hole alle Professoren aus der Datenbank
                    # print(len(list(find_db)))
                    counter = 0
                    profs = []
                    for obj_prof in find_db:
                        if obj_prof is None:
                            break
                        profs.append(obj_prof['username'])
                    str_profs = '<br>'.join(profs)
                    return flask.make_response(
                        '<form method="POST" action="fach_zuweisen" name="passwort_ersetzen">'
                        '<h2>Geben Sie bitte Name vom Fach (' + fach + ') und Name vom Professor, dem Sie das Fach zuweisen möchten, ein:</h2>'
                                                                       '<input name="fach" type="text" size="15" maxlength="20" placeholder="Fach" required=true><br>'
                                                                       '<input name="prof" type="text" size="15" maxlength="40" placeholder="Prof" required=true><br>'
                                                                       '<button name="submitButton" tpye="submit" id="passwordSubmit">bestätigen</button><br>'
                                                                       '<p>hier finden Sie eine Liste von den Professoren, die sich zurzeit im System befinden:</p><br>'
                                                                       + str_profs + '</form>')
    return flask.redirect("/faecherverwaltung")

@app.route("/fach_zuweisen", methods = ['POST'])
def fach_zuweisen():
    if request.method == 'POST':
        if request.form['action'] == 'submit':
            db = connect_to_db()
            fach = request.form['fach']
            prof = request.form['prof']
            find_prof = db['user'].find({'username': prof})
            profId = find_prof[0]['_id']
            db['klausuren'].update_one({'subject': fach}, {'$set': {'prof_id': profId}})
            return flask.make_response(
                '''<h2>Die Aktion wurde erfolgreich ausgeführt. <a href="/faecherverwaltung">hier</a> finden Sie die Benutzerverwaltung-Seite.</h2>''')
        else:
            return flask.make_response(
                '''<h2>w&auml;hlen Sie bitte <a href="/faecherverwaltung">hier</a> die Aktion aus.</h2>''')
    return flask.make_response(
        '''<h2>Die Aktion wurde nicht erfolgreich ausgeführt. Versuchen Sie bitte <a href="/faecherverwaltung">hier</a> noch einmal.</h2>''')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return flask.redirect('/')


# START
if __name__ == '__main__':
    app.run(port=1337, debug=True)
