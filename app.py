#!/usr/bin/env python
# (C) Copyright Swapnanil Sharmah 2021
# @brief: API

from flask import Flask, jsonify, request, session
import json
import sys
from dbOps import DBOperations
from flask_cors import CORS, cross_origin
import logging
import random
from email.message import EmailMessage
import smtplib
import datetime
import os
from datetime import timedelta, datetime
import stripe
from flask_session import Session
import logging
import ast
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import time
import requests
import hmac
import hashlib
import sqlite3
import ctypes
import ccxt

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
CORS(app)
DBNAME = "siraj.db"



def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])
    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)
    return tr

def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()
    return atr 

def supertrend(df, period=10, atr_multiplier=1.5):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True
    for current in range(1, len(df.index)):
        previous = current - 1
        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]
            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]
            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]    
    return df

in_position = False
short_position = False

def check_buy_sell_signals(df):
    global in_position
    global short_position
    print("Analyzing Technical Analysis")
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1 
    third_row_index = previous_row_index - 1
    forth_row_index = third_row_index - 1
    fifth_row_index = forth_row_index - 1
    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
       print("Taking a Long Position")
       try:
           order = exchange.create_market_buy_order(symbol, amount, params)
       except:
             pass
       try:
           if not in_position:
                  order = exchange.create_market_buy_order(symbol, amount)
                  print(order)
                  time.sleep(20) # Sleep for 20 seconds
                  order = exchange.create_order(symbol, order_type, side2, amount, price, paramss)
                  print("Trailing stop loss updated")
                  in_position = True
                  short_position = False
       except:
             print("Error! Unable to enter trade,check your settings")
             pass
            
    
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
       print("Taking a Short Position")
       try:
           order = exchange.create_market_sell_order(symbol, amount, params)
       except:
             pass
       try:
           if not short_position:
              order = exchange.create_market_sell_order(symbol, amount)
              print(order)
              time.sleep(20) # Sleep for 20 seconds
              order = exchange.create_order(symbol, order_type, side1, amount, price, paramss)
              print("Trailing stop loss updated")
              short_position = True
              in_position = False
       except:
             print("Error! Unable to enter trade,check your settings")
             pass

def main_process(exchange, symbol):
    #markets = exchange.load_markets()
    markets = exchange.fetch_ohlcv(symbol, timeframe='3m', limit=100)
    output = {"data": markets, "validation": True}
    try:
        def run_bot():
            print(f"Fetching new charts for {datetime.now().isoformat()}")
            try:
                bars = exchange.fetch_ohlcv(symbol, timeframe='3m', limit=100)
                df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                supertrend_data = supertrend(df)
                check_buy_sell_signals(supertrend_data)
            except:
                print("Binance Network error")
                pass
        run_bot()
    except:
        print("Network error")
        run_bot()
    return output


@app.route('/validateuser', methods=['POST'])
def validateuser():
    email = request.args.get('email') or request.get_json().get('email', '')
    device = request.args.get('device') or request.get_json().get('device', '')
    BINANCE_API_KEY = request.args.get('BINANCE_API_KEY') or request.get_json().get('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = request.args.get('BINANCE_SECRET_KEY') or request.get_json().get('BINANCE_SECRET_KEY', '')
    symbol = request.args.get('symbol') or request.get_json().get('symbol', '')
    global percent
    global amount
    percent = request.args.get('stoploss') or request.get_json().get('stoploss', '')
    amount = request.args.get('size') or request.get_json().get('size', '')


    global side1, side2, order_type, rate, yes, price, paramss, params, leverage
    side1 = 'buy'
    side2 = 'sell'
    order_type = 'TRAILING_STOP_MARKET'
    rate = 'true'
    yes = 'true'
    price = None
    paramss = {
        'callbackRate': percent,
        'ReduceOnly': rate,
    }
    params = {
        'ReduceOnly': rate
    }
    leverage =  10

    account = {'email': email}
    payload = account
    response = requests.get('https://thecryptosignalguy.com/bot/api.php', params=payload)
    if "1" in response.json():
        db = DBOperations(dbName=DBNAME)
        db.createTable()
        try:
            record_id = db.addUser(device, email)

            exchange = ccxt.binanceusdm({"apiKey":BINANCE_API_KEY,
                                         "secret":BINANCE_SECRET_KEY,
                                         "enableRateLimit": True})
            return jsonify(main_process(exchange, symbol))
        except sqlite3.IntegrityError:
            if device != db.getUser(email):
                return jsonify({"validation": False, "reason": "email is valid, but device is not matching with registered device"})
            else:
                exchange = ccxt.binanceusdm({"apiKey":BINANCE_API_KEY,
                                             "secret":BINANCE_SECRET_KEY,
                                             "enableRateLimit": True})
                return jsonify(main_process(exchange, symbol))
    else:
        return jsonify({"validation": False, "reason": "email is not valid"})



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7777, debug=True)