FROM python:3.9

ENV PYTHONUNBUFFERED 1
ENV C_FORCE_ROOT true
RUN mkdir /RangoBotApplication
COPY ./requirements.txt /rango_bot
RUN pip install --upgrade pip
RUN apt-get update
RUN pip install -r /RangoBotApplication/requirements.txt
WORKDIR /RangoBotApplication
COPY ./RangoBotApplication /RangoBotApplication
