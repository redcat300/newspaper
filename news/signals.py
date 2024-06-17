from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post, PostCategory
from .utils import send_new_post_email, send_welcome_email
from django.contrib.auth.models import User

@receiver(post_save, sender=Post)
def notify_subscribers_on_new_post(sender, instance, created, **kwargs):
    if created:
        send_new_post_email.delay(instance.id)


@receiver(post_save, sender=User)
def send_welcome_email_on_registration(sender, instance, created, **kwargs):
    if created:
        send_welcome_email.delay(instance.username, instance.email)
