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
    string = re.sub('<span id="studentname"></span>', '<span id="studentname">'+session['username']+'</span>', string)
    return string

def connect_to_db():
    global db
    if (db is None):
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
    datei    = readhtml('student.html')
    return datei

@app.route("/noteneinsicht")
def noteneinsicht():
    datei   = readhtml('student_noteneinsicht.html')
    db      = connect_to_db()
    col     = db['user']
    find_db = col.find( {'username': session['username']} ) #hole unseren eingeloggten user
    user    = find_db[0]
    find_db = db['noten'].find( {'stud_id': user['_id']} ) # nur die noten vom eingeloggten user
    string  = '' #für unsere tabelle die gefüllt wird
    for obj_note in find_db:
        subject = str(obj_note['subject'])
        grade   = str(obj_note['mark'])
        date    = str(obj_note['date'])
        string += '<tr><td>' + subject + '</td><td>' + grade + '</td><td>' + date + '</td></tr>'
    datei = re.sub('</tr>', '</tr>' + string, datei) #fülle die tabelle mit inhalt
    return datei

@app.route("/klausuren")
def klausuren():
    checkbox = ''
    db       = connect_to_db()
    usr_col  = db['user']
    user     = usr_col.find({'username' : session['username']})  #hole unseren eingeloggten user
    fak      = user[0]['faculty'] # welche fakultät hat der user
    col      = db['studiengang']
    find_db  = col.find( {'faculty': fak} ) #hole alle fächer von dieser fakulktät
    faecher  = find_db[0]['subjects']
    string   = ''
    for fach in faecher:

    return readhtml('student_klausuren.html')

@app.route("/professor")
def professor():
    return readhtml('professor.html')

@app.route("/noten")
def noten():
    return readhtml('professor_noten.html')

@app.route("/klausuren?=68E92D")
def klaus():
    return readhtml('professor_klausuren.html')

@app.route("/administrator")
def administrator():
    return readhtml('administrator.html')

# START
if __name__ == '__main__':
    app.run(port=1337, debug=True)
