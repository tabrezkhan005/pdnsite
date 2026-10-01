from django.core.management.base import BaseCommand
from apps.academics.tasks import generate_upcoming_sessions

class Command(BaseCommand):
    help = "Extends class sessions for all active batches 30 days ahead."

    def handle(self, *args, **options):
        self.stdout.write("Generating upcoming sessions...")
        generate_upcoming_sessions()
        self.stdout.write(self.style.SUCCESS("Successfully generated upcoming sessions."))
