# spark_kafka_hdfs.py - Spark job to consume Kafka stream and save to HDFS
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

KAFKA_TOPIC = "image_topic"
KAFKA_SERVER = "kafka:9092"
HDFS_OUTPUT_PATH = "hdfs://namenode:9000/raw_images/"

spark = SparkSession.builder.appName("KafkaToHDFS").getOrCreate()

# Read stream from Kafka
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", KAFKA_TOPIC) \
    .load()

# Extract image name and data
df = df.selectExpr("CAST(key AS STRING)", "value")

# Write image data to HDFS
query = df.writeStream \
    .format("parquet") \
    .option("path", HDFS_OUTPUT_PATH) \
    .option("checkpointLocation", "/tmp/checkpoints") \
    .start()

query.awaitTermination()
