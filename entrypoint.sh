#!/bin/bash
set -e

# Đường dẫn file caption trên HDFS (điều này phải khớp với file được ghi bởi Spark hoặc một job tương tự)
HDFS_CAPTIONS_PATH="/captions/captions.csv"

echo "[t5-search] Đang kiểm tra dữ liệu captions trên HDFS tại $HDFS_CAPTIONS_PATH..."

# Kiểm tra xem file captions đã tồn tại trên HDFS hay chưa.
# Lệnh 'hdfs dfs -test -e' sẽ trả về 0 nếu file tồn tại.
while true; do
  if hdfs dfs -test -e $HDFS_CAPTIONS_PATH; then
    echo "[t5-search] Tìm thấy file captions trên HDFS."
    break
  else
    echo "[t5-search] Chưa tìm thấy file captions trên HDFS, chờ 5 giây..."
    sleep 5
  fi
done

echo "[t5-search] Bắt đầu tìm kiếm với từ khóa: $SEARCH_QUERY"
exec python t5_image_search.py "$SEARCH_QUERY" --top "$TOP_RESULTS"

