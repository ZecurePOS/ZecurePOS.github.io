# -*- coding: utf-8 -*-
from flask import Flask, request
import pymongo
from pymongo import MongoClient
import flask
from flask import session
import re

app = Flask(__name__)

######## GLOBALS ########
db = None

#########################


def readhtml(filename):
    data = open(filename, "r")
    str  = data.read()
    data.close()
    return str


def connect_to_db():
    global db
    if (db is None):
        CONNECTION_STRING = 'mongodb://Nagel:xL8NyJYnnKkuBM4WaVz8NVsGTg@192.168.0.90:27018'
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

######################################################################################

@app.route("/")
def init():
    return readhtml('login.html')

@app.route("/validate", methods = ['POST'])
def validate():

    db = connect_to_db()

    if request.method=='POST':
        email   = request.form['email']
        pw      = hash_passwd( request.form['passwd'] )
        col     = db['user']
        find_db = col.find( {'email': email, 'passwd': pw} )
        for user in find_db:
            session['username'] = user['username']
            session['role']     = user['role']
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
    replaced = re.sub('<span id="studentname"></span>', '<span id="studentname">'+session['username']+'</span>', datei)
    return replaced


@app.route("/noteneinsicht")
def noteneinsicht():
    return readhtml('noteneinsicht.html')


@app.route("/klausuren")
def klausuren():
    return readhtml('klausuren.html')


@app.route("/professor")
def klausuren():
    return readhtml('professor.html')


@app.route("/administrator")
def klausuren():
    return readhtml('administrator.html')


#start
if __name__ == '__main__':
    app.run(port=1337, debug=True)
