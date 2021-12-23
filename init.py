# -*- coding: utf-8 -*-
from flask import Flask, request
import pymongo
from pymongo import MongoClient
import flask
from flask import session
import re
import os
from flask import send_file

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
    db = connect_to_db()
    find_user = db['user'].find({'username': session['username']})
    session['role'] = find_user[0]['role']
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


# erstellt eine checkbox für ein fach (um sich als student für das fach anzumelden)
# wird nur von "klausuren" benötigt, ist aber dennoch eine utility function
def make_checkbox(fach):
    return '<div><label for="scales">angemeldet: </label><input type="checkbox" id="scales[]" name="scales[]" value="' + str(fach) + '"></div>'


# lädt das dropdown menu auf der seite "p_noten"
# still a utility function
def load_dropdown(datei, klausuren, selected = ''):
    subjects = []
    for klausur in klausuren:
        subjects.append(klausur['subject'])
    unique_subjects = set(subjects)
    subject_list    = ''
    for unique_subject in unique_subjects:
        if unique_subject == selected:
            subject_list += '<option value="' + unique_subject + '" selected>' + unique_subject + '</option>'
        else:
            subject_list += '<option value="' + unique_subject + '">' + unique_subject + '</option>'
    datei = re.sub('<select id="select" name="faecher" onchange="/reload"></select>', '<select id="select" name="faecher" onchange="/reload">' + subject_list + '</select>', datei)
    return datei


# lädt das dropdown menu und damit alle fächer neu
# wird nur auf "p_noten" benötigt, deswegen utility
@app.route("/reload", methods = ['POST'])
def reload():
    session['subject'] = request.form['faecher']
    return flask.redirect("/p_noten")

# etwas im code versteckt, damit es nicht gleich gefunden wird ;)
# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RThuifwebghweqijfgoew8tfuw2tr1t27&/)"ß9tg04'


# APP-ROUTING


@app.route("/")
def init():
    return readhtml('login.html')


# login
# leitet weiter zu student oder prof
@app.route("/validate", methods = ['POST'])
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


# neuen account registrieren
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
            return flask.make_response('<h2>Diese E-Mail-Adresse ist bereits registriert, versuchen Sie bitte <a href="/">hier</a> nochmal mit einer anderen E-Mail-Adresse.</h2>', 409)
        find_username = col.find({'username': benutzername})
        if len(list(find_username)) > 0: # check ob der Benutzername in der Datenbank bereits existiert
            return flask.make_response(
                '<h2>Dieser Benutzername ist bereits registriert, versuchen Sie bitte <a href="/">hier</a> nochmal mit einem anderen Benutzername.</h2>', 409)
        else:
            x = col.insert_one(result) # Ansonsten den neuen Nutzer hinzufügen
            return flask.make_response(
                '<h2>Sie haben sich erfolgreich registriert, melden Sie sich bitte <a href="/">hier</a> an.</h2>', 201)
    return flask.redirect("/")




# STUDENT

@app.route("/student")
def student():
    if check_status('Student') == 200:
        datei = readhtml('student.html')
    else:
        datei = check_status('Student')
    return datei


# student kann seine eigenen noten einsehen
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


# student kann seine noten herunterladen (lädt noten aller studenten herunter)
@app.route('/download_pdf', methods = ['POST'])
def download_pdf():
    db = connect_to_db()
    # generate preamble
    preamble = r'''
        \documentclass[a4paper,12pt]{article}
        \begin{document}
        \begin{table}[h!]
        \begin{tabular}{c c c}
    '''
    # generate end of file
    ending = r'''
        \end{tabular}
        \end{table}
        \end{document}
    '''
    table  = r'''''' # raw multiline string
    studis = db['user'].find({'role': 'Student'})
    # for each studi get username and grade
    # this is not nice code but it is necessary because our db model sucks
    for studi in studis:
        for subj in db['klausuren'].find():
            for reg_student in subj['registered_students']:
                #if reg_student == studi['_id']:
                    grades = db['noten'].find({'stud_id' : studi['_id'], 'subject' : subj['subject'], "mark": {"$exists": True}})
                    for grade in grades:
                        #print(grade)
                        # generate latex-table from matrikelnr (which is username), subject and grade
                        table += studi['username'] + r''' & ''' + subj['subject'] + r''' & ''' + str(grade['mark']) + r'''\\ '''
    # bake tex file
    tex_file = preamble + table + ending
    # write out
    file = open('latex/'+session['username']+'_noten.tex', 'w')
    file.write(tex_file)
    file.close()
    # compile to pdf
    os.system('pdflatex -output-directory latex/ latex/'+session['username']+'_noten.tex')
    # download the pdf
    path = 'latex/'+session['username']+'_noten.pdf'
    return send_file(path,as_attachment=True)


# student kann sich hier für klausur einschreiben
@app.route("/klausuren")
def klausuren():
    if check_status('Student') == 200:
        db       = connect_to_db()
        usr_col  = db['user']
        user     = usr_col.find({'username' : session['username']})  #hole unseren eingeloggten user
        fak      = user[0]['faculty'] # welche fakultät hat der user
        col      = db['studiengang']
        find_db  = col.find( {'faculty': fak} ) #hole alle fächer von dieser fakulktät
        faecher  = find_db[0]['subjects']
        string   = ''
        for fach in faecher:
           string += '<tr><td>' + str(fach) + '</td><td>' + make_checkbox(fach) + '</td></tr>'
        datei = readhtml('student_klausuren.html')
        datei = re.sub('<span id="student_studiengang"></span>', '<span id="student_studiengang">'+fak+'</span>', datei)
        datei = re.sub('</tr>', '</tr>' + string, datei) #fülle die tabelle mit inhalt
    else:
        datei = check_status('Student')
    return datei


# zu klausur anmelden
# übermittelt die daten von backend in die db
@app.route('/anmelden', methods = ['POST'])
def anmelden():
    checkboxes = request.form.getlist('scales[]')
    #print(checkboxes)
    # insert checked subjects into db
    db   = connect_to_db()
    user = db['user'].find({'username': session['username']})[0]
    #print(user)
    # for each subject in checkboxes do
    for subject in checkboxes:
        db_subject = db['klausuren'].find({'subject': subject})
        db.klausuren.update({'subject': subject}, {'$push': {'registered_students': user['_id']} })
    return flask.redirect("/klausuren")



# PROFESSOR


@app.route("/professor")
def professor():
    if check_status('Professor') == 200:
        datei = readhtml('professor.html')
    else:
        datei = check_status('Professor')
    return datei


# als prof noten der studis eintragen
# FIXED
@app.route('/insert_grades', methods = ['POST'])
def insert_grades():
    #db = connect_to_db()
    if request.method=='POST':
        grades = request.form.getlist('grades[]')
        print("grades: ", grades)
    return flask.redirect("/p_noten")


# lädt alle noten der studis, die für das mit dem dropdown menu ausgewählte fach angemeldet sind, so dass der professor dort die noten eintragen kann
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
        datei    = load_dropdown(datei, klausuren, selected)
    else:
        datei = load_dropdown(datei, klausuren)
        return datei
    # get the relevant data
    klausur = db['klausuren'].find({'prof_id': myId, 'subject': selected})[0]
    for reg_student_id in klausur['registered_students']:
        students = db['user'].find({'_id': reg_student_id}) # get the student object
        # this part is super dumb. i cant just 'student = students[0]' cause students might not exist
        # however students is not even None, i simply cant check if it is there
        student = {}
        try:
            student = students[0]
        except:
            print("whoopsies")
            continue
        # now we are save and not causing errors
        noten = db['noten'].find({'stud_id': student['_id'], 'subject': klausur['subject']}) # get the grades
        if (len(list(noten)) < 1): # if grade not in db, display field to enter grade
            displayed = '<input type="number" step="0.1" id="grades" name="grades[]" min="1" max="5" required>'
        else: # else display the grade itself (THIS DOES NOT WORK YET AND IT NEEDS TO BE FIXED)
            displayed = str(noten[0]['mark'])
            print("displayed: ", displayed)
        table += '<tr><td>' + selected + '</td><td>' + student['username'] + '</td><td>' + displayed + '</td></tr>'
    datei = re.sub('</tr>', '</tr>' + table, datei)
    return datei




# prof kann sehen, welche klausuren er anbietet
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



# ADMINISTRATOR


# administrator-Sitemap
@app.route("/administrator")
def administrator():
    # user can only open the administrator-sitemap if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        file = readhtml('administrator.html')
    else:
        file = check_status('Administrator')
    return file


# user management
@app.route("/benutzerverwaltung")
def benutzer():
    # user can only open the user management page if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'GET':
            file = readhtml('administrator_benutzer.html')
            db = connect_to_db()
            find_db  = db['user'].find() # get all users from ,,user"
            string   = ''
            line = 0 # count number of lines
            for obj_user in find_db:
                if obj_user is None:
                    break
                line = line + 1
                username = str(obj_user['username'])
                email    = str(obj_user['email'])
                role     = str(obj_user['role'])
                string  += '<tr><td>' + str(line) + '</td><td>' + username + '</td><td>' + email + '</td><td>' + role + '</td></tr>'
            file = re.sub('</tr>', '</tr>' + string, file)  # fill the table with content
    else:
        file = check_status('Administrator')
    return file


# user management actions
@app.route("/benutzer_action", methods = ['POST'])
def benutzer_action():
    # user can only do changes in user management if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            if request.form['submitButton'] == 'submit':
                db = connect_to_db()
                find_db = db['user'].find()  # get all users from ,,user"
                if request.form['nummer'] == '':
                    return flask.make_response(
                        '<h2>Sie müssen eine Zeile eingeben, versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        400)
                keys1 = request.form.keys()
                if len(list(keys1)) < 3:
                    return flask.make_response(
                        '<h2>Sie müssen eine Aktion auswählen, versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        400)
                if int(request.form['nummer']) > len(list(find_db)): # if the entered line does not exist..
                    return flask.make_response(
                        '<h2>Die Zeile existiert nicht, versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                        404)
                else:
                    request_number = int(request.form['nummer']) - 1
                    if request.form['actions'] == 'rolle': # if administrator want to edit a role of a user
                        find_db = db['user'].find()  # get all users from ,,user"
                        username = find_db[request_number]['username']
                        role = find_db[request_number]['role']
                        # return response for more information and to verify the administrator's identity
                        return flask.make_response(
                            '<form method="POST" action="rolle_zuweisen" name="rolle_zuweisen" name="' + username + '"><h2>Geben Sie bitte den Benutzername (' + username + ') und die neue gewünschte Rolle ein:</h2>'
                            '<input name="' + username + '" type="text" size="15" maxlength="40" placeholder="Benutzername" required=true><br>'
                            '<input name="' + role + '" type="text" size="15" maxlength="20" placeholder="neue Rolle" required=true><br>'
                            '<p>Bestätigen bitte Sie auch, dass Sie ' + session['username'] + ' sind:</p>'
                            '<input name="my_user" type="text" size="15" maxlength="20" placeholder="Ihr Benutzername" required=true><br>'
                             '<input name="my_passwd" type="password" size="15" maxlength="20" placeholder="Ihr Passwort" required=true><br>'
                             '<br><button name="submitButton" type="submit" id="roleSubmit">bestätigen</button></form>',
                            302)
                    elif request.form['actions'] == 'passwort': # if administrator want to change a user's password...
                        find_db  = db['user'].find()  # get all users from ,,user"
                        username = find_db[request_number]['username']
                        # return response for more information and to verify the administrator's identity
                        return flask.make_response(
                            '<form method="POST" action="passwort_ersetzen" name="passwort_ersetzen" name="' + username + '"><h2>Geben Sie bitte den Benutzername (' + username + ') und das neue Passwort ein:</h2>'
                            '<input name="' + username + '" type="text" size="15" maxlength="20" placeholder="Benutzername" required=true><br>'
                            '<input name="passwd" type="password" size="15" maxlength="20" placeholder="Passwort" required=true>'
                            '<p>Bestätigen bitte Sie auch, dass Sie ' + session['username'] + ' sind:</p>'
                            '<input name="my_user" type="text" size="15" maxlength="20" placeholder="Ihr Benutzername" required=true><br>'
                            '<input name="my_passwd" type="password" size="15" maxlength="20" placeholder="Ihr Passwort" required=true><br>'
                            '<br><button name="submitButton" type="submit" id="passwordSubmit">bestätigen</button></form>',
                            302)

                    elif request.form['actions'] == 'loeschen': # if administrator want to delete a user...
                        find_db  = db['user'].find()  # get all users from ,,user"
                        username = find_db[request_number]['username']
                        # return response for more information and to verify the administrator's identity
                        return flask.make_response(
                            '<form method="POST" action="benutzer_loeschen" name="benutzer_loeschen" name="' + username + '"><h2>Geben Sie bitte den Benutzername (' + username + ') ein:</h2>'
                            '<input name="' + username + '" type="text" size="15" maxlength="20" placeholder="Benutzername" required=true><br>'
                            '<p>Bestätigen bitte Sie auch, dass Sie ' + session['username'] + ' sind:</p>'
                             '<input name="my_user" type="text" size="15" maxlength="20" placeholder="Ihr Benutzername" required=true><br>'
                             '<input name="my_passwd" type="password" size="15" maxlength="20" placeholder="Ihr Passwort" required=true><br>'
                             '<br><button name="submitButton" type="submit" id="deleteSubmit">bestätigen</button></form>',
                            302)
            elif request.form['submitButton'] == 'cancel':
                return flask.redirect("/administrator")
        return flask.redirect("/benutzerverwaltung")
    else:
        file = check_status('Administrator')
    return file


# user management action: edit a role of a user
@app.route("/rolle_zuweisen", methods = ['POST'])
def rolle_zuweisen():
    # user can only edit a role of a user if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            my_passwd = hash_passwd(request.form['my_passwd'])
            db = connect_to_db()
            keys1 = request.form.keys()
            keys2 = []
            for key in keys1:
                keys2.append(key)
            find_admin = db['user'].find({'username': session['username']} and {'role': 'Administrator'}) # get administrator's data from ,,user"
            if find_admin[0]['username'] == request.form['my_user'] and find_admin[0]['passwd'] == my_passwd: # check that the adminstrator has correctly verified the identity
                if str(keys2[0]) == request.form[keys2[0]]:
                    find_user = db['user'].find({'username': request.form[keys2[0]]})
                    if len(list(find_user)) > 0: # Check if the user already exists in the database
                        if request.form[keys2[1]] != 'Student' and request.form[keys2[1]] != 'Professor' and request.form[keys2[1]] != 'Administrator': # Check that the role was entered correctly
                            return flask.make_response(
                                '<h2>die eingegebene Rolle kann im System nicht gefunden werden. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                                404)
                        db['user'].update_one({'username': request.form[keys2[0]]}, {'$set': {'role': request.form[keys2[1]]}})
                        return flask.make_response(
                            '<h2>Die Rolle wurde erfolgreich aktualisiert. <a href="/benutzerverwaltung">hier</a> finden Sie die Benutzerverwaltung-Seite.</h2>',
                            200)
                    else:
                        return flask.make_response(
                            '<h2>Benutzer kann nicht gefunden werden. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                            400)
                else:
                    return flask.make_response(
                        '<h2>Der eingegebene Benutzername stimmt mit dem Buntzer, für den Sie das Konto löschen möchten, nicht überein. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                        400)
            else:
                return flask.make_response(
                    '<h2>Ihr Benutzername oder Password haben Sie nicht richtig eingegeben. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                    403)
        return flask.make_response(
            '<h2>Die Rolle konnte nicht aktualisiert werden. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
            400)
    else:
        file = check_status('Administrator')
    return file


# user management action: change user's password
@app.route("/passwort_ersetzen", methods = ['POST'])
def passwort_ersetzen():
    # user can only change user's password if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            my_passwd = hash_passwd(request.form['my_passwd'])
            db = connect_to_db()
            keys1 = request.form.keys()
            keys2 = []
            for key in keys1:
                keys2.append(key)
            find_admin = db['user'].find({'username': session['username']} and {'role': 'Administrator'}) # get administrator's data from ,,user"
            if find_admin[0]['username'] == request.form['my_user'] and find_admin[0]['passwd'] == my_passwd: # check that the adminstrator has correctly verified the identity
                if str(keys2[0]) == request.form[keys2[0]]:
                    find_user = db['user'].find({'username': request.form[keys2[0]]})
                    if len(list(find_user)) > 0: # Check if the user already exists in the database
                        pw = hash_passwd(request.form['passwd'])
                        db['user'].update_one({'username': request.form[keys2[0]]}, {'$set': {'passwd': pw}}) # change user's password
                        return flask.make_response(
                            '<h2>Das Passwort wurde erfolgreich aktualisiert. <a href="/benutzerverwaltung">hier</a> finden Sie die Benutzerverwaltung-Seite.</h2>',
                            200)
                    else:
                        return flask.make_response(
                            '<h2>Benutzer kann nicht gefunden werden. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                            400)
                else:
                    return flask.make_response(
                        '<h2>Der eingegebene Benutzername stimmt mit dem Buntzer, für den Sie das Passwort ändern möchten, nicht überein. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                        400)
            else:
                return flask.make_response(
                    '<h2>Ihr Benutzername oder Password haben Sie nicht richtig eingegeben. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                    403)
        return flask.make_response(
            '<h2>Das Passwort konnte nicht aktualisiert werden. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
            400)
    else:
        file = check_status('Administrator')
    return file


# user management action: delete a user
@app.route("/benutzer_loeschen", methods = ['POST'])
def benutzer_loeschen():
    # user can only delete a user if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            my_passwd = hash_passwd(request.form['my_passwd'])
            db        = connect_to_db()
            keys1     = request.form.keys()
            keys2     = []
            for key in keys1:
                keys2.append(key)
            find_admin = db['user'].find({'username': session['username']} and {'role': 'Administrator'}) # get administrator's data from ,,user"
            if find_admin[0]['username'] == request.form['my_user'] and find_admin[0]['passwd'] == my_passwd: # check that the adminstrator has correctly verified the identity
                if str(keys2[0]) == request.form[keys2[0]]:
                    find_user = db['user'].find({'username': request.form[keys2[0]]})
                    if len(list(find_user)) > 0: # Check if the user already exists in the database
                        find_user    = db['user'].find({'username': request.form[keys2[0]]})
                        userToDelete = find_user[0]
                        db['user'].delete_one(userToDelete) # delete the user
                        return flask.make_response(
                            '<h2>Das Konto wurde erfolgreich gelöscht. <a href="/benutzerverwaltung">hier</a> finden Sie die Benutzerverwaltung-Seite.</h2>',
                            200)
                    else:
                        return flask.make_response(
                            '<h2>Benutzer kann nicht gefunden werden. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                            400)
                else:
                    return flask.make_response(
                        '<h2>Der eingegebene Benutzername stimmt mit dem Buntzer, für den Sie das Konto löschen möchten, nicht überein. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                        400)
            else:
                return flask.make_response(
                    '<h2>Ihr Benutzername oder Password haben Sie nicht richtig eingegeben. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
                    403)
        return flask.make_response(
            '<h2>Das Konto konnte nicht gelöscht werden. Versuchen Sie bitte <a href="/benutzerverwaltung">hier</a> noch einmal.</h2>',
            400)
    else:
        file = check_status('Administrator')
    return file


# grades management
@app.route("/notenverwaltung")
def notenverwaltung():
    # user can only open the grades management page if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        file    = readhtml('administrator_noten.html')
        db       = connect_to_db()
        find_db  = db['noten'].find() # get all grades from ,,noten"
        string   = ''
        zeile = 0
        for obj_note in find_db:
            if obj_note is None:
                break
            subject = obj_note['subject']
            grade = str(obj_note['mark'])
            date = format_date(str(obj_note['date']))
            zeile = zeile + 1
            users   = db['user'].find({'_id': obj_note['stud_id']}) # get student from ,,user"
            for user in users:
                if user is None:
                    break
                username = user['username']
                email    = user['email']
                faculty  = user['faculty']
            profs = db['user'].find({'_id': obj_note['prof_id']}) # get prof from ,,user"
            for prof in profs:
                if prof is None:
                    break
                prof_username = prof['username']
            string += '<tr><td>' + str(zeile) + '</td><td>' + username + '</td><td>' + email + '</td><td>' + faculty + '</td><td>' + subject + '</td><td>' + grade + '</td><td>' + prof_username + '</td><td>' + date + '</td></tr>'
        file = re.sub('</tr>', '</tr>' + string, file)  # fill the table with content
    else:
        file = check_status('Administrator')
    return file


# grades management actions
@app.route("/noten_action", methods = ['POST'])
def noten_action():
    # user can only do changes in grades management if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            if request.form['submitButton'] == 'submit':
                db = connect_to_db()
                find_db = db['noten'].find()  # get all exams from ,,klausuren"
                if request.form['nummer'] == '':
                    return flask.make_response(
                        '<h2>Sie müssen eine Zeile eingeben, versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        400)
                keys1 = request.form.keys()
                if len(list(keys1)) < 3:
                    return flask.make_response(
                        '<h2>Sie müssen eine Aktion auswählen, versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        400)
                if int(request.form['nummer']) > len(list(find_db)):
                    return flask.make_response(
                        '<h2>Die Zeile existiert nicht, versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        404)
                else:
                    request_number = int(request.form['nummer']) - 1
                    find_note = db['noten'].find()  # get all grades from ,,noten"
                    stud_id = find_note[request_number]['stud_id']
                    subject = find_note[request_number]['subject']
                    find_student = db['user'].find({'_id': stud_id})
                    student = find_student[0]['username']
                    if request.form['actions'] == 'loeschen':
                        return flask.make_response(
                            '<form method="POST" action="note_loeschen" name="note_loeschen"><h2>Geben Sie bitte Name vom Student (' + student + '), für den Sie die Note löschen möchten und Name vom Fach (' + subject + '), ein:</h2>'
                            '<input name="' + student + '" type="text" size="15" maxlength="20" placeholder="Student" required=true><br>'
                            '<input name="' + subject + '" type="text" size="15" maxlength="40" placeholder="Fach" required=true><br>'
                            '<p>Bestätigen bitte Sie auch, dass Sie ' + session['username'] + ' sind:</p>'
                            '<input name="my_user" type="text" size="15" maxlength="20" placeholder="Ihr Benutzername" required=true><br>'
                            '<input name="my_passwd" type="password" size="15" maxlength="20" placeholder="Ihr Passwort" required=true><br>'
                            '<button name="submitButton" tpye="submit" id="passwordSubmit">bestätigen</button><br></form>',
                            302)
                    elif request.form['actions'] == 'bearbeiten':
                        return flask.make_response(
                            '<form method="POST" action="note_bearbeiten" name="note_bearbeiten"><h2>Geben Sie bitte Name vom Student (' + student + '), für den Sie die Note ändern möchten, Name vom Fach (' + subject + ') und die neue Note, ein:</h2>'
                            '<input name="' + student + '" type="text" size="15" maxlength="20" placeholder="Student" required=true><br>'
                            '<input name="' + subject + '" type="text" size="15" maxlength="40" placeholder="Fach" required=true><br>'
                            '<input type="number" step="0.1" id="grades" name="note" min="1" max="5" placeholder="Note" required>'
                            '<p>Bestätigen bitte Sie auch, dass Sie ' + session['username'] + ' sind:</p>'
                            '<input name="my_user" type="text" size="15" maxlength="20" placeholder="Ihr Benutzername" required=true><br>'
                            '<input name="my_passwd" type="password" size="15" maxlength="20" placeholder="Ihr Passwort" required=true><br>'
                            '<button name="submitButton" tpye="submit" id="passwordSubmit">bestätigen</button><br></form>',
                            302)
            elif request.form['submitButton'] == 'cancel':
                return flask.redirect("/administrator")
        return flask.redirect("/notenverwaltung")
    else:
        file = check_status('Administrator')
    return file


# grades management action: delete a grade
@app.route("/note_loeschen", methods = ['POST'])
def note_loeschen():
    # user can only delete a grade if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            my_passwd = hash_passwd(request.form['my_passwd'])
            db        = connect_to_db()
            keys1     = request.form.keys()
            keys2     = []
            for key in keys1:
                keys2.append(key)
            find_admin = db['user'].find({'username': session['username']} and {'role': 'Administrator'}) # get administrator's data from ,,user"
            if find_admin[0]['username'] == request.form['my_user'] and find_admin[0]['passwd'] == my_passwd: # check that the adminstrator has correctly verified the identity
                if str(keys2[0]) == request.form[keys2[0]]:
                    if str(keys2[1]) == request.form[keys2[1]]:
                        student = request.form[keys2[0]]
                        subject = request.form[keys2[1]]
                        find_student = db['user'].find({'username': student})
                        stud_id = find_student[0]['_id']
                        find_grad = db['noten'].find({'subject': subject} and {'stud_id': stud_id})
                        gradToDelete = find_grad[0]
                        db['noten'].delete_one(gradToDelete)
                        return flask.make_response(
                                '<h2>Die Aktion wurde erfolgreich ausgeführt. <a href="/notenverwaltung">hier</a> finden Sie die Notenverwaltung-Seite.</h2>',
                            200)
                    else:
                        return flask.make_response(
                            '<h2>Das eingegebene Fach stimmt mit dem Fach, für das Sie die Note löschen möchten, nicht überein. Versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                            400)
                else:
                    return flask.make_response(
                        '<h2>Der eingegebene Student stimmt mit dem Student, für den Sie die Note löschen möchten, nicht überein. Versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        400)
            else:
                return flask.make_response(
                    '<h2>Ihr Benutzername oder Password haben Sie nicht richtig eingegeben. Versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                    403)
        return flask.make_response(
            '<h2>Die Aktion wurde nicht erfolgreich ausgeführt. Versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
            400)
    else:
        file = check_status('Administrator')
    return file


# grades management action: edit a grade
@app.route("/note_bearbeiten", methods = ['POST'])
def note_bearbeiten():
    # user can only edit a grade if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            my_passwd = hash_passwd(request.form['my_passwd'])
            db        = connect_to_db()
            keys1     = request.form.keys()
            keys2     = []
            for key in keys1:
                keys2.append(key)
            find_admin = db['user'].find({'username': session['username']} and {'role': 'Administrator'}) # get administrator's data from ,,user"
            if find_admin[0]['username'] == request.form['my_user'] and find_admin[0]['passwd'] == my_passwd: # check that the adminstrator has correctly verified the identity
                if str(keys2[0]) == request.form[keys2[0]]:
                    if str(keys2[1]) == request.form[keys2[1]]:
                        student = request.form[keys2[0]]
                        subject = request.form[keys2[1]]
                        mark = request.form['note']
                        find_student = db['user'].find({'username': student})
                        stud_id = find_student[0]['_id']
                        db['noten'].update_one({'subject': subject} and {'stud_id': stud_id}, {'$set': {'mark': mark}})
                        return flask.make_response(
                                '<h2>Die Aktion wurde erfolgreich ausgeführt. <a href="/notenverwaltung">hier</a> finden Sie die Notenverwaltung-Seite.</h2>',
                            200)
                    else:
                        return flask.make_response(
                            '<h2>Das eingegebene Fach stimmt mit dem Fach, für das Sie die Note ändern möchten, nicht überein. Versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                            400)
                else:
                    return flask.make_response(
                        '<h2>Der eingegebene Student stimmt mit dem Student, für den Sie die Note ändern möchten, nicht überein. Versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        400)
            else:
                return flask.make_response(
                    '<h2>Ihr Benutzername oder Password haben Sie nicht richtig eingegeben. Versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                    403)
        return flask.make_response(
            '<h2>Die Aktion wurde nicht erfolgreich ausgeführt. Versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
            400)
    else:
        file = check_status('Administrator')
    return file


# subject management
@app.route("/faecherverwaltung")
def faecherverwaltung():
    # user can only open subject management if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if check_status('Administrator') == 200:
            file    = readhtml('administrator_faecher.html')
            db       = connect_to_db()
            string   = ''
            line    = 0
            find_db  = db['klausuren'].find({"subject": {"$exists": True}})  # get all subjects from ,,klausur"
            for obj_fach in find_db:
                if obj_fach is None:
                    break
                subject = obj_fach['subject']
                line   = line + 1
                profs   = db['user'].find({'_id': obj_fach['prof_id']}) # get profId from ,,user"
                for obj_user in profs:
                    if obj_user is None:
                        break
                    prof = obj_user['username']
                string += '<tr><td>' + str(line) + '</td><td>' + subject + '</td><td>' + prof + '</td></tr>'
            file = re.sub('</tr>', '</tr>' + string, file)  # fill the table with content
        else:
            file = check_status('Administrator')
        return file


# subject management actions
@app.route("/faecher_action", methods = ['POST'])
def faecher_action():
    # user can only do changes in subject management if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            if request.form['submitButton'] == 'submit':
                db = connect_to_db()
                find_db = db['klausuren'].find()  # get all exams from ,,klausuren"
                if request.form['nummer'] == '':
                    return flask.make_response(
                        '<h2>Sie müssen eine Zeile eingeben, versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        400)
                keys1 = request.form.keys()
                if len(list(keys1)) < 3:
                    return flask.make_response(
                        '<h2>Sie müssen eine Aktion auswählen, versuchen Sie bitte <a href="/notenverwaltung">hier</a> noch einmal.</h2>',
                        400)
                if int(request.form['nummer']) > len(list(find_db)):
                    return flask.make_response(
                        '<h2>Die Zeile existiert nicht, versuchen Sie bitte <a href="/faecherverwaltung">hier</a> noch einmal.</h2>',
                        404)
                else:
                    request_number = int(request.form['nummer']) - 1
                    if request.form['actions'] == 'zuweisen':
                        find_fach = db['klausuren'].find()  # get all exams from ,,klausuren"
                        fach      = find_fach[request_number]['subject']
                        find_db   = db['user'].find({'role': 'Professor'})  # get all profs from ,,user"
                        profs     = []
                        for obj_prof in find_db:
                            if obj_prof is None:
                                break
                            profs.append(obj_prof['username'])
                        str_profs = '<br>'.join(profs)
                        return flask.make_response(
                            '<form method="POST" action="fach_zuweisen" name="passwort_ersetzen">'
                            '<h2>Geben Sie bitte Name vom Fach (' + fach + ') und Name vom Professor, dem Sie das Fach zuweisen möchten, ein:</h2>'
                            '<input name="' + fach + '" type="text" size="15" maxlength="20" placeholder="Fach" required=true><br>'
                            '<input name="prof" type="text" size="15" maxlength="40" placeholder="Prof" required=true><br>'
                            '<p>Bestätigen bitte Sie auch, dass Sie ' + session['username'] + ' sind:</p>'
                            '<input name="my_user" type="text" size="15" maxlength="20" placeholder="Ihr Benutzername" required=true><br>'
                            '<input name="my_passwd" type="password" size="15" maxlength="20" placeholder="Ihr Passwort" required=true><br>'
                            '<button name="submitButton" tpye="submit" id="passwordSubmit">bestätigen</button><br>'
                            '<p>hier finden Sie eine Liste von den Professoren, die sich zurzeit im System befinden:</p>'
                            + str_profs + '</form>',
                            302)
            elif request.form['submitButton'] == 'cancel':
                return flask.redirect("/administrator")
        return flask.redirect("/faecherverwaltung")
    else:
        file = check_status('Administrator')
    return file


# subject management action: change assigned prof
@app.route("/fach_zuweisen", methods = ['POST'])
def fach_zuweisen():
    # user can only do the action if he is logged in as an administrator.
    if check_status('Administrator') == 200:
        if request.method == 'POST':
            my_passwd = hash_passwd(request.form['my_passwd'])
            db        = connect_to_db()
            keys1     = request.form.keys()
            keys2     = []
            for key in keys1:
                keys2.append(key)
            find_admin = db['user'].find({'username': session['username']} and {'role': 'Administrator'}) # get administrator's data from ,,user"
            if find_admin[0]['username'] == request.form['my_user'] and find_admin[0]['passwd'] == my_passwd: # check that the adminstrator has correctly verified the identity
                if str(keys2[0]) == request.form[keys2[0]]:
                    fach = request.form[keys2[0]]
                    prof = request.form['prof']
                    find_prof = db['user'].find({'username': prof})
                    if len(list(find_prof)) < 1:
                        return flask.make_response(
                            '<h2>Der eingegebene Professor kann im System nicht gefunden werden. Versuchen Sie bitte <a href="/faecherverwaltung">hier</a> noch einmal.</h2>',
                            404)
                    find_prof = db['user'].find({'username': prof})
                    profId = find_prof[0]['_id']
                    db['klausuren'].update_one({'subject': fach}, {'$set': {'prof_id': profId}})
                    return flask.make_response(
                            '<h2>Die Aktion wurde erfolgreich ausgeführt. <a href="/faecherverwaltung">hier</a> finden Sie die Fächerwervaltung-Seite.</h2>',
                        200)
                else:
                    return flask.make_response(
                        '<h2>Das eingegebene Fach stimmt mit dem Fach, für das Sie den Professor ändern möchten, nicht überein. Versuchen Sie bitte <a href="/faecherverwaltung">hier</a> noch einmal.</h2>',
                        404)
            else:
                return flask.make_response(
                    '<h2>Ihr Benutzername oder Password haben Sie nicht richtig eingegeben. Versuchen Sie bitte <a href="/faecherverwaltung">hier</a> noch einmal.</h2>',
                    403)
        return flask.make_response(
            '<h2>Die Aktion wurde nicht erfolgreich ausgeführt. Versuchen Sie bitte <a href="/faecherverwaltung">hier</a> noch einmal.</h2>',
            400)
    else:
        file = check_status('Administrator')
    return file


# logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return flask.redirect('/')


# START
if __name__ == '__main__':
    app.run(port=1337, debug=True)
