FROM python:latest

WORKDIR /app

RUN pip install flask pymysql cryptography

COPY app/main.py /app/main.py

COPY data /app/data

CMD ["python", "main.py"]
