# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the Docker image
WORKDIR /app

# Copy the requirements.txt file into the image to install Python dependencies
COPY requirements.txt .


# Install system dependencies required for psycopg2 compilation
RUN apt-get update && apt-get install -y gcc libpq-dev python3-dev

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code
COPY . .

# Command to run the application
CMD ["python", "./main.py"]


# the running python from the dockerfile instead of locally via the python terminal will execute the above commands. It will install python, all the dependencies in requirements.txt, and run the main.py file. This allows you to run the project from here on any machine, or more importantly, on a server online if you ever wanted to deploy it in the future.

# to build the dockerfile, you can run the following command in the terminal:
# docker build -t app .
# then to run the dockerfile, you can run the following command in the terminal:
# docker run app

# building should take a while the first time