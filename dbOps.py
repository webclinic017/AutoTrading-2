#!/usr/bin/env python
# (C) Copyright Swapnanil Sharmah 2021
# @brief: API

import numpy as np
import pandas as pd
import json
import sqlite3
import datetime
import os
import string
import random


class DBOperations():

    def __init__(self, dbName="siraj.db"):
        self.dbName = dbName

    def createTable(self):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        conn.execute('''CREATE TABLE IF NOT EXISTS MASTER_TABLE(record_id      CHAR(100) NOT NULL, 
                                                                device         CHAR(300) NOT NULL,
                                                                email          CHAR(100) PRIMARY KEY NOT NULL
                                                                );''')
        conn.close()

    def addUser(self, device, email):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        total_rec = conn.execute('''SELECT COUNT(*) FROM MASTER_TABLE;''')
        idx = "record_"+str(list(total_rec)[0][0] + 1)
        conn.execute('INSERT INTO MASTER_TABLE VALUES (?,?,?)', (idx, device, email))
        conn.commit()
        conn.close()
        return idx

    def getUser(self, email):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        df = pd.read_sql_query(
            "SELECT device FROM MASTER_TABLE WHERE email = " + repr(str(email)), conn)
        conn.close()
        return df.values.tolist()[0][0]

    def generateCoupon(self, email, transectionid, amount, redeemed=0):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        expirydate = datetime.date.today() + datetime.timedelta(days=60)
        couponcode = ''.join(random.choices(string.ascii_uppercase +
                             string.ascii_lowercase, k=12))
        total_rec = conn.execute('''SELECT COUNT(*) FROM COUPON_TABLE;''')
        idx = "record_" + str(list(total_rec)[0][0] + 1)
        conn.execute('INSERT INTO COUPON_TABLE VALUES (?,?,?,?,?,?,?)', (idx, email, couponcode,
                                                                       transectionid, amount, redeemed, expirydate))
        conn.commit()
        conn.close()
        return couponcode

    def updateCoupon(self, email, couponcode, redeemed=1):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        try:
            conn.execute('UPDATE COUPON_TABLE SET redeemed =? WHERE email=? AND couponcode=?', (redeemed, email, couponcode))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def validateCoupon(self, email, couponcode):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        df = pd.read_sql_query(
            "SELECT redeemed, expirydate FROM COUPON_TABLE WHERE email = " +
            repr(str(email)) + " AND couponcode = " + repr(str(couponcode)), conn)
        reedemed, expirydate = df.values.tolist()[0][0], df.values.tolist()[0][1]
        expirydate = datetime.datetime.strptime(expirydate, "%Y-%m-%d").date()
        conn.close()
        if reedemed == 0 and expirydate >= datetime.date.today():
            return True
        return False

    def availableCoupons(self, email):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        df = pd.read_sql_query(
            "SELECT * FROM COUPON_TABLE WHERE email = " + repr(str(email)), conn)
        conn.close()
        return df

    def updatePassword(self, email, password):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        try:
            conn.execute('UPDATE MASTER_TABLE SET password =? WHERE email=?', (password, email))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def validateEmail(self, email):
        conn = sqlite3.connect(self.dbName, check_same_thread=False)
        df = pd.read_sql_query(
            "SELECT COUNT(*) FROM MASTER_TABLE WHERE email = " + repr(str(email)), conn)
        conn.close()
        if df.values.tolist()[0][0]==1:
            return True
        else:
            return False