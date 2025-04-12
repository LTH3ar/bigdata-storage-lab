#!/bin/bash
# Tạo thư mục và đẩy data lên HDFS
hdfs dfs -mkdir -p /data/images
hdfs dfs -put /data/flickr30k_images/* /data/images/
hdfs dfs -put /data/results.csv /data/
hdfs dfs -ls /data
