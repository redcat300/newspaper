
from django.core.management.base import BaseCommand
from news.utils import send_weekly_newsletter

class Command(BaseCommand):
    help = 'Send weekly newsletter to category subscribers'

    def handle(self, *args, **kwargs):
        send_weekly_newsletter()
        self.stdout.write(self.style.SUCCESS('Successfully sent weekly newsletter'))
