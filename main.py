# ALLSTEWARTSITEMS18MAR24

import os, sys, requests, re, time        # core python modules, don't need to be in the requirements.txt
from datetime import date     # core python packages from the datetime module. not needed in requirements.txt
import psycopg2                     # postgresql database package, imported via psycopg2-binary in requirements.txt
from bs4 import BeautifulSoup         # scraping tool package, from requirements.txt

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
class StewartsNewItemsScraper:
    def __init__(self,databaseManager):
         self.databaseManager = databaseManager

    def productIDGenerator(self):
        lastProductID = self.databaseManager.sqlFetch('''SELECT MAX(product_id) FROM products''')
        if lastProductID[0][0] is not None:
            productID = int(lastProductID[0][0]) + 1
        else:
            productID = 1  # Start from 1 if the table is empty
        print(f'ASSIGNING ID'.ljust(100, '.') + f'{productID}')
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
            titleElement   = productSoup.find('h3', class_='d-lg-none')
            title          = re.sub('<[^<]+?>', '', str(titleElement))
            title          = title.split('\n')[0]
            print ('SUCCESS'.ljust(100,'.')+'TITLE CAPTURED')
        # scrapeDesc
            descElement = productSoup.find('p')
            desc        = re.sub('<[^<]+?>', '', str(descElement))
            desc        = desc.strip()
            desc        = desc.replace("'","*")
            print ('SUCCESS'.ljust(100,'.')+'DESC CAPTURED')
        # scrapePrice
            priceElement   = productSoup.find('div', id='cart_readout')
            price = (priceElement.find('b')).text
            price = price.replace(',','')            
            price = float(price[1:])
            print ('SUCCESS'.ljust(100,'.')+'PRICE CAPTURED')
        # scrapeImage
            imageThumbElement    = productSoup.find('div', class_="container")
            imageThumb           = imageThumbElement.find('img')['src']
            imageDetailedElement = productSoup.find('div', class_='d-flex flex-row flex-wrap justify-content-around my-flex-container')
            images = imageDetailedElement.find_all('img','src')
            imageList = []
            for image in images:
                image = image.img['src']
                imageList += [image]
            imageList = ' '.join(imageList)
            print ('SUCCESS'.ljust(100,'.')+'IMAGES CAPTURED')
        # scrapeInvStatus
            inventoryStatus = 'AVAILABLE'
            unavailableSince = 'N/A'

        # return info back to main()
            return ([title,desc,price,imageThumb,imageList,inventoryStatus,unavailableSince])


# SECOND PHASE : GET THE SQL PORTION READY
class PostgreSQLProcessor:
    # set max retry attempts to connect to 5, with a 3 second delay, or wait time to allow the computer to connect
    def __init__(self,hostName, dataBase,userName,pwd,portId, max_retries=5, delay=3):
        self.hostName = hostName
        self.dataBase = dataBase
        self.userName = userName
        self.pwd      = pwd
        self.portId   = portId
        for attempt in range(max_retries):
            # try/except block to catch connection issues and retry the connection if there is one, logging the error
            # this is an asynchronous operation, so we need to wait for the connection to be established before moving forward

            try: 
                self.conn     = psycopg2.connect(
                        host = hostName,
                        dbname = dataBase,
                        user = userName,
                        password = pwd,
                        port = portId)
                self.cur      = self.conn.cursor()
                break
            except psycopg2.OperationalError as exception:
                if attempt < max_retries - 1:  # Avoid sleeping on the last attempt, just go for it
                    print(f"Connection attempt {attempt + 1} failed, retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print('connection failed. Error is below...')
                    raise exception  # Reraise the last exception


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


# MAIN EXECUTION

def main():

    hostName = 'db'
    dataBase = 'stew_mil_db'
    userName = 'postgres'
    pwd      = 'poop'
    portId   = 5432

    dataManager      = PostgreSQLProcessor(hostName, dataBase,userName,pwd,portId)
    webScrapeManager = StewartsNewItemsScraper(dataManager)

    currentRow = 0
    while True:
        url = f'https://stewartsmilitaryantiques.com/search_products.php?row={currentRow}&search_for=wwii+german'
        currentRow += 50
        print(f'URL : {url}')
        soup = webScrapeManager.readProductPage(url)

        #Iterate through every item on product page
        productLinks = soup.find_all('div', class_='p-2 my-flex-item')
        urlCount = 0
        for product in productLinks :
            urlCount += 1
            print(f'URL COUNT : {urlCount}'.center(100,'*'))
            productSoup,productUrl = webScrapeManager.scrapePage(product)
            ([title,desc,price,imageThumb,imageList,inventoryStatus,unavailableSince]) = webScrapeManager.scrapeData(productSoup)
            productID = webScrapeManager.productIDGenerator()

            #IF ITEM IN LIST, UPDATE IT
            searchQuery = f"SELECT url FROM products WHERE url LIKE '{productUrl}'"
            cellValue = dataManager.sqlFetch(searchQuery)
            match = [tup[0] for tup in cellValue]
            if productUrl in match:
                print (f'PRODUCT {title} ALREADY IN SYSTEM'.center(100,'*'))
                continue

            else:
            #IF ITEM NOT IN LIST, ADD IT
                todayDate = date.today()
                appendQuery = f'''INSERT INTO products (url, product_id, title, description, price, product_thumbnail, images, status,data_enter_date) VALUES ('{productUrl}','{productID}', '{title}', '{desc}', {price}, '{imageThumb}', '{imageList}', '{inventoryStatus}','{todayDate}')'''
                dataManager.sqlExecute(appendQuery)
            print (f"""                   
--------------------------------------------
Captured File       : {productID}
Product Name        : {title}
Product Description : {desc}
Sold For Price      : ${price}
Image ThumbNail     : {imageThumb}
Images              : {imageList}
Inventory Status    : {inventoryStatus}
Unavailable Since   : {unavailableSince}
--------------------------------------------
""")








if __name__ == "__main__":
    main()
