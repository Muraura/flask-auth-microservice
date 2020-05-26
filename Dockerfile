FROM python:3.5.2-slim

RUN apt-get update && apt-get install -y python3-dev libmysqlclient-dev build-essential libssl-dev libffi-dev libpq-dev gcc

RUN mkdir -p /amura_service
WORKDIR /amura_service

ADD . /amura_service/
RUN pip install -r requirements.txt --cache-dir /pip-cache

RUN echo "Africa/Nairobi" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata

ENTRYPOINT ["python", "app/run.py"]
EXPOSE 9000