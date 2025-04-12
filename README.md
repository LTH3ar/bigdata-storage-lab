# Big Data Pipeline - Tìm Ảnh qua Caption với T5

## Cách Triển khai và Chạy

### 1. Chuẩn bị
- Docker và Docker Compose đã cài trên máy.
- Clone repository và đảm bảo có đầy đủ thư mục:
  ```bash
  git clone <repo_url>
  cd project-root
  ```
- Copy dữ liệu `flickr30k_images/` và file `results.csv` vào thư mục `data/`

### 2. Khởi động hệ thống
```bash
docker-compose up -d
```

### 3. Đưa dữ liệu lên HDFS
```bash
docker-compose run --rm hadoop-init
```

### 4. Gửi caption lên Kafka
```bash
docker-compose up -d producer
```

### 5. Chạy Spark job tính embedding caption
```bash
docker-compose exec spark-master spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2 \
  /opt/app/caption_embedding_job.py
```

### 6. Gửi truy vấn caption (Search)
```bash
docker-compose run --rm search-producer python search_producer.py "a man riding a horse"
```

### 7. Chạy Spark job tìm kiếm theo truy vấn
```bash
docker-compose exec spark-master spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2 \
  /opt/app/query_job.py
```

### 8. Xem kết qủa tìm kiếm
```bash
docker-compose exec kafka kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic SearchResults --from-beginning
```

---

## Tóm tắt
- Caption được streaming từ file `results.csv` lên Kafka topic `Captions`.
- Spark Structured Streaming nhận và nhớ caption, tính embedding bằng T5, lưu vào HDFS.
- Spark job khác stream truy vấn từ Kafka topic `SearchQueries`, tính embedding và so khớp cosine similarity.
- Top-5 kế tủa tìm kiếm được đẩy lên topic `SearchResults`.

