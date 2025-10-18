import logging
from django.core.management.base import BaseCommand
from question_service.kafka.kafka_client import kafka_client

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs Kafka consumer for question service"

    def handle(self, *args, **options):
        kafka_client.match_found_consumer()
