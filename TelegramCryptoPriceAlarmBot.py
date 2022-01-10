# -*- coding: utf-8 -*-
from time import sleep
import requests
from bs4 import BeautifulSoup
import json
from requests import Session


# please do not use this token :) 
token = "5042153408:AAESkQlsFaD7_crr4PnC-iPOHI9daXaXG6k"
url = "https://api.telegram.org/bot" + token

alarm_list = []

def get_top_ten():
    prices = []
    url= "https://coinmarketcap.com"
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "html.parser")
    price_table = soup.find('tbody')
    prices_row = price_table.find_all('tr')
    for price_col in prices_row[:10]:
        name = price_col.findChildren('td')[2].findChild('div').findChild('p').text
        price = price_col.findChildren('td')[3].text
        prices.append(f'{name} current price is {price}')
    return prices
    
def get_updates_json(request):  
    params = {'timeout': 100, 'offset': None}
    response = requests.get(request + '/getUpdates', data=params)
    return response.json()

def last_update(data):  
    results = data['result']
    total_updates = len(results) - 1
    return results[total_updates]

def get_update_id(data):
    return data['update_id']

def get_chat_id(update):  
    chat_id = update['message']['chat']['id']
    return chat_id

def get_user_message():
    return last_update(get_updates_json(url))['message']['text']

def send_mess(chat, text):  
    params = {'chat_id': chat, 'text': text}
    response = requests.post(url + '/sendMessage', data=params)
    return response

def set_btc_alert(chat_id, price):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
        'slug' : 'bitcoin','convert' : 'USD'
    }
    headers = {
        'Accepts' : 'application/json',
        'X-CMC_PRO_API_KEY' : '402ac260-61f4-4801-9640-b480e3aa6b91'   
        }    
    session = Session() 
    session.headers.update(headers)
    response = session.get(url, params = parameters)
    btc_price = format(json.loads(response.text)['data']['1']['quote']['USD']['price'], '.2f')
    btc_price = float(btc_price)

    range_btc_up = btc_price * 1.01
    range_btc_down = btc_price * 0.99

    if price <= range_btc_up and btc_price >= range_btc_down :
        send_mess(chat_id, f'ALARM!!! current BTC price --> {btc_price}')
        return True
    return False

def set_alarm(chat_id, update_id):
    l_update = last_update(get_updates_json(url))
    user_alarm = {}
    if update_id != get_update_id(l_update):
        # chat_id = get_chat_id(l_update)
        user_message = get_user_message().lower()
        if user_message.isdigit():
            user_alarm['chat_id'] = chat_id
            user_alarm['price'] = float(user_message)
            alarm_list.append(user_alarm)
        # set_btc_alert(int(user_message))
        return True

def check_alarms():
    for alarm in alarm_list:
        print(f'checking alarm --> {alarm}')
        # print(f'checking alarm --> {type(alarm)}')
        status = set_btc_alert(alarm['chat_id'], alarm['price'])
        if status:
            alarm_list.remove(alarm)

last_update_id = 0
while True:
    check_alarms()
    l_update = last_update(get_updates_json(url))
    update_id = get_update_id(l_update)
    
    chat_id = get_chat_id(l_update)
    user_message = get_user_message().lower()

    if update_id != last_update_id:
        if user_message == '/price':
            print('we are in price section')
            prices = get_top_ten()
            prices_in_str = ''
            for price in prices:
                prices_in_str = prices_in_str + '\n' + price        
            send_mess(chat_id, prices_in_str)
    
        if user_message == '/alarm':
            print('we are in alarm section')
            send_mess(chat_id, 'please tell us your alarm price:')
            while True:
                status = set_alarm(chat_id, update_id)
                if status:
                    send_mess(chat_id, 'alarm set')
                    break                
        
        last_update_id = update_id