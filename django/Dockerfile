FROM python:3.7.2
WORKDIR /code
ADD requirements.txt /code
RUN apt-get update
RUN pip install -r requirements.txt
RUN apt-get install -y mysql-client
