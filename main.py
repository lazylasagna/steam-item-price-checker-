import requests
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA
import warnings
import keyboard
import time
warnings.filterwarnings("ignore")

def func(url, database):

    def rub(price):
        if price.count('TL') > 0:
            price = price.replace('TL', '')
            price = price.replace(',', '.')
            if all(c.isdigit() or c == '.' for c in price):
                price = float(price) * 3.96
        elif price.count('¥') > 0:
            price = price.replace('¥', '')
            if all(c.isdigit() or c == '.' for c in price):
                price = float(price) * 10,97
        elif price.count('$') > 0:
            price = price.replace('$', '')
            if all(c.isdigit() or c == '.' for c in price):
                price = float(price) * 74.71
        elif price.count('zł') > 0:
            price = price.replace('zł', '')
            price = price.replace(',', '.')
            if all(c.isdigit() or c == '.' for c in price):
                price = float(price) * 16.93
        elif price.count('S/.') > 0:
            price = price.replace('S/.', '')
            if all(c.isdigit() or c == '.' for c in price):
                price = float(price) * 19.9
        elif price.count('€') > 0:
            price = price.replace('€', '')
            price = price.replace(',', '.')
            if all(c.isdigit() or c == '.' for c in price):
                price = float(price) * 79.57
        elif price.count('pуб.') > 0:
            price = price.replace(',', '.')
            price = price.replace('pуб.', '')
        return price


    # Подключение к базе данных MySQL
    mydb = mysql.connector.connect(
        host="localhost",
        user="", #вставить свое
        password="",
        database=database
    )
    mycursor = mydb.cursor()
    # Создание таблицы для хранения цен, если ее еще не существует
    mycursor.execute('''CREATE TABLE IF NOT EXISTS prices
                        (id INT AUTO_INCREMENT PRIMARY KEY,
                        timestamp DATETIME NOT NULL,
                        price FLOAT NOT NULL)''')
    l = ''
    d = {'pуб.': 0, '¥': 0, '$': 0, 'zł': 0, 'S/.': 0, '€': 0, 'TL': 0}
    # Запрос страницы и создание объекта BeautifulSoup для извлечения информации
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    # Извлечение цены из HTML-кода страницы
    price_string = soup.find_all(class_='market_table_value')
    array = ['</span>', '<span class="market_listing_price market_listing_price_with_fee">',
             '<span class="market_listing_price market_listing_price_with_publisher_fee_only">',
             '<span class="market_listing_price market_listing_price_without_fee">', '<br>', '<br/>',
             '</n>', '</br>', ' ', '\t', '-', 'USD', '\r', '\n']
    i = 0
    for price_str2 in price_string:
        for price_str1 in price_str2:
            i += 1
            if i % 3 == 1:
                for j in array:
                    price_str1 = str(price_str1).replace(j, '')
                for e in d:
                    if price_str1.count(e)>0:
                        d[e]+=1
                l += price_str1
                l += ' '
                #print(price_str1)

    #for e in d:
        #print(e, d[e], ' ', end ="")
    #print()
    # Получение списка цен из базы данных для анализа
    prices = []
    query = "SELECT price FROM prices ORDER BY timestamp"
    mycursor.execute(query)
    result = mycursor.fetchall()
    if result is not None:
        for row in result:
            prices.append(row[0])
    print(prices)

    for price_str in l.split():
        price = rub(price_str)
        if all(c.isdigit() or c == '.' for c in str(price)):
            price = round(float(price), 2)
            #print(price, 'руб')

            #if price not in prices:
            print('Добавлен:', price, 'руб')
            # Добавление цены и временной метки в базу данных
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            query = "INSERT INTO prices (timestamp, price) VALUES (%s, %s)"
            values = (now, price)
            mycursor.execute(query, values)
            mydb.commit()

    mycursor.close()
    mydb.close()

def prognose(database):
    # Подключение к базе данных MySQL
    mydb = mysql.connector.connect(
        host="localhost",
        user="",
        password="",
        database=database
    )
    mycursor = mydb.cursor()
    # Создание таблицы для хранения цен, если ее еще не существует
    mycursor.execute('''CREATE TABLE IF NOT EXISTS prices
                            (id INT AUTO_INCREMENT PRIMARY KEY,
                            timestamp DATETIME NOT NULL,
                            price FLOAT NOT NULL)''')
    # Получение списка цен из базы данных для анализа
    prices = []
    query = "SELECT price FROM prices ORDER BY timestamp"
    mycursor.execute(query)
    result = mycursor.fetchall()
    if result is not None:
        for row in result:
            prices.append(row[0])
    print(prices)
    # Прогнозирование изменения цен с помощью модели ARIMA
    if len(prices) > 0:
        model = ARIMA(prices, order=(1, 1, 1))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=7)
        forecast_list = forecast.tolist()
        print('Прогноз изменения цен на неделю вперед:')
        for i, price in enumerate(forecast_list):
            print(f'{i + 1} день: {price:.2f}руб.')
    else:
        print("No data available for analysis")
    #Закрытие соединения с базой данных
    mycursor.close()
    mydb.close()
# URL страницы с информацией о предмете на торговой площадке Steam
url = 'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Field-Tested%29'

while True:
    flag = False
    func(url, 'prices')
    for i in range(60):
        for j in range(60):
            if keyboard.is_pressed('q'):
                flag = True
                break
            time.sleep(1)
    if flag: break
prognose('prices')
