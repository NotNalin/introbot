FROM python:3.10-slim-buster
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN mkdir /var/log/introbot
RUN apt-get update -y && apt-get install -y default-libmysqlclient-dev python-dev git build-essential
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT sh entrypoint.sh
