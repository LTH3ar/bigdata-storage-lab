#!/bin/bash
set -e

echo "[t5-search] Đang đợi file CSV: $CSV_PATH"

# Chờ file CSV có kích thước > 0 (có dữ liệu)
while [ ! -s "$CSV_PATH" ]; do
  echo "[t5-search] CSV chưa có dữ liệu. Chờ 5 giây..."
  sleep 5
done

echo "[t5-search] CSV đã sẵn sàng. Bắt đầu tìm kiếm với từ khóa: $SEARCH_QUERY"
exec python t5_image_search.py "$SEARCH_QUERY" --csv "$CSV_PATH" --top "$TOP_RESULTS"
