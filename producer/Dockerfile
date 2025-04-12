FROM python:3.8-slim
RUN pip install kafka-python pandas
WORKDIR /app
COPY producer.py ./
CMD ["python", "producer.py"]
