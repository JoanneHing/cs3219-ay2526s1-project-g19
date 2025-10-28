# Kafka-Based Topics and Difficulties Distribution

This document describes the implementation of Kafka-based distribution of topics and difficulties lists, replacing the previous HTTP API endpoints approach.

## Overview

Previously, the matching service made HTTP requests to the question service endpoints:
- `GET /api/topics` - Returns list of available topics
- `GET /api/difficulty` - Returns list of available difficulties

This approach had several limitations:
1. **Performance**: HTTP requests on every validation
2. **Coupling**: Direct service-to-service dependencies
3. **Scalability**: Multiple services making the same requests
4. **Reliability**: HTTP failures could break matching

The new Kafka-based approach provides:
1. **Event-driven**: Real-time updates when data changes
2. **Decoupled**: Services subscribe to events independently
3. **Scalable**: Multiple consumers can subscribe
4. **Reliable**: Kafka's durability and fault tolerance

## Architecture

### Question Service (Publisher)

**New Components:**
- `kafka/publisher.py` - Publishes topics/difficulties updates
- `kafka/signals.py` - Django signals for automatic publishing
- `kafka/schemas/topics_updated.avsc` - Avro schema for topics
- `kafka/schemas/difficulties_updated.avsc` - Avro schema for difficulties
- `management/commands/setup_kafka.py` - Setup command

**Kafka Topics:**
- `topics.updated` - Published when topics list changes
- `difficulties.updated` - Published when difficulties list changes

**Event Triggers:**
- Question created/updated/deleted (via Django signals)
- Manual publishing via management command
- Service startup (initial data publication)

### Matching Service (Consumer)

**New Components:**
- `kafka/consumers/topics_difficulties_consumer.py` - Consumes updates
- Updated `service/django_question_service.py` - Uses cached data

**Behavior:**
- Subscribes to `topics.updated` and `difficulties.updated` topics
- Caches received data in memory
- Falls back to HTTP if no cached data available
- Uses cached data for validation (faster response)

## Implementation Details

### Question Service Changes

1. **Kafka Publisher** (`kafka/publisher.py`):
   ```python
   class TopicsDifficultiesPublisher:
       def publish_topics_update(self, topics_list)
       def publish_difficulties_update(self, difficulties_list)
       def publish_initial_data(self)
   ```

2. **Django Signals** (`kafka/signals.py`):
   ```python
   @receiver(post_save, sender=Question)
   def question_saved(sender, instance, created, **kwargs)
   
   @receiver(post_delete, sender=Question)
   def question_deleted(sender, instance, **kwargs)
   ```

3. **Avro Schemas**:
   - `topics_updated.avsc`: Contains topics array, timestamp, version
   - `difficulties_updated.avsc`: Contains difficulties array, timestamp, version

### Matching Service Changes

1. **Consumer** (`kafka/consumers/topics_difficulties_consumer.py`):
   ```python
   class TopicsDifficultiesConsumer:
       async def handle_topics_update(self, data: dict)
       async def handle_difficulties_update(self, data: dict)
   ```

2. **Updated Service** (`service/django_question_service.py`):
   ```python
   async def get_topics(self) -> list[str]:
       # Try cached data first
       if self.topics is not None:
           return self.topics
       # Fallback to HTTP
       if self._fallback_to_http:
           return await self._fetch_topics_http()
       return []
   ```

## Deployment Steps

### 1. Question Service Setup

1. **Register Schemas**:
   ```bash
   cd question_service
   python manage.py setup_kafka --register-schemas-only
   ```

2. **Publish Initial Data**:
   ```bash
   python manage.py setup_kafka --publish-only
   ```

3. **Start Service** (signals will auto-publish on changes)

### 2. Matching Service Setup

1. **Start Service** (consumer will start automatically)
2. **Verify Logs** for successful subscription and data reception

### 3. Environment Variables

Add to your `.env` file:
```bash
# Kafka Topics
TOPIC_TOPICS_UPDATED=topics.updated
TOPIC_DIFFICULTIES_UPDATED=difficulties.updated
```

## Benefits

### Performance Improvements
- **Before**: HTTP request on every validation (~50-100ms)
- **After**: In-memory cache lookup (~1ms)
- **Improvement**: 50-100x faster validation

### Reliability Improvements
- **Before**: Single point of failure (HTTP endpoint)
- **After**: Kafka's built-in durability and replication
- **Fallback**: HTTP still available if Kafka data unavailable

### Scalability Improvements
- **Before**: Each service makes individual HTTP requests
- **After**: Single publisher, multiple subscribers
- **Scalability**: Linear scaling with number of consumers

## Monitoring and Observability

### Key Metrics to Monitor

1. **Question Service**:
   - Kafka publish success/failure rates
   - Message publishing latency
   - Schema registration status

2. **Matching Service**:
   - Kafka consumption lag
   - Cache hit/miss rates
   - HTTP fallback usage

3. **Kafka Topics**:
   - Message throughput
   - Consumer lag
   - Topic partition health

### Logging

Both services include comprehensive logging:
- Topic/difficulties updates
- Cache hits/misses
- HTTP fallback usage
- Kafka connection status

## Migration Strategy

### Phase 1: Deploy Question Service
1. Deploy question service with Kafka publisher
2. Register schemas and publish initial data
3. Verify topics are being published

### Phase 2: Deploy Matching Service
1. Deploy matching service with consumer
2. Verify data is being consumed and cached
3. Monitor fallback usage

### Phase 3: Optimize
1. Monitor performance improvements
2. Adjust caching strategies if needed
3. Consider removing HTTP endpoints (optional)

## Troubleshooting

### Common Issues

1. **No cached data in matching service**:
   - Check Kafka consumer logs
   - Verify topic names match
   - Check schema registry connectivity

2. **HTTP fallback being used**:
   - Normal during startup
   - Check Kafka consumer status
   - Verify message consumption

3. **Schema registration failures**:
   - Check schema registry credentials
   - Verify schema syntax
   - Check network connectivity

### Debug Commands

```bash
# Check Kafka topics
kafka-topics --bootstrap-server <kafka-server> --list

# Check consumer lag
kafka-consumer-groups --bootstrap-server <kafka-server> --describe --group <group-id>

# Check schema registry
curl -u <username>:<password> <schema-registry-url>/subjects
```

## Future Enhancements

1. **Caching Strategy**: Implement Redis-based caching for distributed services
2. **Versioning**: Add schema versioning for backward compatibility
3. **Metrics**: Add Prometheus metrics for monitoring
4. **Dead Letter Queue**: Handle failed message processing
5. **Compression**: Enable Kafka compression for large payloads

