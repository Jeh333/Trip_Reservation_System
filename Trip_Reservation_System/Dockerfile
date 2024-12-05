FROM python:3.10-slim

# Set up working directory
WORKDIR /app

#Copy the contents of the current directory in the container to the /app diectory
COPY . /app

#Upgrade pip 
RUN pip install --upgrade pip

#Install any needed packages 
RUN pip install --no-cache-dir -r requirements.txt

#set the default commandsto run when starting the container
CMD ["python3", "main.py"]