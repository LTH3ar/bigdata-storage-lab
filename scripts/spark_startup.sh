#!/bin/bash

# check the NODE_TYPE environment variable
if [ "$NODE_TYPE" == "master" ]; then
    # run the master node script
    spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 /spark_kafka_hdfs.py
elif [ "$NODE_TYPE" == "worker" ]; then
    # run the worker node script
    echo "Worker node started"
else
    echo "Unknown node type: $NODE_TYPE"
fi