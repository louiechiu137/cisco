# 使用官方 Python 镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app/flask_app

# 更改 apt 的源到阿里云并安装必要的依赖项，包括 python3-pip
RUN sed -i 's|http://deb.debian.org/debian|http://mirrors.aliyun.com/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org/debian-security|http://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list && \
    apt-get clean && \
    apt-get update && \
    apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    python3-pip \
    && apt-get clean

# 更新 pip 到最新版本并使用阿里云镜像源
RUN python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

# 复制 requirements.txt 并安装依赖
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制应用代码
COPY http_dir/flask_app /app/flask_app/
COPY http_dir/flask_app/device_init_config.cfg /app/flask_app/device_init_config.cfg
COPY http_dir/flask_app/device_init_stack.json /app/flask_app/device_init_stack.json

# 暴露应用端口
EXPOSE 80

# 运行 Flask 应用
CMD ["python", "app.py"]