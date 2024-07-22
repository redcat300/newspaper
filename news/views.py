import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User, Permission
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.core.management.base import BaseCommand
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView
)

from .models import Post, Article, Category, Profile, Author
from .utils import get_cached_post, set_cached_post, send_new_post_email


def send_email(subject, message, recipient_list, html_message=None):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='redcatyolo@yandex.ru',
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_message
        )
        logging.info(f"Письмо успешно отправлено на: {recipient_list}")
    except Exception as e:
        logging.error(f"Ошибка отправки письма: {e}")

class AuthorRequestView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            author_group = Group.objects.get(name='authors')
            request.user.groups.add(author_group)
            return redirect('profile')
        return redirect('login')


def news_list(request):
    news_list = Post.objects.order_by('-created_at')
    paginator = Paginator(news_list, 10)  # Пагинация, по 10 новостей на страницу
    page = request.GET.get('page')
    try:
        news = paginator.page(page)
    except PageNotAnInteger:
        news = paginator.page(1)
    except EmptyPage:
        news = paginator.page(paginator.num_pages)
    return render(request, 'news/news_list.html', {'news': news})


def news_detail(request, pk):
    news_item = get_object_or_404(Post, pk=pk)
    return render(request, 'news/news_detail.html', {'news_item': news_item})


def news_search(request):
    query = request.GET.get('q')
    author_username = request.GET.get('author')
    date = request.GET.get('date')

    news = Post.objects.all()

    if query:
        news = news.filter(title__icontains=query)
    if author_username:
        author = User.objects.filter(username=author_username).first()
        if author:
            news = news.filter(author=author)
        else:
            news = news.none()
    if date:
        news = news.filter(created_at__gte=date)

    return render(request, 'news/news_search.html', {'news': news})


class NewsCreateView(CreateView):
    model = Post
    fields = ['title', 'content', 'categories']
    template_name = 'news/post_form.html'
    success_url = reverse_lazy('news_list')

    def form_valid(self, form):
        # Убедись, что текущий пользователь имеет связанный объект Author
        if hasattr(self.request.user, 'author'):
            form.instance.author = self.request.user.author
        else:
            # Логируем ошибку, если у пользователя нет связанного объекта Author
            logging.error("Текущий пользователь не имеет связанного объекта Author.")
            return self.form_invalid(form)  # Возвращаем ошибку формы

        response = super().form_valid(form)
        try:
            send_new_post_email(form.instance)
            logging.info(f"Уведомления отправлены для поста: {form.instance.title}")
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомлений для поста: {form.instance.title}: {e}")
        return response


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:  # Проверка, создан ли объект
            context['article_url'] = reverse_lazy('news_detail', kwargs={'pk': self.object.pk})
        else:
            context['article_url'] = None
        return context


    def send_notifications_to_subscribers(self, article):
        category = article.category
        subscribers_emails = category.subscribers.values_list('email', flat=True)
        subject = f"Новая статья в категории {category.name}"
        message = render_to_string('email/new_article_notification.html', {
            'article': article,
            'article_url': reverse_lazy('news_detail', kwargs={'pk': article.pk}),
        })
        send_email(subject, 'У вас новый пост, пожалуйста проверьте свою почту.', list(subscribers_emails), html_message=message)


class NewsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']
    template_name = 'news/news_update.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user.groups.filter(name='authors').exists() or self.request.user == post.author.user


class NewsDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('news_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user.groups.filter(name='authors').exists() or self.request.user == post.author.user


class ArticleCreateView(CreateView):
    model = Article
    fields = ['title', 'content', 'category']
    template_name = 'news/article_form.html'
    success_url = reverse_lazy('news_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.send_notifications_to_subscribers(form.instance)
        return response

    def send_notifications_to_subscribers(self, article):
        category = article.category
        subscribers_emails = category.subscribers.values_list('email', flat=True)
        subject = f"Новая статья в категории {category.name}"
        message = render_to_string('email/new_article_notification.html', {
            'article': article,
            'article_url': reverse_lazy('news_detail', kwargs={'pk': article.pk}),
        })
        send_email(subject, 'У вас новый пост, пожалуйста проверьте свою почту.', list(subscribers_emails), html_message=message)


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    fields = ['title', 'content']
    template_name = 'news/article_form.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        article = self.get_object()
        return self.request.user.groups.filter(name='authors').exists() or self.request.user == article.author.user


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('news_list')
    template_name = 'news/article_confirm_delete.html'

    def test_func(self):
        article = self.get_object()
        return self.request.user.groups.filter(name='authors').exists() or self.request.user == article.author.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ['bio', 'location', 'birth_date']
    template_name = 'profiles/profile_edit.html'
    success_url = reverse_lazy('profile_detail')

    def get_object(self, queryset=None):
        # Получаем объект профиля текущего пользователя
        return self.request.user.profile

    def form_valid(self, form):
        # Убедимся, что текущий пользователь сохраняется как владелец профиля
        form.instance.user = self.request.user
        return super().form_valid(form)


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save(commit=False)
        email = form.cleaned_data['email']
        username = form.cleaned_data['username']
        user.save()

        send_email(
            subject='Добро пожаловать на наш сайт!',
            message=f'Здравствуйте, {username}!\n\nСпасибо за регистрацию на нашем сайте.',
            recipient_list=[email],
            html_message=render_to_string('email/welcome_email.html', {'username': username})
        )

        return response


@login_required
def profile(request):
    return render(request, 'profile.html')


def category_list(request):
    categories = Category.objects.all()
    user = request.user
    return render(request, 'categories.html', {'categories': categories, 'user': user})


@login_required
def subscribed_categories(request):
    # Получаем категории, на которые подписан текущий пользователь
    subscribed_categories = request.user.subscribed_categories.all()
    return render(request, 'subscribed_categories.html', {'subscribed_categories': subscribed_categories})


@login_required
def subscribe_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.user not in category.subscribers.all():
        category.subscribers.add(request.user)
        messages.success(request, 'Вы успешно подписались на категорию.')

        send_email(
            subject='Подписка на категорию',
            message=f'Вы успешно подписались на категорию {category.name}.',
            recipient_list=[request.user.email]
        )
    else:
        messages.info(request, 'Вы уже подписаны на эту категорию.')
    return redirect('category_list')


@login_required
def unsubscribe_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.user in category.subscribers.all():
        category.subscribers.remove(request.user)
        messages.success(request, 'Вы успешно отписались от категории.')

        send_email(
            subject='Отписка от категории',
            message=f'Вы успешно отписались от категории {category.name}.',
            recipient_list=[request.user.email]
        )
    else:
        messages.info(request, 'Вы не подписаны на эту категорию.')
    return redirect('category_list')

def send_news_email(article):
    category = article.category
    subscribers = category.subscribers.all()

    for subscriber in subscribers:
        subject = f"Новая статья в категории {category.name}"
        message_html = render_to_string('email/new_article_notification.html', {
            'subscriber': subscriber,
            'article': article,
            'category': category,
        })

        send_email(
            subject=subject,
            message='У вас новый пост, пожалуйста проверьте свою почту.',
            recipient_list=[subscriber.email],
            html_message=message_html
        )


def send_article_notification(article):
    categories = article.category
    subscribers = category.subscribers.all()

    for subscriber in subscribers:
        subject = f"Новая статья в категории {category.name}"
        message = render_to_string('email/new_article_notification.html', {
            'subscriber': subscriber,
            'article': article,
            'article_url': reverse_lazy('news_detail', kwargs={'pk': article.pk}),
        })
        send_email(subject, message, [subscriber.email], html_message=message)


class Command(BaseCommand):
    help = 'Send weekly news to subscribers'

    def handle(self, *args, **kwargs):
        last_week = timezone.now() - timedelta(days=7)
        categories = Category.objects.all()
        for category in categories:
            new_articles = category.articles.filter(created_at__gte=last_week)
            if new_articles.exists():
                for subscriber in category.subscribers.all():
                    subject = f"Новые статьи в категории {category.name}"
                    html_message = render_to_string('email/weekly_news.html', {
                        'subscriber': subscriber,
                        'articles': new_articles,
                    })
                    plain_message = strip_tags(html_message)

                    send_email(
                        subject=subject,
                        message=plain_message,
                        recipient_list=[subscriber.email],
                        html_message=html_message
                    )

@method_decorator(cache_page(60 * 5), name='dispatch')
class NewsListView(ListView):
    model = Post
    template_name = 'news/news_list.html'

class NewsDetailView(DetailView):
    model = Post
    template_name = 'news/news_detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post_id = self.kwargs.get('pk')
        post = get_cached_post(post_id)
        if not post:
            post = super().get_object(queryset)
            set_cached_post(post)
        return post