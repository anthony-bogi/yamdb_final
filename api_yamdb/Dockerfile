FROM python:3.7-slim

RUN mkdir /app

COPY . /app

RUN pip install -r /app/api_yamdb/requirements.txt --no-cache-dir

WORKDIR /app

CMD ["gunicorn", "api_yamdb.wsgi:application", "--bind", "0:8000" ]
