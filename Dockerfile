# syntax=docker/dockerfile:1
# https://docs.docker.com/samples/django/
FROM python:3.8
WORKDIR /code
RUN apt-get update \
    && apt-get -y install libpq-dev gcc build-essential wget unzip pip
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get -y install google-chrome-stable
RUN wget -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/115.0.5790.170/linux64/chromedriver-linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver-linux64/chromedriver -d /usr/local/bin/
COPY requirements.txt /code/
COPY docker-entrypoint.sh /code/
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
COPY . /code/