# news/views.py

from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.http import Http404
from .models import Post
from .models import Article

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
        author = User.objects.filter(username=author_username).first()  # Получаем пользователя по имени
        if author:
            news = news.filter(author=author)  # Фильтруем новости по полученному пользователю
        else:
            news = news.none()  # Если пользователь не найден, возвращаем пустой queryset
    if date:
        news = news.filter(created_at__gte=date)

    return render(request, 'news/news_search.html', {'news': news})

class NewsCreateView(CreateView):
    model = Post
    fields = ['title', 'content']  # Укажите нужные поля модели
    template_name = 'news/news_create.html'
    success_url = reverse_lazy('news_list')  # Укажите URL для перенаправления после успешного создания

class NewsUpdateView(UpdateView):
    model = Post
    fields = ['title', 'content']
    template_name = 'news/news_update.html'
    success_url = reverse_lazy('news_list')

class NewsDeleteView(DeleteView):
    model = Post
    success_url = reverse_lazy('news_list')


class ArticleCreateView(CreateView):
    model = Article
    fields = ['title', 'content']
    template_name = 'news/article_form.html'  # Изменили путь к шаблону
    success_url = reverse_lazy('news_list')


class ArticleUpdateView(UpdateView):
    model = Article
    fields = ['title', 'content']  # Здесь перечислите поля, которые вы хотите включить в форму редактирования статьи
    template_name = 'news/article_form.html'
    success_url = reverse_lazy('news_list')  # Перенаправление после успешного редактирования статьи

class ArticleDeleteView(DeleteView):
    model = Article
    success_url = reverse_lazy('news_list')  # Перенаправление после успешного удаления статьи
    template_name = 'news/article_confirm_delete.html'