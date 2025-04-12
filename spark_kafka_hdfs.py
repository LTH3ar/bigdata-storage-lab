from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StringType

KAFKA_IMAGE_TOPIC = "image_topic"
KAFKA_CAPTION_TOPIC = "caption_topic"
KAFKA_SERVER = "kafka:9092"
HDFS_OUTPUT_PATH = "hdfs://namenode:9000/raw_images/"
CHECKPOINT_PATH = "/tmp/checkpoints"

spark = SparkSession.builder.appName("KafkaToHDFS").getOrCreate()

# Đọc stream từ Kafka cho cả 2 topic
df_images = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", KAFKA_IMAGE_TOPIC) \
    .load()

df_captions = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", KAFKA_CAPTION_TOPIC) \
    .load()

# Giải mã dữ liệu từ Kafka (ảnh là nhị phân, caption là văn bản)
df_images = df_images.selectExpr("CAST(key AS STRING)", "CAST(value AS BINARY) AS image_data")
df_captions = df_captions.selectExpr("CAST(key AS STRING) AS image_name", "CAST(value AS STRING) AS caption")

# Kết hợp ảnh và caption dựa trên key (image_name)
df_combined = df_images.join(df_captions, df_images.key == df_captions.image_name, "inner") \
    .select(df_images.key.alias("image_name"), df_images.image_data, df_captions.caption)

# Ghi kết quả vào HDFS dưới định dạng Parquet
query = df_combined.writeStream \
    .format("parquet") \
    .option("path", HDFS_OUTPUT_PATH) \
    .option("checkpointLocation", CHECKPOINT_PATH) \
    .start()

query.awaitTermination()

