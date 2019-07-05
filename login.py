'''
Created on 20190622

@author: liao.zeno
'''


import pickle
import hashlib
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from os import path

#import dirsync

class Login():
    def __init__(self):
        super().__init__()
        self.username = ""
        ## check if the database exists.
        if path.isfile('database.db'):
            fh = open('database.db', 'rb')
            self.db = pickle.load(fh)
            fh.close()
        ## else, create one.
        else:
            self.db = {'admin': self.Encryption('7110'),
                       'rixs': self.Encryption('123456'),
                       'user': self.Encryption('123')}
            fh = open('database.db', 'wb')
            pickle.dump(self.db, fh)
            fh.close()

    def Encryption(self, data):
        return hashlib.sha224(data.encode()).hexdigest()

    def checkUser(self, username):
        print('user name: ', username)
        if username in self.db:
            self.username = username
            return True
        else:
            return False

    def handleLogin(self, password):## If the user exists in the "db", and then decoded password
        if self.db[self.username] == self.Encryption(password):
            if self.username == 'admin':
                return 2
            else:
                return 1
        else:
            return 0

    def adduser(self, newuser, password):
        with open('database.db', 'rb') as fh:
            db = pickle.load(fh)

        db[newuser] = self.Encryption(password)

        with open('database.db', 'wb') as fh:
            pickle.dump(db, fh)
            
    def deluser(self, username):
        with open('database.db', 'rb') as fh:
            db = pickle.load(fh)

        if username in db:
            del db[username]
            flag = True
        else:
            flag = False

        with open('database.db', 'wb') as fh:
            pickle.dump(db, fh)

        return flag

