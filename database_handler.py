import psycopg2
import time

# break your understanding of this class, which is used elsewhere, into he init and it's other 4 defs. These are connect, sql_execute, sql_fetch, and sql_close.

# the init is telling the rest of the file what it is retrieving from main.py and defining the cursor. These necessary variables are used in all other defs

# This is all meant to define how to interact with a PostgreSQL database. The defined interactions of execute and fetch are what is used elsewhere in other scrapers repetivtively, just with different information being processed in the "query" parameters. 

# the connect and close are used to open and close the connection to the database. These are used only once, in the main.py file in particular.
class PostgreSQLProcessor:
    def __init__(self, host_name, database_name, user_name, password, port_id):
        self.host_name = host_name
        self.database_name = database_name
        self.user_name = user_name
        self.password = password
        self.port_id = port_id
        self.connection = None  # Initializes the connection attribute to None
        self.cursor = None  # Initializes the cursor attribute to None. A cursor is like a virtual 'pointer' for iterating over query results.
        self.connect()

    # I added this function to retry the connection if it fails. That way we can handle network issues or other connection problems. Feel free to ignore it
    def connect_with_retry(self, max_attempts=5, sleep_interval=5):
        """Attempt to connect to the database with retries."""
        for attempt in range(max_attempts):
            try:
                self.connect()  # Attempt to connect to the database
                print("Successfully connected to the database.")
                return  # Exit the function if connection is successful
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Waiting for {sleep_interval} seconds before retrying...")
                time.sleep(sleep_interval)
        raise Exception("Could not connect to the database after several attempts.")

    def connect(self):
        """Attempt to connect to the PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=self.host_name,
                dbname=self.database_name,
                user=self.user_name,
                password=self.password,
                port=self.port_id
            )
            # After connecting to the database, we create a cursor from the connection. Think of the cursor as a tool to interact with the database:
            # It allows us to execute SQL queries and retrieve results.
            self.cursor = self.connection.cursor()
            print("Database connection was successful")
        except Exception as e:
            print(f"An error occurred when connecting to the database: {e}")

    def sql_execute(self, query):
        """Execute an SQL query without returning any results."""
        try:
            # The cursor executes the SQL command provided to it.
            self.cursor.execute(query)
            # After executing a command that modifies the database, we must commit the changes.
            self.connection.commit()
        except Exception as e:
            print(f"An error occurred during query execution: {e}")
            self.connection.rollback()  # If an error occurs, rollback any changes made during the command.

    def sql_fetch(self, query):
        """Execute an SQL query and return the results."""
        try:
            # Here, we use the cursor to execute a query that we expect to return results.
            self.cursor.execute(query)
            # fetchall() collects all the rows returned by the query. The cursor iterates over the result set internally to gather these.
            return self.cursor.fetchall()
        except Exception as e:
            print(f"An error occurred fetching data: {e}")
            return None

    def sql_close(self):
        """Safely close the cursor and database connection."""
        if self.cursor:
            # Close the cursor when done to free database resources. Think of closing a file after reading it.
            self.cursor.close()
        if self.connection:
            # Similarly, close the connection to the database when all operations are complete.
            self.connection.close()
            print("Database connection closed")
