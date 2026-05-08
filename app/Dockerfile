FROM python:latest

WORKDIR /app

RUN pip install flask mysql-connector-python werkzeug

# RUN export MYSQL_HOST=localhost && export MYSQL_USER=root && export MYSQL_PASSWORD=password && MYSQL_DATABASE=cadetcoin

# Hash of password "demo"
ENV LOGIN_USERNAME="cadet.demo"
ENV LOGIN_PASSWORD_HASH="scrypt:32768:8:1\$bBb3hE4wRW2DzHTW\$c4a1a4f3fe6a5c39500b86c27e87e46cfd2995c25d77121a9f8ede36c84adf0cfedd62f2dcc5c6087cf42ad83a026a32a02688a9883b0e9939d11f0a25f577eb"

# SHHHH
ENV secret_key="de3e72ce62445e9a58d0c0bd4553395a50813dc449450903876a6a4eb2d90821"

COPY app/main.py /app/main.py

CMD ["python", "main.py"]
