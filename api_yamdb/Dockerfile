FROM python:3.7-slim

COPY . .

RUN pip install -r ./requirements.txt --no-cache-dir

WORKDIR /app

CMD ["gunicorn", "api_yamdb.wsgi:application", "--bind", "0:8000" ]
