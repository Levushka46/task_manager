FROM python:3.8-bullseye

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # for PostgreSQL
  && apt-get install -y libpq-dev libssl-dev \
  # netcat is used to wait for PostgreSQL to be available
  && apt-get install -y netcat

  
# Requirements are installed here to ensure they will be cached.
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY . /app

RUN chmod +x /app/start.sh
RUN chmod +x /app/start-celery-worker.sh

WORKDIR /app

#ENTRYPOINT ["/app/start.sh"]