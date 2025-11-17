#使用官方python3.10镜像
FROM python:3.10-slim

#设置工作目录
WORKDIR /app

#复制依赖列表文件
COPY requirements.txt .

#安装所有依赖
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

#复制大脑的所有代码到容器里
COPY . .

#容器启动时要运行的命令
CMD ["python","bot.py"]