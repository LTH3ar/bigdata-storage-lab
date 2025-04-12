import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, DoubleType
from transformers import T5Tokenizer, T5Model
import torch

def load_model():
    tok = T5Tokenizer.from_pretrained("t5-small")
    mdl = T5Model.from_pretrained("t5-small")
    mdl.eval()
    return tok, mdl

tokenizer, model = load_model()

def embed(text):
    inp = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad(): out = model(**inp)
    emb = out.last_hidden_state.mean(dim=1).squeeze().tolist()
    return emb

embed_udf = udf(embed, ArrayType(DoubleType()))

spark = SparkSession.builder.appName("CaptionEmbeddingJob").getOrCreate()

df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS")) \
    .option("subscribe", "Captions").load()

schema = StructType([StructField("image_id", StringType()), StructField("caption", StringType())])
json_df = df.select(from_json(col("value").cast("string"), schema).alias("d")).select("d.*")

emb_df = json_df.withColumn("embedding", embed_udf(col("caption")))

emb_df.writeStream \
    .format("parquet") \
    .option("path", os.getenv("HDFS_URI") + "/embeddings") \
    .option("checkpointLocation", os.getenv("HDFS_URI") + "/checkpoints/embeddings") \
    .start() \
    .awaitTermination()
