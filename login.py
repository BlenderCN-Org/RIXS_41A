'''
Created on 20190622

@author: liao.zeno
'''


import pickle
import hashlib
from os import path

#import dirsync

class Login():
    def __init__(self):
        super().__init__()

    def Encryption(self, data):
        return hashlib.sha224(data.encode()).hexdigest()

    def handleLogin(self, username, password):
        ## check if the database exists.
        if path.isfile('database.db'):
            fh = open('database.db', 'rb')
            db = pickle.load(fh)
            fh.close()
        ## else, create one.
        else:
            db = {'rixs' : self.Encryption('123456'), 'user' : self.Encryption('123')}
            fh = open('database.db', 'wb')
            pickle.dump(db, fh)
            fh.close()

        ## If the user exists in the "db", and then decoded password
        if username in db and db[username] == self.Encryption(password):
            return True
        else:
            return False

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