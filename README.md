# bigdata-storage-lab

## 1. Description

- This is just a basic kafka - zookeeper - spark - hdfs stack for big data storage lab.
- The dataset use in this lab is flickr30k dataset from kaggle.
- The process is as follows:
  - Kafka: Producer reads the dataset and sends it to the kafka topic.
  - Zookeeper: Kafka uses zookeeper to manage the kafka brokers.
  - Spark: Spark reads the data from kafka topic and processes it.
  - HDFS: Spark writes the processed data to hdfs.
- The data is stored in hdfs in parquet format.

## 2. Requirements

- Docker
- Docker-compose
- Python

## 3. How to run

- Clone the repository:

    ```bash
    git clone https://github.com/LTH3ar/bigdata-storage-lab.git
    cd bigdata-storage-lab
    ```

- Build the docker images:

    ```bash
    docker build -f dockerfile.kafka -t kafka:lab .
    docker build -f dockerfile.spark -t spark:lab .

    ```

- Download the dataset:

    ```bash
    #!/bin/bash
    curl -L -o ~/Downloads/flickr-image-dataset.zip\
    https://www.kaggle.com/api/v1/datasets/download/hsankesara/flickr-image-dataset
    ```

- Extract the dataset and make sure the folder `flickr30k_images` and `results.csv` are in the same directory as the docker-compose.yml file.
- There are possible duplicated flickr30k folder in the dataset, make sure to remove the duplicated folder.

- Copy file to kafka and spark container:

    ```bash
    docker cp kafka_producer.py kafka:/kafka_producer.py
    docker cp spark_kafka_hdfs.py spark-master:/spark_kafka_hdfs.py
    docker cp t5_image_search.py t5-search:/t5_image_search.py

- Create kafka topic:

    ```bash
    docker exec -it kafka kafka-topics.sh --create --topic caption_topic \
  --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1
    docker exec -it kafka kafka-topics.sh --create --topic image_topic \
  --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1


    ```

- Run spark job first for listening to kafka topic:

    ```bash
    docker exec -it spark-master spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  /spark_kafka_hdfs.py

    ```

- Run kafka producer this will send the data to kafka topic:

    ```bash
    docker exec -it kafka python /kafka_producer.py
    ```
- Run the docker-compose:

    ```bash
    docker compose up -d
    ```
    
- Check the data in hdfs:

    ```bash
    docker exec -it namenode hdfs dfs -ls /raw_images
    ```
- Run image search
   - The t5-search service is preconfigured in docker-compose.yml and will automatically start once other services are up.

   - It consumes captions from the Kafka topic and performs semantic search with a user-defined query.

- Environment variables used (defined in .env):
    ```bash
    KAFKA_SERVER="kafka:9092"
    KAFKA_IMAGE_TOPIC="image_topic"
    KAFKA_CAPTION_TOPIC="caption_topic"
    QUERY="biển xanh"

    ```
- When the container starts, it automatically runs:
    ```bash
    python t5_search.py --query "$QUERY" --image-topic "$KAFKA_IMAGE_TOPIC" --caption-topic "$KAFKA_CAPTION_TOPIC" --kafka "$KAFKA_SERVER"
    ```
- To check the search results:

    ```bash
    docker logs t5-search
    ```


- To stop the services:

    ```bash
    docker compose down -v
    ```
  

- Available UIs:
  - Spark: http://localhost:8080
  - HDFS: http://localhost:9870
