# Scraping Militaria Plaza products

import requests, re, os, time, psycopg2
from bs4 import BeautifulSoup
from datetime import date
from decimal import Decimal
from re import sub
from currency_converter import CurrencyConverter



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



class militariaPlazaProductsScraper:
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
        productSuffix = product.find('a')['href']
        productUrl  = 'https://militariaplaza.nl/'+productSuffix
        response    = requests.get(productUrl)
        productSoup = BeautifulSoup(response.content, 'html.parser')
        return productSoup, productUrl
    
    def scrapeData(self,productSoup):
        
        # scrapeTitle
            try:
                titleElement   = productSoup.find('h2')
                title          = titleElement.text
                title         = title.replace("'","*")
                print (f'TITLE : {title}')
                print ('SUCCESS'.ljust(100,'.')+'TITLE CAPTURED')
            except:
                title = 'None'
                print ('FAILURE'.ljust(100,'.')+'TITLE NOT CAPTURED')
        
        # scrapeDesc
            try:
                descElement = productSoup.find('div',class_='product-description')
                #desc        = re.sub('<[^<]+?>', '', str(descElement))
                desc        = descElement.text
                desc        = desc.strip()
                desc        = desc.replace("'","*")
                print (f'DESC : {desc}')
                print ('SUCCESS'.ljust(100,'.')+'DESC CAPTURED')
            except:
                desc = 'None'
                print ('FAILURE'.ljust(100,'.')+'DESC NOT CAPTURED')
        
        # scrapePrice
            unavailableSince = date.today()
            try:
                c = CurrencyConverter()
                priceElement   = productSoup.find('span', class_='PricesalesPrice')
                price = (priceElement).text
                price = price.replace(',','.')
                price = Decimal(sub(r'[^\d.]', '', price))
                price = c.convert(price,'EUR','USD')
                print ('PRICE'.ljust(100,'.')+f'{price}')
                print ('SUCCESS'.ljust(100,'.')+'PRICE CAPTURED')
                inventoryStatus = 'AVAILABLE'
            except:
                price = 0
                inventoryStatus = 'NULL'
                print ('FAILURE'.ljust(100,'.')+'PRICE NOT CAPTURED')

        # scrapeImage
            try:
                imageThumbElement    = productSoup.find('div', class_='product-single__photo')
                imageThumb           = imageThumbElement.find('img')['src']
                print ('SUCCESS'.ljust(100,'.')+'IMAGES CAPTURED')
            except:
                imageThumb = 'None'
                print ('FAILURE'.ljust(100,'.')+'IMAGE NOT CAPTURED')

        # scrapeCategories
            try:
                categoriesElement = productSoup.find('div',class_='product-single__meta small--text-center')
                category = categoriesElement.text
                category = category.split('-')[0].strip()
                collections = {'C': 'Cloth Insignia','B':'Belt Buckle','BK':'Book','HG':'Headgear','E':'Edged Blade','F':'Field Gear','FL':'Flag','USU':'US Uniform','U':'Uniform','M':'Medal','S':'Specialty','H':'Helmet','USF':'US Field Gear','JBH':'Helmet','JBD':'Document'}
                if category in collections:
                    category = collections[category]
                print (f'CATEGORIES : {category}')
            except:
                category = 'None'
        # return info back to main()
            return ([title,desc,price,imageThumb,inventoryStatus,unavailableSince,category])





def main():

    hostName = 'localhost'
    dataBase = 'Militaria Products'
    userName = 'postgres'
    pwd      = 'poop'
    portId   = 5432

    dataManager      = PostgreSQLProcessor(hostName, dataBase,userName,pwd,portId)
    webScrapeManager = militariaPlazaProductsScraper(dataManager)

    firstProduct = 1
    lastProduct  = 50
    page = f'{firstProduct}-{lastProduct}'
    urlCount = 0
    while True:
        url = f'https://militariaplaza.nl/new/results,{page}'
        firstProduct += 50
        lastProduct  += 50
        print(f'URL : {url}')
        soup = webScrapeManager.readProductPage(url)

        #Iterate through every item on product page
        products = soup.find_all('div',class_= 'vm-product-descr-container-1')
        
        consecutiveMatches = 0
        for product in products :
            #if consecutiveMatches == 100:
             #   print (f'{consecutiveMatches} MATCHES MET'.ljust(100,'.')+'WAITING 5 MINUTES')
              #  time.sleep(300)
               # break
            urlCount += 1
            print(f'URL COUNT : {urlCount}'.center(150,'-'))
            productSoup,productUrl = webScrapeManager.scrapePage(product)
            ([title,desc,price,imageThumb,inventoryStatus,unavailableSince,category]) = webScrapeManager.scrapeData(productSoup)
            productID = webScrapeManager.productIDGenerator()

            #IF ITEM IN LIST, UPDATE IT
            searchQuery = f'''SELECT product_thumbnail 
                            FROM products 
                            WHERE product_thumbnail LIKE '{imageThumb}' '''
            cellValue = dataManager.sqlFetch(searchQuery)
            match = [tup[0] for tup in cellValue]

            if imageThumb in match:
                consecutiveMatches += 1
                updateStatus = f'''  UPDATE products
                                    SET status = 'SOLD'
                                    WHERE product_thumbnail = '{imageThumb}';'''
                updateSoldDate = f'''  UPDATE products
                                    SET sold_date = '{unavailableSince}'
                                    WHERE product_thumbnail = '{imageThumb}';'''
                dataManager.sqlExecute(updateStatus)
                dataManager.sqlExecute(updateSoldDate)
                print (f'PRODUCT {title} ALREADY IN SYSTEM'.center(150,'-'))
                continue
            else:
                consecutiveMatches = 0

            #IF ITEM NOT IN LIST, ADD IT
                todayDate = date.today()
                productOrigin = 'RUPTURED DUCK'
                appendQuery = f'''  INSERT INTO products 
                                    (url, product_id, title, description, price, product_thumbnail, status,data_enter_date,sold_date,product_origin,categories) 
                                    VALUES ('{productUrl}','{productID}', '{title}', '{desc}', '{price}', '{imageThumb}', '{inventoryStatus}','{todayDate}','{unavailableSince}','{productOrigin}','{category}')'''
                #dataManager.sqlExecute(appendQuery)
            print (f"""                   
--------------------------------------------
Captured File       : {productID}
Product Name        : {title}
Product Description : {desc}
Price               : ${price}
Image ThumbNail     : {imageThumb}
Inventory Status    : {inventoryStatus}
Unavailable Since   : {unavailableSince}
--------------------------------------------
""")








if __name__ == "__main__":
    main()
