FROM python:3.8-slim
RUN pip install kafka-python
WORKDIR /app
COPY search_producer.py ./
CMD ["python", "search_producer.py"]
