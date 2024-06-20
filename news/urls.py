from django.urls import path, include
from django.contrib.auth import views as auth_views
from allauth.account.views import SignupView
from news.views import NewsListView
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('search/', views.news_search, name='news_search'),
    path('create/', views.NewsCreateView.as_view(), name='news_create'),
    path('<int:pk>/edit/', views.NewsUpdateView.as_view(), name='news_edit'),
    path('<int:pk>/delete/', views.NewsDeleteView.as_view(), name='news_delete'),
    path('articles/create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('articles/<int:pk>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
    path('articles/<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('become_author/', views.AuthorRequestView.as_view(), name='become_author'),
    path('profile/', views.profile, name='profile'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:category_id>/subscribe/', views.subscribe_category, name='subscribe_category'),
    path('subscribed_categories/', views.subscribed_categories, name='subscribed_categories'),
    path('categories/<int:category_id>/unsubscribe/', views.unsubscribe_category, name='unsubscribe_category'),
]
