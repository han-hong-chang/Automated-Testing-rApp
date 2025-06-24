# 使用官方 Python slim 版本作為基底映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app
RUN apt-get update && apt-get install -y curl
# 安裝 flask 和 requests 套件
RUN pip install --no-cache-dir flask requests
RUN pip install --no-cache-dir pandas requests ncclient influxdb influxdb-client kafka-python


# 複製所有程式碼到容器中
COPY src/ .

# 對外暴露 8080 埠口（Flask 預設）
EXPOSE 8080

# 以非緩衝模式執行，方便即時輸出日誌
CMD ["python", "-u", "main.py"]

