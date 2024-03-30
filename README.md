# stew_mil
Keeping a database of all the products from Stewarts Militaria.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Docker and Docker Compose installed on your system. You can find instructions for installing Docker [here](https://docs.docker.com/get-docker/) and Docker Compose [here](https://docs.docker.com/compose/install/).
- Basic knowledge of Docker and command-line tools.


## Running the Application

To run the application, follow these steps:

1. **Build and start the containers:**

   This command will build the Docker images and start the containers as defined in your `docker-compose.yml` file.

    ```bash
    docker-compose up --build <scraper name>
    ```
    an example of this would be the below command, running your original main stew_mil_scraper:
    ```bash
    docker-compose up --build basic
    ```
    or you could search new items or the archive
    ```bash
    docker-compose up --build new
    docker-compose up --build archive
    ```

   Add a `-d` flag to run the containers in the background:

    ```bash
    docker-compose up --build -d
    ```

3. **Viewing Logs:**

   You should see your scraper running in the terminal with your print statements.
   If your application is running in the background, you can view the logs using:

    ```bash
    docker-compose logs -f
    ```

   The `-f` flag will follow the log output.

## Viewing the Database

Explain how to connect to the PostgreSQL database using `psql` or a GUI tool like pgAdmin. For command-line access:

```bash
docker-compose exec db psql -U postgres -d stew_mil_db
Replace stew_mil_db with the actual name of your database.
```

## Stopping the Application
To stop and remove the containers, networks, and volumes created by docker-compose up, run:
    
    ```bash
    docker-compose down -v
    ```
This command ensures a clean shutdown and cleanup of your application's Docker environment. It will also remove the database so remove the -v tag if you want to keep the database.
