from django.views.generic import CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.http import Http404
from django.core.exceptions import PermissionDenied
from .models import Post, Article, Profile
from django.views import generic
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import FormView
from django.urls import reverse_lazy
from .forms import AuthorRequestForm
from django.contrib.auth.decorators import login_required

class AuthorRequestView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Получаем группу 'authors'
            authors_group = Group.objects.get(name='authors')
            # Проверяем, входит ли пользователь в группу 'authors'
            if authors_group.user_set.filter(id=request.user.id).exists():
                # Пользователь уже является автором
                return redirect('profile')
            else:
                # Добавляем пользователя в группу 'authors'
                authors_group.user_set.add(request.user)
                return redirect('profile')
        return redirect('login')

    def form_valid(self, form):
        # Отправляем уведомление администратору о запросе на статус автора
        reason = form.cleaned_data['reason']
        send_mail(
            'Author Request',
            f'A user has requested author status. Reason: {reason}',
            'from@example.com',
            ['admin@example.com'],
            fail_silently=False,
        )
        return super().form_valid(form)

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

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

class NewsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']
    template_name = 'news/news_update.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user.groups.filter(name='authors').exists() or self.request.user == post.author

class NewsDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('news_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user.groups.filter(name='authors').exists() or self.request.user == post.author

class ArticleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Article
    fields = ['title', 'content']
    template_name = 'news/article_form.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        return self.request.user.groups.filter(name='authors').exists()

class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    fields = ['title', 'content']
    template_name = 'news/article_form.html'
    success_url = reverse_lazy('news_list')

    def test_func(self):
        article = self.get_object()
        return self.request.user.groups.filter(name='authors').exists() or self.request.user == article.author

class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('news_list')
    template_name = 'news/article_confirm_delete.html'

    def test_func(self):
        article = self.get_object()
        return self.request.user.groups.filter(name='authors').exists() or self.request.user == article.author

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

class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

@login_required
def profile(request):
    return render(request, 'profile.html')

class AuthorRequestView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            author_group = Group.objects.get(name='authors')
            request.user.groups.add(author_group)
            return redirect('profile')
        return redirect('login')