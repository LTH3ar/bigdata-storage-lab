#!/bin/bash

# Set environment variables (can be overridden by .env)
export KAFKA_SERVER=${KAFKA_SERVER:-kafka:9092}
export KAFKA_IMAGE_TOPIC=${KAFKA_IMAGE_TOPIC:-image_topic}
export KAFKA_CAPTION_TOPIC=${KAFKA_CAPTION_TOPIC:-caption_topic}

# Run the main application (t5-search, kafka producer, or other services)
echo "Starting service with Kafka at $KAFKA_SERVER"
echo "Listening to topics: $KAFKA_IMAGE_TOPIC and $KAFKA_CAPTION_TOPIC"

# Example command to start your application (adjust as needed):
python /app/t5_search.py
# Hoặc lệnh để chạy Spark job, Kafka consumer, etc.

exec "$@"


