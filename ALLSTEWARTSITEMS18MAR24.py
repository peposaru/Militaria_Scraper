# ALLSTEWARTSITEMS18MAR24

import requests, re, os, gspread, time, psycopg2
from bs4 import BeautifulSoup
from datetime import date

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

# A
class StewartsNewItemsScraper:
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


# MAIN EXECUTION

def main():

    hostName = 'localhost'
    dataBase = 'Militaria Products'
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
