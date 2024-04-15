# Militaria DB

## Setup and Running the MILITARIA_SCRAPER_JSON.py
Run the following commands to setup the project:
```bash
docker-compose build
```
That will install everything you need to run the project by pip-installing everything from the requirements.txt to a localized environment. then you can run:
```bash
docker-compose up
```
to run the project. This Will show all logs.
If you want to run it in detached mode, or without all the logs crowding your screen, run:
```bash
docker-compose up -d
```
After doing this, there should be three services running: the scraper, the database (db), and pgadmin. 

## Shutting down the project
To shut down the project, run:
```bash
docker-compose down
```
Because your scraper runs on a continuous loop, you need to exit the current process first (ctrl+C) and then issue the `docker-compose down` command. After that, if by any chance you have a bad container you need to get rid of to start the project again, you can run 
```bash
docker volume prune
```
after, and only after, you issued the `docker-compose down` command. This will remove all the volumes that were created by the project, and you can start fresh. Then you can make your changes, type `docker-compose up -d` and repeat.

</br> 

## DB information
the new db folder is a utility for docker to store the database information. It is not necessary to run the project, but it is necessary to run the database. This db folder, outside of containing the database information, also contains the create-table.sql file, which is used to create the database table 'militaria' if it doesn't exist. That's important while testing locally because often when you shut down a service, the table, and it's database disappears. That table is what your scraper is writing data to.

## pgAdmin
pgAdmin is a web-based interface for managing your database. It is accessible at `http://localhost:5050`. The default username is `admin@admin.com` and the default password is `root`. You can change these in the docker-compose.yml file. You can also change the port that pgAdmin is accessible on in the docker-compose.yml file, if you really want to.

</br>

## Adding a new server to pgAdmin
To add your server, first run your `docker-compose up` command, and then go to `http://localhost:5050`. 

In a new Terminal, run `docker inspect db_container`. Look for the `IPAddress` field, about 5 lines from the bottom. This is the IP address of your database connection.

Log in with the default credentials, and then click on `Add New Server`. In the `General` tab, give your server whatever name. In the `Connection` tab, fill in the following fields:
- Host name/address: The IP address you found earlier (something like 172.22.0.3)
- Port: 5432
- Maintenance database: db
- Username: postgres
- Password: poop

On pressing save, you should see a little elephant called "db" on the left-hand side under "servers", click and navigate through "db" -> "Databases" -> "db" -> "Schemas" -> "public" -> "Tables" -> "militaria". Right click "militaria" and select "view/edit data" -> "all Rows". That is  This is a visual graph of your data table on the lower part of your screen!You can also make queries on the upper half! Keep selecting the "view/edit data" option to see the data in the table refreshed.

## Moving forward
Aside from the obvious cleaning of data and feeding it to a machine learning model, we need to make your db persistant. We made this here as a great example of a developer testing environment, but when you test, it is on another branch. When the "main" branch is run, you want 