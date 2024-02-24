FROM python:3.9

ENV PYTHONUNBUFFERED 1
ENV C_FORCE_ROOT true
RUN mkdir /rango_bot
COPY ./requirements.txt /rango_bot
RUN pip install --upgrade pip
RUN apt-get update
RUN pip install -r /rango_bot/requirements.txt
WORKDIR /rango_bot
COPY ./src /rango_bot
