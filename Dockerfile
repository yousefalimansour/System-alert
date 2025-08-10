FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y build-essential libpq-dev

COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip && pip install -r /code/requirements.txt

COPY . /code

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
