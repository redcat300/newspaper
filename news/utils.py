from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.contrib.sites.models import Site
from .models import Article

def send_news_email(article):
    category = article.category
    subscribers = category.subscribers.all()
    for subscriber in subscribers:
        email_subject = article.title
        email_body = render_to_string('news_email.html', {
            'article_title': article.title,
            'article_content': article.content[:50],
            'username': subscriber.username,
            'article_url': f"http://{Site.objects.get_current().domain}{reverse_lazy('news_detail', kwargs={'pk': article.pk})}"
        })

        email = EmailMessage(
            email_subject,
            email_body,
            to=[subscriber.email]
        )
        email.content_subtype = "html"
        email.send()