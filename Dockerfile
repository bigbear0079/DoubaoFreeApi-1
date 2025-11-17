# 使用 Playwright 官方镜像（已包含浏览器和所有依赖）
# 注意：镜像版本需要与 requirements.txt 中的 playwright 版本匹配
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p src/static src/templates

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "app.py"]
