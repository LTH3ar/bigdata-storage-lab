FROM python:3.8-slim
RUN pip install pyspark==3.1.2 transformers torch kafka-python
WORKDIR /opt/app
COPY caption_embedding_job.py query_job.py ./
