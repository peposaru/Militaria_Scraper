# Scraping Stewart's Militaria Archives

import requests, re, os, time, psycopg2
from bs4 import BeautifulSoup
from datetime import date
from decimal import Decimal
from re import sub


# FIRST PHASE: GET THE WEBSCRAPER READY
    # A : GET ALL FOR SALE ITEMS
        # 1 : IF NEW ITEM IN DATABASE
            # a: FINISH PAGE AND BREAK
        # 2 : IF NEW ITEM NOT IN DATABASE
            # APPEND DATABASE WITH NEW ITEM
        # 3 : CHECK ARCHIVE UPDATES ON ITEMS SOLD 
            #-> NOT RELEVANT UNTIL ALL FOR SALE ITEMS PROCESSED
    # B : CHECK ARCHIVES FOR ITEMS SOLD
# SECOND PHASE : POSTGRESQL

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


class StewartsArchiveScraper:
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
        productUrl  = product.find('a')['href']
        response    = requests.get(productUrl)
        productSoup = BeautifulSoup(response.content, 'html.parser')
        return productSoup, productUrl
    
    def scrapeData(self,productSoup):
        
        # scrapeTitle
            try:
                titleElement   = productSoup.find('div', class_='section-title')
                title          = titleElement.text
                title         = title.split('\n')[1]
                title         = title.replace("'","*")
                print (f'TITLE : {title}')
                print ('SUCCESS'.ljust(100,'.')+'TITLE CAPTURED')
            except:
                title = 'NULL'
                print ('FAILURE'.ljust(100,'.')+'TITLE NOT CAPTURED')
        
        # scrapeDesc
            try:
                descElement = productSoup.find('p')
                desc        = re.sub('<[^<]+?>', '', str(descElement))
                desc        = desc.strip()
                desc        = desc.replace("'","*")
                print (f'DESC : {desc}')
                print ('SUCCESS'.ljust(100,'.')+'DESC CAPTURED')
            except:
                desc = 'NULL'
                print ('FAILURE'.ljust(100,'.')+'DESC NOT CAPTURED')
        
        # scrapePrice
            try:
                priceElement   = productSoup.find('h3', class_='d-lg-none')
                priceElement = (priceElement.find('small'))
                price = (priceElement).text
                price = price.split('Sold for: $')[1]
                price = Decimal(sub(r'[^\d.]', '', price))

                print (f'PRICE : {price}')
                print ('SUCCESS'.ljust(100,'.')+'PRICE CAPTURED')
            except:
                price = 'NULL'
                print ('FAILURE'.ljust(100,'.')+'PRICE NOT CAPTURED')

        # scrapeImage
            try:
                imageThumbElement    = productSoup.find('p')
                imageThumb           = imageThumbElement.find('img')['src']
                print (f'THUMBNAIL : {imageThumb}')                
                print ('SUCCESS'.ljust(100,'.')+'IMAGES CAPTURED')
            except:
                imageThumb = 'NULL'
                print ('FAILURE'.ljust(100,'.')+'IMAGE NOT CAPTURED')

        # scrapeInvStatus
            inventoryStatus = 'SOLD'
            unavailableSince = date.today()

        # return info back to main()
            return ([title,desc,price,imageThumb,inventoryStatus,unavailableSince])



def main():

    hostName = 'localhost'
    dataBase = 'Militaria Products'
    userName = 'postgres'
    pwd      = 'poop'
    portId   = 5432

    dataManager      = PostgreSQLProcessor(hostName, dataBase,userName,pwd,portId)
    webScrapeManager = StewartsArchiveScraper(dataManager)

    currentRow = 0
    while True:
        url = f'https://stewartsmilitaryantiques.com/search_archives.php?row={currentRow}&search_for='
        currentRow += 50
        print(f'URL : {url}')
        soup = webScrapeManager.readProductPage(url)

        #Iterate through every item on product page
        productLinks = soup.find_all('div', class_='p-2 my-flex-item')
        urlCount = 0
        consecutiveMatches = 0
        for product in productLinks :
            #if consecutiveMatches == 100:
             #   print (f'{consecutiveMatches} MATCHES MET'.ljust(100,'.')+'WAITING 5 MINUTES')
              #  time.sleep(300)
               # break
            urlCount += 1
            print(f'URL COUNT : {urlCount}'.center(150,'-'))
            productSoup,productUrl = webScrapeManager.scrapePage(product)
            ([title,desc,price,imageThumb,inventoryStatus,unavailableSince]) = webScrapeManager.scrapeData(productSoup)
            productID = webScrapeManager.productIDGenerator()

            #IF ITEM IN LIST, UPDATE IT
            searchQuery = f"SELECT product_thumbnail FROM products WHERE product_thumbnail LIKE '{imageThumb}'"
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
                appendQuery = f'''INSERT INTO products (url, product_id, title, description, price, product_thumbnail, status,data_enter_date,sold_date,product_origin) VALUES ('{productUrl}','{productID}', '{title}', '{desc}', {price}, '{imageThumb}', '{inventoryStatus}','{todayDate}','{todayDate}','STEWARTS MILITARIA')'''
                dataManager.sqlExecute(appendQuery)
            print (f"""                   
--------------------------------------------
Captured File       : {productID}
Product Name        : {title}
Product Description : {desc}
Sold For Price      : ${price}
Image ThumbNail     : {imageThumb}
Inventory Status    : {inventoryStatus}
Unavailable Since   : {unavailableSince}
--------------------------------------------
""")








if __name__ == "__main__":
    main()
