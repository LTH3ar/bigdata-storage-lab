#!/bin/bash
set -e

# Đọc các biến môi trường cần thiết (nếu có)
: "${SEARCH_QUERY:?Vui lòng định nghĩa biến môi trường SEARCH_QUERY}"
: "${KAFKA_SERVER:=kafka:9092}"
: "${KAFKA_TOPIC:=caption_topic}"
: "${TOP_RESULTS:=5}"

echo "[t5-search] Đang kiểm tra kết nối tới Kafka tại $KAFKA_SERVER ..."

# Nếu cần, có thể thêm kiểm tra (ví dụ dùng telnet hoặc nc) để đảm bảo Kafka server đã sẵn sàng.
# Ví dụ:
# until nc -z $(echo $KAFKA_SERVER | cut -d':' -f1) $(echo $KAFKA_SERVER | cut -d':' -f2); do
#   echo "[t5-search] Chờ Kafka sẵn sàng..."
#   sleep 5
# done

# Nếu không có cơ chế kiểm tra, ta dùng sleep tạm thời
sleep 10

echo "[t5-search] Bắt đầu tìm kiếm với từ khóa: $SEARCH_QUERY"
exec python t5_image_search.py "$SEARCH_QUERY" --top "$TOP_RESULTS" --topic "$KAFKA_TOPIC" --kafka "$KAFKA_SERVER"


