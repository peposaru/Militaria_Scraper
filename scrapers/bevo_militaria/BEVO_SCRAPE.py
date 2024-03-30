# Scraping Bevo Militaria Site

import requests, re, psycopg2, time
from bs4 import BeautifulSoup
from datetime import date
from currency_converter import CurrencyConverter
from decimal import Decimal
from re import sub



class PostgreSQLProcessor:
    def __init__(self,hostName, dataBase,userName,pwd,portId):
        self.hostName = hostName
        self.dataBase = dataBase
        self.userName = userName
        self.pwd      = pwd
        self.portId   = portId
        self.conn     = psycopg2.connect(
                        host = hostName,
                        dbname = dataBase,
                        user = userName,
                        password = pwd,
                        port = portId)
        self.cur      = self.conn.cursor()


    def sqlExecute(self,query):
        self.cur.execute(query)
        self.conn.commit()

    def sqlFetch(self,query):
        self.cur.execute(query)
        cellValue = self.cur.fetchall()
        return cellValue

    def sqlClose(self):
        self.cur.close()
        self.conn.close()


class BevoItemsScraper:
    def __init__(self,spreadSheetManager):
         self.spreadSheetManager = spreadSheetManager

    def productIDGenerator(self):
        lastProductID = self.spreadSheetManager.sqlFetch('''SELECT MAX(product_id) FROM products''') 
        productID = int(lastProductID[0][0]) + 1
        print (f'ASSIGNING ID'.ljust(100,'.')+ F'{productID}')
        return productID

    def readProductPage(self,url):
        response = requests.get(url)
        soup     = BeautifulSoup(response.content, 'html.parser')
        print ('SUCCESS'.ljust(100,'.')+'SOUP CAPTURED')
        return soup

    def scrapePage(self,product):
        aTag  = product.find('a', class_='woocommerce-LoopProduct-link-title')
        productUrl = aTag.get('href')
        print(f'PRODUCT URL : {productUrl}')
        response    = requests.get(productUrl)
        productSoup = BeautifulSoup(response.content, 'html.parser')
        return productSoup, productUrl

    def scrapeData(self,productSoup):
        # scrapeTitle
            try:
                titleElement   = productSoup.find('h1', class_='product_title entry-title')
                title          = titleElement.text
                print (f'TITLE | {title}')
                print ('SUCCESS'.ljust(100,'.')+'TITLE CAPTURED')
            except:
                title = 'UKNOWN'
        # scrapeDesc
            try:
                descElement = productSoup.find('div',class_='woocommerce-Tabs-panel woocommerce-Tabs-panel--description panel entry-content wc-tab')
                desc        = descElement.text
                desc        = desc.strip()
                desc        = desc.replace("'","*")
                print (f'DESCRIPTION | {desc}')
                print ('SUCCESS'.ljust(100,'.')+'DESC CAPTURED')
            except:
                desc = 'UNKNOWN'
        # scrapePrice
            try:
                c = CurrencyConverter()
                priceElement   = productSoup.find('span',class_='woocommerce-Price-amount amount')
                price = priceElement.text
                price = price.replace(',','.')
                price = Decimal(sub(r'[^\d.]', '', price))
                price = c.convert(price,'EUR','USD')
                print (f'PRICE | {price}')
                print ('SUCCESS'.ljust(100,'.')+'PRICE CAPTURED')
            except:
                price = '0'
        # scrapeImage
            try:
                imageThumbElement    = productSoup.find('div', class_="woocommerce-product-gallery__wrapper")
                imageThumb           = imageThumbElement.find('img')['src']
                print (f'Image Thumb | {imageThumb}')
                print ('SUCCESS'.ljust(100,'.')+'IMAGES CAPTURED')
            except:
                imageThumb = 'UNKNOWN'
        # scrapeInvStatus
            try:
                inventoryStatus = productSoup.find('p',class_='stock in-stock').text
                inventoryStatus = 'AVAILABLE'
                unavailableSince = None
            except:
                inventoryStatus = 'SOLD'
                unavailableSince = date.today()


            print (inventoryStatus)

        # return info back to main()
            return ([title,desc,price,imageThumb,inventoryStatus,unavailableSince])



def main():

    hostName = 'localhost'
    dataBase = 'Militaria Products'
    userName = 'postgres'
    pwd      = 'poop'
    portId   = 5432

    dataManager      = PostgreSQLProcessor(hostName, dataBase,userName,pwd,portId)
    webScrapeManager = BevoItemsScraper(dataManager)
    urlCount = 0
    page = 2
    while True:
        url = f'https://bevo-militaria.com/shop/page/{page}/'
        page += 1
        print(f'URL : {url}')
        soup = webScrapeManager.readProductPage(url)
        #Iterate through every item on product page
        products = soup.find_all('li',class_= 'product')
        consecutiveMatches = 0
        for product in products :
            if consecutiveMatches == 200:
                print (f'{consecutiveMatches} MATCHES MET'.ljust(100,'.')+'WAITING 5 MINUTES')
                time.sleep(300)
                break
            print('NEW PRODUCT'.center(100,'-'))
            urlCount += 1
            print(f'URL COUNT : {urlCount}'.center(100,' '))
            productSoup,productUrl = webScrapeManager.scrapePage(product)
            #IF ITEM IN LIST, UPDATE IT
            searchQuery = f"SELECT url FROM products WHERE url LIKE '{productUrl}'"
            cellValue = dataManager.sqlFetch(searchQuery)
            match = [tup[0] for tup in cellValue]
            if productUrl in match:
                consecutiveMatches += 1
                print (f'PRODUCT ALREADY IN SYSTEM'.center(100,'*'))
                continue
            else:
                consecutiveMatches = 0
                ([title,desc,price,imageThumb,inventoryStatus,unavailableSince]) = webScrapeManager.scrapeData(productSoup)
                productID = webScrapeManager.productIDGenerator()
                #IF ITEM NOT IN LIST, ADD IT
                todayDate = date.today()
                appendQuery = f'''INSERT INTO products (url, product_id, title, description, price, product_thumbnail, status,data_enter_date,product_origin) VALUES ('{productUrl}','{productID}', '{title}', '{desc}', {price}, '{imageThumb}', '{inventoryStatus}','{todayDate}','BEVO-MILITARIA')'''
                dataManager.sqlExecute(appendQuery)
                print (f"""                   
--------------------------------------------
Page                : {page}
Captured File       : {productID}
Product Name        : {title}
Product Description : {desc}
Price               : {price}
Image ThumbNail     : {imageThumb}
Inventory Status    : {inventoryStatus}
Unavailable Since   : {unavailableSince}
--------------------------------------------
""")
            

if __name__ == "__main__":
    main()