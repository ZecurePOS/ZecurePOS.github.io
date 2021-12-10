# -*- coding: utf-8 -*-
from flask import Flask, request
import pymongo
from pymongo import MongoClient

"""
################################################

# DB-Credentials -> spaeter Config file oder so
address  = '149.172.144.70' # aktuelle gebe ich dir wenn ich portfreigabe mache
#address  = 'localhost'
port     = 27017
username = None
password = None
db_name  = 'gdv'
#################################################


class DB:


    def init( self, addr, port, username, password, db_name ):
        self.addr     = addr
        self.port     = port
        self.username = username
        self.password = password
        self.db_name  = db_name

        self.client = MongoClient( address, port )
"""

def readhtml(filename):
    data     = open(filename, "r")
    str      = data.read()
    data.close()
    return str

app = Flask(__name__)

@app.route("/")
def init():
    return readhtml('login.html')

@app.route("/validate", methods=['POST'])
def validate():
    name = ""
    pw   = ""

    if request.method == 'POST':
        name = request.form[ 'email' ]
        pw   = request.form[ 'passwd' ]
        # suche in db nach email und check ob passwort stimmt und rolle
        # wenn email net da ist kommt meldung zum regisitrieren
        # wenn ja, dann entscheide nach rolle und leite weiter zu prof oder student
        return 'validating'


@app.route("/student")
def student():
    return readhtml('student.html')


@app.route("/noteneinsicht")
def noteneinsicht():
    return readhtml('noteneinsicht.html')


@app.route("/klausuren")
def klausuren():
    return readhtml('klausuren.html')


#start
if __name__ == '__main__':
    app.run(port=1337, debug=True)
