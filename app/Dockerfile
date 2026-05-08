FROM python:latest

WORKDIR /app

RUN pip install flask mysql-connector-python werkzeug

# RUN export MYSQL_HOST=localhost && export MYSQL_USER=root && export MYSQL_PASSWORD=password && MYSQL_DATABASE=cadetcoin

COPY app/main.py /app/main.py

CMD ["python", "main.py"]
