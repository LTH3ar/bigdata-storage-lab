#!/usr/bin/env python3
"""
File: t5_image_search.py
Mô tả: Tìm kiếm ảnh thông qua caption sử dụng mô hình T5 và lấy dữ liệu trực tiếp từ Kafka topic.
Các tham số (có thể được truyền qua biến môi trường hoặc dòng lệnh):
    - SEARCH_QUERY: từ khóa tìm kiếm (bắt buộc)
    - KAFKA_TOPIC: tên topic chứa dữ liệu caption (mặc định: "caption_topic")
    - KAFKA_SERVER: Kafka bootstrap server (mặc định: "kafka:9092")
    - TOP_RESULTS: số lượng kết quả hiển thị (mặc định: 5)
Usage:
    python t5_image_search.py "từ khóa tìm kiếm" --top 5
Ví dụ:
    python t5_image_search.py "biển xanh" --top 5
"""

import argparse
import json
import os
import sys
import time

import torch
import torch.nn.functional as F
from kafka import KafkaConsumer
from transformers import T5Tokenizer, T5EncoderModel


def load_captions_from_kafka(topic, kafka_server, consumer_timeout=30000):
    """
    Kết nối với Kafka và thu thập message từ topic.
    consumer_timeout: thời gian chờ (ms) để dừng lắng nghe khi không có message mới.
    Các message được giả định là định dạng JSON có các khóa 'image' và 'caption'.
    """
    captions = []
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[kafka_server],
            auto_offset_reset='earliest',
            consumer_timeout_ms=consumer_timeout,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        print(f"[t5-search] Đang thu thập dữ liệu từ Kafka topic '{topic}' trong khoảng {consumer_timeout/1000} giây ...")
        for message in consumer:
            captions.append(message.value)
        consumer.close()
        if len(captions) == 0:
            print("[t5-search] Không nhận được message nào từ Kafka topic.")
        return captions
    except Exception as e:
        print(f"[t5-search] Lỗi khi kết nối tới Kafka: {e}")
        sys.exit(1)


def compute_embedding(text, tokenizer, model, device):
    """
    Tính embedding trung bình cho văn bản sử dụng encoder của T5.
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=64
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        encoder_outputs = model.encoder(**inputs)
    embeddings = encoder_outputs.last_hidden_state  # shape: (batch, seq_length, hidden_size)
    attention_mask = inputs["attention_mask"]
    mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
    sum_embeddings = torch.sum(embeddings * mask_expanded, dim=1)
    sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    avg_embedding = sum_embeddings / sum_mask
    return avg_embedding.squeeze(0)


def main():
    # Lấy giá trị từ biến môi trường (nếu có)
    default_query = os.environ.get("SEARCH_QUERY")
    default_topic = os.environ.get("KAFKA_TOPIC", "caption_topic")
    default_kafka_server = os.environ.get("KAFKA_SERVER", "kafka:9092")
    default_top = os.environ.get("TOP_RESULTS", "5")
    
    parser = argparse.ArgumentParser(description="Tìm kiếm ảnh thông qua caption sử dụng T5 và Kafka")
    parser.add_argument("query", type=str, nargs="?", default=default_query,
                        help="Caption hoặc từ khóa tìm kiếm")
    parser.add_argument("--top", type=int, default=int(default_top),
                        help="Số lượng ảnh kết quả hiển thị")
    parser.add_argument("--topic", type=str, default=default_topic,
                        help="Tên Kafka topic chứa dữ liệu caption")
    parser.add_argument("--kafka", type=str, default=default_kafka_server,
                        help="Kafka bootstrap server (ví dụ: kafka:9092)")
    args = parser.parse_args()

    if not args.query:
        print("Vui lòng cung cấp từ khóa tìm kiếm thông qua tham số dòng lệnh hoặc biến môi trường SEARCH_QUERY.")
        sys.exit(1)

    # Lấy dữ liệu caption từ Kafka
    captions = load_captions_from_kafka(args.topic, args.kafka)
    if len(captions) == 0:
        print("Không có dữ liệu caption được thu thập từ Kafka. Kết thúc chương trình.")
        sys.exit(0)

    # Thiết lập thiết bị: GPU nếu có, ngược lại CPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Tải tokenizer và model T5 encoder (sử dụng phiên bản t5-small)
    print("[t5-search] Đang tải mô hình T5...")
    tokenizer = T5Tokenizer.from_pretrained("t5-small")
    model = T5EncoderModel.from_pretrained("t5-small")
    model.to(device)
    model.eval()

    print("[t5-search] Tính embedding cho query...")
    query_embedding = compute_embedding(args.query, tokenizer, model, device)

    results = []
    print("[t5-search] Tính độ tương đồng cho từng caption nhận được từ Kafka...")
    for item in captions:
        caption_text = item.get('caption', '')
        image_file = item.get('image', 'unknown')
        caption_embedding = compute_embedding(caption_text, tokenizer, model, device)
        similarity = F.cosine_similarity(query_embedding, caption_embedding, dim=0).item()
        results.append({
            "image": image_file,
            "caption": caption_text,
            "similarity": similarity
        })

    # Sắp xếp kết quả theo độ tương đồng giảm dần và lấy top kết quả
    results = sorted(results, key=lambda x: x["similarity"], reverse=True)
    top_results = results[:args.top]

    print(f"\nTop {args.top} kết quả tìm kiếm cho query: '{args.query}'")
    for res in top_results:
        print(f"Image: {res['image']}\nCaption: {res['caption']}\nĐộ tương đồng: {res['similarity']:.4f}\n{'-'*40}")


if __name__ == "__main__":
    main()

