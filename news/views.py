from django.shortcuts import render, get_object_or_404
from .models import Category, Post
from django.http import Http404

def news_list(request):
    news = Post.objects.order_by('-created_at')
    return render(request, 'news/news_list.html', {'news': news})

def news_detail(request, id):
    news_item = get_object_or_404(Post, id=id)
    return render(request, 'news/news_detail.html', {'news_item': news_item})


