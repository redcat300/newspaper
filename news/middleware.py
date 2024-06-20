# news/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/':
            if request.user.is_authenticated:

                if request.path != reverse('news_list'):
                    return redirect(reverse('news_list'))
            else:

                if request.path != reverse('account_login'):
                    return redirect(reverse('account_login'))
        return self.get_response(request)
