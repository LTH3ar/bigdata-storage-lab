import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, DoubleType
from transformers import T5Tokenizer, T5Model
import torch
import numpy as np

def load_model():
    tok = T5Tokenizer.from_pretrained("t5-small")
    mdl = T5Model.from_pretrained("t5-small")
    mdl.eval()
    return tok, mdl

tokenizer, model = load_model()

def embed(text):
    inp = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad(): out = model(**inp)
    return out.last_hidden_state.mean(dim=1).squeeze().tolist()

embed_udf = udf(embed, ArrayType(DoubleType()))

def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a)*np.linalg.norm(b)))
cosine_udf = udf(cosine, DoubleType())

spark = SparkSession.builder.appName("QueryJob").getOrCreate()

# Đọc embeddings tĩnh
emb_df = spark.read.parquet(os.getenv("HDFS_URI") + "/embeddings")

# Stream truy vấn
qdf = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS")) \
    .option("subscribe", "SearchQueries").load()

schema = StructType([StructField("query", StringType())])
qjson = qdf.select(from_json(col("value").cast("string"), schema).alias("d")).select("d.*")
qemb = qjson.withColumn("q_emb", embed_udf(col("query")))

# Tính cosine similarity và chọn top-5
joined = qemb.crossJoin(emb_df) \
    .withColumn("score", cosine_udf(col("q_emb"), col("embedding")))
top5 = joined.orderBy(col("score").desc()).limit(5)

# Gửi kết quả lên Kafka
out = top5.selectExpr("to_json(struct(image_id, score)) AS value")
out.writeStream.format("kafka") \
    .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS")) \
    .option("topic", "SearchResults") \
    .option("checkpointLocation", os.getenv("HDFS_URI") + "/checkpoints/search") \
    .start() \
    .awaitTermination()
