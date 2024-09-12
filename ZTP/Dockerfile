FROM python:3.9-slim

RUN mkdir -p /app/flask_app
WORKDIR /app/flask_app

COPY . .
RUN pip3 install -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

EXPOSE 80

CMD ["python", "app.py"]
