#!/bin/bash

# create kafka topic
kafka-topics.sh --create --topic image_topic --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1

# # wait 30 seconds
# sleep 30

# python /kafka_producer.py