from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.conf import settings
import logging
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

def get_cache_key(post_id):
    return f'post_{post_id}'

def get_cached_post(post_id):
    cache_key = get_cache_key(post_id)
    return cache.get(cache_key)

def set_cached_post(post):
    cache_key = get_cache_key(post.id)
    cache.set(cache_key, post, timeout=60 * 5)

@shared_task
def send_new_post_email(post_id):
    from .models import Post
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        logging.warning(f"Пост с ID '{post_id}' не найден.")
        return

    categories = post.categories.all()
    if not categories:
        logging.warning(f"Пост '{post.title}' не относится ни к одной категории.")
        return

    for category in categories:
        subscribers = category.subscribers.all()
        if not subscribers:
            logging.warning(f"У категории '{category.name}' нет подписчиков.")
            continue

        for subscriber in subscribers:
            subject = f"Новая статья в категории '{category.name}'"
            html_message = render_to_string('email/new_article_notification.html', {
                'subscriber': subscriber,
                'post': post,
                'category': category,
                'article_url': f"/news/detail/{post.id}/"
            })
            plain_message = strip_tags(html_message)
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email='redcatyolo@yandex.ru',
                    recipient_list=[subscriber.email],
                    html_message=html_message
                )
                logging.info(f"Письмо отправлено на: {subscriber.email}")
            except Exception as e:
                logging.error(f"Ошибка отправки письма на {subscriber.email}: {e}")

@shared_task
def send_weekly_newsletter():
    from .models import Category
    one_week_ago = timezone.now() - timedelta(days=7)
    for category in Category.objects.all():
        posts = category.post_set.filter(created_at__gte=one_week_ago)
        if posts.exists():
            subscribers_emails = category.subscribers.values_list('email', flat=True)
            for email in subscribers_emails:
                subject = f'Новые публикации в категории {category.name}'
                html_message = render_to_string('email/weekly_news.html', {
                    'posts': posts,
                    'post_url': settings.SITE_URL + reverse('post_detail', args=[''])
                })
                plain_message = strip_tags(html_message)
                from_email = settings.DEFAULT_FROM_EMAIL
                send_mail(subject, plain_message, from_email, [email], html_message=html_message)


@shared_task
def send_welcome_email(username, email):
    subject = 'Добро пожаловать на наш портал!'
    message = f'Здравствуйте, {username}!\n\nСпасибо за регистрацию на нашем портале.'
    from_email = 'redcatyolo@yandex.ru'
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list)
