from celery import shared_task
from django.urls import reverse
from django.core.mail import send_mail
from django.utils.html import format_html
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Post, User, Profile
import logging
import pytz
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)

# Настраиваем логирование
logger = logging.getLogger(__name__)

@shared_task
def send_welcome_email(username, user_email):

    logger.info(f'Отправка приветственного письма на {user_email}')
    message = f'Здравствуйте, {username}! Добро пожаловать на наш сайт!'
    try:
        send_mail(
            'Добро пожаловать!',
            message,
            'redcatyolo@yandex.ru',
            [user_email],
            fail_silently=False,
        )
        logger.info(f'Письмо успешно отправлено на {user_email}')
    except Exception as e:
        logger.error(f'Ошибка при отправке письма на {user_email}: {e}')


@shared_task
def send_new_post_email(post_id, subscriber_email):
    from .models import Post
    try:
        post = Post.objects.get(id=post_id)
        post_url = f'http://127.0.0.1:8000{reverse("news_detail", args=[post.id])}'

        logger.info(f'Отправка уведомления о новой публикации "{post.title}" на {subscriber_email}')

        message = format_html(
            'Новая публикация: <a href="{url}">{title}</a>. Посмотрите на нашем сайте!',
            url=post_url,
            title=post.title
        )

        send_mail(
            'Новая публикация!',
            message,
            'redcatyolo@yandex.ru',
            [subscriber_email],
            fail_silently=False,
            html_message=message
        )
        logger.info(f'Письмо успешно отправлено на {subscriber_email}')
    except Post.DoesNotExist:
        logger.error(f'Пост с ID {post_id} не найден.')
    except Exception as e:
        logger.error(f'Ошибка при отправке письма на {subscriber_email}: {e}')

@shared_task
def send_weekly_newsletter():
    timezone = pytz.timezone('Europe/Moscow')  # Замените на вашу временную зону
    one_week_ago = timezone.localize(datetime.now() - timedelta(days=7))
    recent_posts = Post.objects.filter(created_at__gte=one_week_ago)

    if not recent_posts.exists():
        logger.info('Нет новых новостей за последнюю неделю.')
        return

    subject = 'Еженедельная рассылка новостей'
    html_content = render_to_string('email/weekly_news.html', {'posts': recent_posts})
    text_content = strip_tags(html_content)

    subscribers = Profile.objects.filter(is_subscribed=True)
    for profile in subscribers:
        try:
            send_mail(
                subject,
                text_content,
                'redcatyolo@yandex.ru',
                [profile.user.email],
                html_message=html_content,
                fail_silently=False,
            )
            logger.info(f'Письмо успешно отправлено на {profile.user.email}')
        except Exception as e:
            logger.error(f'Ошибка при отправке письма на {profile.user.email}: {e}')