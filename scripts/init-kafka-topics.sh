#!/bin/bash
set -e

echo "Waiting for Kafka at $KAFKA_HOST:$KAFKA_PORT ..."

# Wait until Kafka is ready
until /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server "$KAFKA_HOST:$KAFKA_PORT" >/dev/null 2>&1; do
  echo "Kafka not ready yet..."
  sleep 2
done

echo "Kafka ready, creating topics..."

# Loop through all topics from env
for TOPIC_VAR in TOPIC_MATCH_FOUND TOPIC_USER_ACTIVITY; do
  TOPIC_NAME="${!TOPIC_VAR}"
  echo "Creating topic: $TOPIC_NAME"
  /opt/kafka/bin/kafka-topics.sh --create \
    --topic "$TOPIC_NAME" \
    --bootstrap-server "$KAFKA_HOST:$KAFKA_PORT" \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists
done

echo "All topics created. Current topics:"
/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server "$KAFKA_HOST:$KAFKA_PORT"
