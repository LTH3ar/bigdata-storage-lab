#!/usr/bin/env python3
"""
File: t5_image_search.py
Mô tả: Tìm kiếm ảnh thông qua caption sử dụng mô hình T5.
Phiên bản mới tích hợp với pipeline Big Data, thay vì đọc file CSV cục bộ thì lấy dữ liệu caption từ HDFS.
Có thể nhận tham số từ dòng lệnh hoặc qua biến môi trường:
    - SEARCH_QUERY: từ khóa tìm kiếm (nếu không truyền qua dòng lệnh)
    - HDFS_CAPTIONS_PATH: đường dẫn trên HDFS chứa file CSV caption (mặc định là /captions/captions.csv)
    - TOP_RESULTS: số lượng kết quả hiển thị (mặc định là 5)
Usage:
    python t5_image_search.py "từ khóa tìm kiếm" --top 5
Ví dụ:
    python t5_image_search.py "biển xanh" --top 5
"""

import argparse
import csv
import os
import sys
import tempfile

import torch
import torch.nn.functional as F
from transformers import T5Tokenizer, T5EncoderModel

# Sử dụng thư viện hdfs để download file từ HDFS thông qua WebHDFS (port mặc định của Namenode UI là 9870)
from hdfs import InsecureClient


def load_captions_from_hdfs(hdfs_path):
    """
    Kết nối với HDFS và tải file CSV chứa caption về tạm (local) rồi đọc nội dung.
    Mỗi bản ghi là một dict với các khóa: 'image' và 'caption'.
    """
    try:
        # Kết nối với HDFS (đảm bảo hostname 'namenode' được định danh trong mạng của docker-compose)
        client = InsecureClient("http://namenode:9870", user="hadoop")
        with tempfile.NamedTemporaryFile(mode="r+", delete=False, encoding='utf-8') as tmpfile:
            # Tải file từ HDFS về file tạm
            client.download(hdfs_path, tmpfile.name, overwrite=True)
            tmpfile.flush()
            tmpfile.seek(0)
            captions = []
            reader = csv.DictReader(tmpfile)
            for row in reader:
                captions.append(row)
        return captions
    except Exception as e:
        print(f"Lỗi khi tải file từ HDFS ({hdfs_path}): {e}")
        sys.exit(1)


def compute_embedding(text, tokenizer, model, device):
    """
    Tính embedding trung bình cho văn bản sử dụng encoder của T5.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=64)
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
    # Lấy giá trị mặc định từ biến môi trường nếu có
    default_query = os.environ.get("SEARCH_QUERY")
    default_hdfs_path = os.environ.get("HDFS_CAPTIONS_PATH", "/captions/captions.csv")
    default_top = os.environ.get("TOP_RESULTS", "5")
    
    parser = argparse.ArgumentParser(description="Tìm kiếm ảnh thông qua caption sử dụng T5")
    parser.add_argument("query", type=str, nargs="?", default=default_query, help="Caption hoặc từ khóa tìm kiếm")
    parser.add_argument("--csv", type=str, default=default_hdfs_path,
                        help="Đường dẫn HDFS tới file CSV chứa caption (ví dụ: /captions/captions.csv)")
    parser.add_argument("--top", type=int, default=int(default_top), help="Số lượng ảnh kết quả hiển thị")
    args = parser.parse_args()

    if not args.query:
        print("Vui lòng cung cấp từ khóa tìm kiếm thông qua tham số dòng lệnh hoặc biến môi trường SEARCH_QUERY.")
        sys.exit(1)

    # Tải dữ liệu caption từ HDFS
    print(f"Đang tải file caption từ HDFS: {args.csv} ...")
    captions = load_captions_from_hdfs(args.csv)
    if len(captions) == 0:
        print("Không có caption nào được tải từ file trên HDFS.")
        sys.exit(0)

    # Thiết lập thiết bị: GPU nếu có, ngược lại sử dụng CPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Tải tokenizer và model T5 encoder (sử dụng t5-small)
    print("Đang tải mô hình T5...")
    tokenizer = T5Tokenizer.from_pretrained("t5-small")
    model = T5EncoderModel.from_pretrained("t5-small")
    model.to(device)
    model.eval()

    print("Tính embedding cho query...")
    query_embedding = compute_embedding(args.query, tokenizer, model, device)

    results = []
    print("Đang tính độ tương đồng cho từng caption...")
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

    # Sắp xếp theo độ tương đồng giảm dần và lấy top kết quả
    results = sorted(results, key=lambda x: x["similarity"], reverse=True)
    top_results = results[:args.top]

    print(f"\nTop {args.top} kết quả tìm kiếm cho query: '{args.query}'")
    for res in top_results:
        print(f"Image: {res['image']}\nCaption: {res['caption']}\nĐộ tương đồng: {res['similarity']:.4f}\n{'-'*40}")


if __name__ == "__main__":
    main()

