from django.views.generic import (
    CreateView, UpdateView, DeleteView
)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.mixins import (
    LoginRequiredMixin, UserPassesTestMixin
)
from django.core.management.base import BaseCommand

from django.urls import reverse_lazy
from django.contrib import messages
from .models import Post, Article, Category, Profile, Author
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import Group, User, Permission
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver





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


class NewsCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    fields = ['title', 'content']
    template_name = 'news/news_create.html'
    success_url = reverse_lazy('news_list')

    def form_valid(self, form):
        author, created = Author.objects.get_or_create(user=self.request.user)
        form.instance.author = author
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()


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


class ArticleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Article
    fields = ['title', 'content', 'category']
    template_name = 'news/article_form.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

    def form_valid(self, form):
        response = super().form_valid(form)
        send_news_email(form.instance)
        return response


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

        # Отправка приветственного письма
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        email_subject = 'Welcome to Our Site'
        email_body = render_to_string('welcome_email.html', {'username': username})

        email = EmailMessage(
            email_subject,
            email_body,
            'gavrilovvikt2012@yandex.com',  # отправитель
            [email],  # получатель
        )
        email.content_subtype = "html"
        email.send()


        authors_group, _ = Group.objects.get_or_create(name='authors')

        superuser = User.objects.get(is_superuser=True)

        superuser.groups.add(authors_group)

        add_post_permission, _ = Permission.objects.get_or_create(codename='add_post')

        authors_group.permissions.add(add_post_permission)

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

        print(f'Email пользователя {request.user.username} ({request.user.email}) при подписке на категорию {category.name}')

        send_mail(
            'Подписка на категорию',
            'Вы успешно подписались на категорию {}.'.format(category.name),
            'gavrilovvikt2012@yandex.ru',
            ["gavrilovvikt0303@gmail.com"],
            fail_silently=False,
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

        print(f'Email пользователя {request.user.username} ({request.user.email}) при отписке от категории {category.name}')

        send_mail(
            'Отписка от категории',
            'Вы успешно отписались от категории {}.'.format(category.name),
            'gavrilovvikt2012@yandex.ru',
            ["gavrilovvikt0303@gmail.com"],
            fail_silently=False,
        )

    else:
        messages.info(request, 'Вы не подписаны на эту категорию.')
    return redirect('category_list')


    def send_news_email(article):
        category = article.category
        subscribers = category.subscribers.all()
        for subscriber in subscribers:
            email_subject = article.title
            email_body = render_to_string('news_email.html', {
                'article_title': article.title,
                'article_content': article.content[:50],
                'username': subscriber.username,
                'article_url': reverse_lazy('news_detail', kwargs={'pk': article.pk})
            })

            email = EmailMessage(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,  # используем адрес отправителя из настроек
                [subscriber.email]
            )
            email.content_subtype = "html"

            # Отправляем письмо
            if settings.DEBUG:
                print(f"Отправка письма на адрес {subscriber.email}:")
                print(f"Тема: {email_subject}")
                print(f"Тело:\n{email_body}")
                print("------------------------------")
            else:
                email.send()


def send_article_notification(article):
    category = article.category
    subscribers = category.subscribers.all()

    for subscriber in subscribers:
        subject = f"Новая статья в категории {category.name}"
        message = render_to_string('email/article_notification.html', {
            'subscriber': subscriber,
            'article': article,
            'article_url': reverse_lazy('news_detail', kwargs={'pk': article.pk}),
        })
        send_mail(subject, message, 'your_email@example.com', [subscriber.email])


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
                    message = render_to_string('email/weekly_news.html', {
                        'subscriber': subscriber,
                        'articles': new_articles,
                    })
                    send_mail(subject, message, 'your_email@example.com', [subscriber.email])

