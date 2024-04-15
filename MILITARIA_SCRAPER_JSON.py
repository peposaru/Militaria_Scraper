# Making a more universal scraper which just takes a json library as input

import requests, re, os, time, psycopg2,json
from bs4 import BeautifulSoup
from datetime import date
from decimal import Decimal
from re import sub
from currency_converter import CurrencyConverter


class ProductScraper:
    def __init__(self,spreadSheetManager):
         self.spreadSheetManager = spreadSheetManager

    def readProductPage(self,url):
        response = requests.get(url)
        soup     = BeautifulSoup(response.content, 'html.parser')
        return soup
    
    def scrapePage(self,product):
        response    = requests.get(product)
        productSoup = BeautifulSoup(response.content, 'html.parser')
        return productSoup
    
    def scrapeData(self,productSoup,titleElement,descElement,priceElement,availableElement,currency,source):
            
        # Scrape Title
            try:
                title  = eval(titleElement)
                title  = title.strip()
                title  = title.replace("'","*")
                title  = title.replace('"',"*")
                title  = title.replace('‘','*')
                title  = title.replace('’','*')
            except:
                title = 'NULL'

        # Scrape Description
            try:
                description = eval(descElement)
                description = description.replace("'","*")
                description = description.replace('"',"*")
                description = description.replace('‘','*')
                description = description.replace('’','*')
                description = description.replace('Description','')
                description = description.strip()
            except:
                description = 'NULL'

        # Scrape Price
            c = CurrencyConverter()
            try:
                priceRegex  = r"[\d.,]+"
                price       = eval(priceElement)
                priceMatch1 = re.search(priceRegex,price)
                price       = priceMatch1.group()
                price       = price.replace(',','.')
                periodRegex = r'\.(?=.*\.)'
                price       = re.sub(periodRegex,'',price)
                if source == 'RUPTURED_DUCK':
                    price = price.replace('.','')
                if currency == 'euros':
                    price = c.convert(price,'EUR','USD')
                elif currency == 'dollars':
                    pass
                else:
                    print('CURRENCY / PRICE ISSUE')
                    price = c.convert(price,'EUR','USD')

            except Exception as err:
                print (err)
                price = 0

        # Scrape Availability
            available = eval(availableElement)

        # Return all values
            print (f'TITLE: {title}\nDESCRIPTION: {description}\nPRICE: {price}\nAVILABLE: {available}')
            return ([title,description,price,available])


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

    


def main():
    while True:
        # see the docker-compose.yml for where i'm storing the info
        # soon, we need to create a .env file to store this info securely. Fine for now
        hostName = os.getenv('DATABASE_HOST', 'localhost')
        dataBase = os.getenv('DATABASE_NAME', 'Militaria_Products_DB') # this format means "grab the database_name, and if it doesn't exist, make it Militaria_Products_DB"
        userName = os.getenv('DATABASE_USER', 'postgres')
        pwd      = os.getenv('DATABASE_PASSWORD', 'poop')
        portId   = os.getenv('DATABASE_PORT', 5432)

        # Handling different data input / output
        dataManager      = PostgreSQLProcessor(hostName, dataBase,userName,pwd,portId)
        webScrapeManager = ProductScraper(dataManager)

        runCycle          = 0
        productsProcessed = 0

        while True: # this will make the scraper keep running until you manually stop it. With docker, you can use "docker-compose stop scraper" to stop it

            # Opening the JSON file containing website specific selectors
            with open('MILITARIA_SELECTORS.json','r') as userFile:
                jsonData = json.load(userFile)

            # Iterating over each site in the JSON file and grabbing their respective selectors.
            for militariaSite in jsonData:
                
                urlCount           = 0
                consecutiveMatches = 0
                page               = 0

                source           = militariaSite['source']
                url              = f"{militariaSite['base_url'].replace('{page}', str(page))}"
                pageIncrement    = militariaSite['page_increment']
                currency         = militariaSite['currency']
                products         = militariaSite['products_url_list']
                productUrlElement= militariaSite['product_url_element']

                titleElement     = militariaSite['title_element']
                descElement      = militariaSite['desc_element']
                priceElement     = militariaSite['price_element']
                availableElement = militariaSite['available_element']

                soup             = webScrapeManager.readProductPage(url)

                print(f"""
--------------------------------------------
                NEW INSTANCE
MILITARIA SITE      : {source}
PRODUCTS URL        : {url}
CYCLES RUN          : {runCycle}
PRODUCTS PROCESSED  : {productsProcessed}
--------------------------------------------
                """)

                # Iterating over all the products on a the products list.
                for product in eval(products) :
                    urlCount += 1
                    productsProcessed += 1

                    # If x amount of matches are met, end this run for this site
                    if consecutiveMatches == 25:
                        print (f"""
--------------------------------------------
MILITARIA SITE      : {source}
CONSECUTIVE MATCHES : {consecutiveMatches}
CYCLES RUN          : {runCycle}
PRODUCTS PROCESSED  : {productsProcessed}
           TERMINATING INSTANCE
--------------------------------------------
                        """)
                        break

                    productUrl  = eval(productUrlElement)
                    productSoup = webScrapeManager.scrapePage(productUrl)

                    ([title,description,price,available]) = webScrapeManager.scrapeData(productSoup,titleElement,descElement,priceElement,availableElement,currency,source)
                    todayDate = date.today()

                #IF ITEM IN LIST, UPDATE IT
                    searchQuery = f"SELECT url FROM militaria WHERE url LIKE '{productUrl}'"
                    cellValue = dataManager.sqlFetch(searchQuery)
                    match = [tup[0] for tup in cellValue]

                # If the product url is in the database
                    if productUrl in match:
                        consecutiveMatches += 1
                    # If the product url is in the database and the item has been sold
                        if available == False:
                            updateStatus = f''' UPDATE militaria
                                                SET available = False
                                                WHERE url = '{productUrl}';'''
                            updateSoldDate = f'''  UPDATE militaria
                                                SET date_sold = '{todayDate}'
                                                WHERE url = '{productUrl}';'''
                            # COMMENT THIS APPENDQUERY LINE OUT IF YOU WANT TO TEST BEFORE WRITING TO DATABASE 
                            dataManager.sqlExecute(updateStatus)
                            # COMMENT THIS APPENDQUERY LINE OUT IF YOU WANT TO TEST BEFORE WRITING TO DATABASE 
                            dataManager.sqlExecute(updateSoldDate)

                            print(f"""
    --------------------------------------------
    PRODUCT IN SYSTEM   : UPDATED
    CURRENT PAGE        : {page}
    PRODUCTS PROCESSED  : {urlCount} 
    CONSECUTIVE MATCHES : {consecutiveMatches}
    URL                 : {productUrl}
    --------------------------------------------
    """)
                            continue
                        else:
                            print(f"""
    --------------------------------------------
    PRODUCT IN SYSTEM   : NO UPDATES
    CURRENT PAGE        : {page}
    PRODUCTS PROCESSED  : {urlCount} 
    CONSECUTIVE MATCHES : {consecutiveMatches}
    URL                 : {productUrl}
    --------------------------------------------
    """)
                    if productUrl not in match:
                        consecutiveMatches = 0
                        appendQuery = f'''INSERT INTO militaria (url, title, description, price, available,date,site) VALUES ('{productUrl}','{title}','{description}',{price},{available},'{todayDate}','{source}')'''
                        # COMMENT THIS APPENDQUERY LINE OUT IF YOU WANT TO TEST BEFORE WRITING TO DATABASE 
                        dataManager.sqlExecute(appendQuery)
                        print (f"""  
    --------------------------------------------
    NEW PRODUCT                                              
    CURRENT PAGE        : {page}
    PRODUCTS PROCESSED  : {urlCount}
    TITLE               : {title} 
    URL                 : {productUrl}        
    DESCRIPTION         : {description}
    PRICE               : {price}
    AVAILABLE           : {available}
    PROCESS DATE        : {todayDate}
    --------------------------------------------
        """)

                page += int(pageIncrement)
            runCycle += 1
            print("""
--------------------------------------------
        SITE SCRAPE PROCESS COMPLETE
           STAND BY FOR 5 MINUTES
--------------------------------------------
""")
            time.sleep(300)






if __name__ == "__main__":
    main()
