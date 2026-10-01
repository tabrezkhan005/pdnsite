from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Batch
from .services import generate_sessions

@shared_task
def generate_upcoming_sessions():
    """
    Task to run nightly: extends sessions for all active batches 30 days ahead.
    """
    today = timezone.now().date()
    to_date = today + timedelta(days=30)
    
    active_batches = Batch.objects.filter(is_active=True)
    for batch in active_batches:
        generate_sessions(batch, today, to_date)
