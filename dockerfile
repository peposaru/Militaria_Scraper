# This Docker Compose file is used to define and manage a multi-container application using Docker. Docker allows you to automate the deployment, scaling, and management of apps like yours using containers such as the one defined here. A container is a lightweight, standalone, executable package of software that includes everything needed to run an application, including the code, runtime, libraries, and dependencies.This container will be running python 3.9 within it, allowing you to run docker-compose up to start the application instead of python directly, allowing you to run it anywhere, on any computer or server.


# use this version of python to run the project
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the command to start your application
CMD ["/wait-for-it.sh", "db:5432", "--", "python", "./main.py"]
