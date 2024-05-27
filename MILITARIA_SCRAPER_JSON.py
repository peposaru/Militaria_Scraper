# Making a more universal scraper which just takes a json library as input

import requests, re, os, psycopg2,json
from bs4 import BeautifulSoup
from datetime import date
from re import sub
from tqdm import tqdm
from time import sleep

class ProductScraper:
    def __init__(self,spreadSheetManager):
         self.spreadSheetManager = spreadSheetManager

    def readProductPage(self,url):
        headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"
}        
        response = requests.get(url,headers=headers)
        soup     = BeautifulSoup(response.content, 'html.parser')
        return soup
    
    def scrapePage(self,product):
        headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"
}     
        response    = requests.get(product,headers=headers)
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
                title  = title.replace('click image for larger view.','')
                title  = title.strip()
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
                description = description.replace('Description','')
                description = description.replace('Full image','')
                description = description.split('USD', 1)[0]
                description = description.strip()
            except:
                description = 'NULL'

        # Scrape Price
            try:
                if source == 'VIRTUAL_GRENADIER':
                    priceRegex  = r'\$(\d+(?:,\d+)*)\b'
                    price       = eval(priceElement)
                    priceMatch1 = re.search(priceRegex,price)
                    price       = priceMatch1.group(1).replace(",", "")
                    price       = price.replace('$','')
                    price       = int(price)

                else:
                    priceRegex  = r"[\d.,]+"
                    price       = eval(priceElement)
                    priceMatch1 = re.search(priceRegex,price)
                    price       = priceMatch1.group()
                    price       = price.replace(',','.')
                    periodRegex = r'\.(?=.*\.)'
                    price       = re.sub(periodRegex,'',price)
                    if source == 'RUPTURED_DUCK':
                        price = price.replace('.','')

            except Exception as err:
                    print (err)
                    price = 0

        # Scrape Availability
            available = eval(availableElement)

        # Return all values
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

class JsonManager:        
    def jsonSelectors(self,militariaSite):
        base_url         = militariaSite['base_url']
        source           = militariaSite['source']
        pageIncrement    = militariaSite['page_increment']
        currency         = militariaSite['currency']
        products         = militariaSite['products']
        productUrlElement= militariaSite['product_url_element']
        titleElement     = militariaSite['title_element']
        descElement      = militariaSite['desc_element']
        priceElement     = militariaSite['price_element']
        availableElement = militariaSite['available_element']
        conflict         = militariaSite['conflict_element']
        nation           = militariaSite['nation_element']
        item_type        = militariaSite['item_type_element']
        productsPageUrl  = militariaSite['productsPageUrl']
        grade            = militariaSite['grade_element']

        return conflict,nation,item_type,grade,source,pageIncrement,currency,products,productUrlElement,titleElement,descElement,priceElement,availableElement,productsPageUrl,base_url

class MainPrinting:
    def newInstance(self,source,productsPage,runCycle,productsProcessed):
            print(f"""
--------------------------------------------
            NEW INSTANCE
MILITARIA SITE      : {source}
PRODUCTS URL        : {productsPage}
CYCLES RUN          : {runCycle}
PRODUCTS PROCESSED  : {productsProcessed}
--------------------------------------------""")
    def terminating(self,source,consecutiveMatches,runCycle,productsProcessed):
        print (f"""
--------------------------------------------
MILITARIA SITE      : {source}
CONSECUTIVE MATCHES : {consecutiveMatches}
CYCLES RUN          : {runCycle}
PRODUCTS PROCESSED  : {productsProcessed}
        TERMINATING INSTANCE
--------------------------------------------""")
    def sysUpdate(self,page,urlCount,consecutiveMatches,productUrl):
        print(f"""
--------------------------------------------
PRODUCT IN SYSTEM   : UPDATED
CURRENT PAGE        : {page}
PRODUCTS PROCESSED  : {urlCount} 
CONSECUTIVE MATCHES : {consecutiveMatches}
URL                 : {productUrl}
--------------------------------------------""")  
    def noUpdate(self,page,urlCount,consecutiveMatches,productUrl):
        print(f"""
--------------------------------------------
PRODUCT IN SYSTEM   : NO UPDATES
CURRENT PAGE        : {page}
PRODUCTS PROCESSED  : {urlCount} 
CONSECUTIVE MATCHES : {consecutiveMatches}
URL                 : {productUrl}
--------------------------------------------""")
    def newProduct(self,page,urlCount,title,productUrl,description,price,available,todayDate):
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
--------------------------------------------""")
    def standby(self):
        print("""
--------------------------------------------
    SITE SCRAPE PROCESS COMPLETE
        STAND BY FOR 5 MINUTES
--------------------------------------------
""")

def main():
    print ('INITIALIZING. PLEASE WAIT...')
    # Location where credentials are located
    infoLocation = r'C:\Users\keena\Desktop\Militaria Scrape Program POSTGRESQL'
    pgAdminCred  = 'pgadminCredentials.json'
    selectorJson = 'MILITARIA_SELECTORS.json'
    os.chdir(infoLocation)

    # pgAdmin 4 Credentials
    with open (pgAdminCred,'r') as credFile:
        jsonData = json.load(credFile)
        hostName = jsonData['hostName'] 
        dataBase = jsonData['dataBase']
        userName = jsonData['userName']
        pwd      = jsonData['pwd']
        portId   = jsonData['portId']

    # Postgresql - Web Scraping / Beautiful Soup - Json Manager
    dataManager      = PostgreSQLProcessor(hostName, dataBase,userName,pwd,portId)
    webScrapeManager = ProductScraper(dataManager)
    jsonManager      = JsonManager()
    prints           = MainPrinting()

    # Setting up counts
    runCycle          = 0
    productsProcessed = 0
    
    # Set how many in a row you want to match
    targetMatch = 10

    # Opening the JSON file containing website specific selectors
    with open(selectorJson,'r') as userFile:
        jsonData = json.load(userFile)


    # Main Loop
    while True:

        # Iterating over each site in the JSON file and grabbing their respective selectors.
        for militariaSite in jsonData:
            conflict,nation,item_type,grade,source,pageIncrement,currency,products,productUrlElement,titleElement,descElement,priceElement,availableElement,productsPageUrl,base_url = jsonManager.jsonSelectors(militariaSite)
            
            # Counters for current site
            urlCount           = 0
            consecutiveMatches = 0
            page               = 0

            # Iterating over all the products on a the products list.
            while consecutiveMatches != targetMatch:
                productsPage = base_url + productsPageUrl.format(page=page)
                print(productsPage)
                soup             = webScrapeManager.readProductPage(productsPage)
                prints.newInstance(source,productsPage,runCycle,productsProcessed)
                for product in eval(products) :
                    if len(product) == 0:
                        break
                    urlCount += 1
                    productsProcessed += 1

                    # If x amount of matches are met, end this run for this site
                    if consecutiveMatches == targetMatch:

                        # Notifying user of cycle termination
                        prints.terminating(source,consecutiveMatches,runCycle,productsProcessed)
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

                        soldDateExists = f"""SELECT date_sold FROM militaria WHERE url LIKE '{productUrl}'"""

                        # If the product url is in the database and the item has been sold
                        if available == False:
                            cellValue = dataManager.sqlFetch(soldDateExists)

                            match = [tup[0] for tup in cellValue]
                            if match != False:
                                print('UPDATING SOLD DATE')
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

                                prints.sysUpdate(page,urlCount,consecutiveMatches,productUrl)
                                continue
                        else:
                            prints.noUpdate(page,urlCount,consecutiveMatches,productUrl)

                    if productUrl not in match:
                        consecutiveMatches = 0
                        appendQuery = f'''INSERT INTO militaria (url, title, description, price, available,date,site,currency,conflict,nation,item_type) VALUES ('{productUrl}','{title}','{description}',{price},{available},'{todayDate}','{source}','{currency}','{conflict}','{nation}','{item_type}')'''
                        # COMMENT THIS APPENDQUERY LINE OUT IF YOU WANT TO TEST BEFORE WRITING TO DATABASE 
                        dataManager.sqlExecute(appendQuery)
                        prints.newProduct(page,urlCount,title,productUrl,description,price,available,todayDate)

                page += int(pageIncrement)

        runCycle += 1
        prints.standby()

        for i in tqdm(range(100)):
            sleep(5)





if __name__ == "__main__":
    main()
