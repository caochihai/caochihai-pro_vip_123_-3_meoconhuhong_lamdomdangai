FROM python:3.11-slim

# Cài các gói cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/wkentaro/gdown.git
EXPOSE 5000
CMD ["python", "main.py"]