# news/signals.py

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags  # Исправленный импорт
from news.models import PostCategory, Category
import logging


def send_email(subject, message, recipient_list, html_message=None):
    from django.core.mail import send_mail
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='redcatyolo@yandex.ru',
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_message
        )
        logging.info(f"Письмо отправлено на: {recipient_list}")
    except Exception as e:
        logging.error(f"Ошибка отправки письма: {e}")


@receiver(post_save, sender=PostCategory)
def send_post_notification(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        category = instance.category
        subscribers = category.subscribers.all()

        if not subscribers:
            logging.warning(f"У категории {category.name} нет подписчиков.")
            return

        for subscriber in subscribers:
            subject = f"Новая статья в категории {category.name}"
            html_message = render_to_string('email/new_article_notification.html', {
                'subscriber': subscriber,
                'post': post,
                'category': category,
                'article_url': f"/news/detail/{post.id}/"  # Используем ID поста для создания ссылки
            })
            plain_message = strip_tags(html_message)

            send_email(
                subject=subject,
                message=plain_message,
                recipient_list=[subscriber.email],
                html_message=html_message
            )
        logging.info(f"Письмо отправлено для поста {post.title} в категории {category.name}.")


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        subject = 'Добро пожаловать на наш сайт!'
        html_message = render_to_string('email/welcome_email.html', {'username': instance.username})
        plain_message = strip_tags(html_message)

        send_email(
            subject=subject,
            message=plain_message,
            recipient_list=[instance.email],
            html_message=html_message
        )
