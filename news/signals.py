from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PostCategory, User
from .tasks import send_new_post_email, send_welcome_email

@receiver(post_save, sender=PostCategory)
def notify_subscribers_on_new_post(sender, instance, created, **kwargs):

    if created:
        category = instance.category
        post = instance.post
        subscribers = category.subscribers.all()

        for subscriber in subscribers:
            send_new_post_email.delay(post.id, subscriber.email)

@receiver(post_save, sender=User)
def send_welcome_email_on_registration(sender, instance, created, **kwargs):

    if created:
        send_welcome_email.delay(instance.username, instance.email)
