from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse_lazy



class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    def update_rating(self):
        posts_rating = sum(post.rating * 3 for post in self.post_set.all())
        comments_rating = sum(comment.rating for comment in Comment.objects.filter(user=self.user))
        comments_to_posts_rating = sum(comment.rating for post in self.post_set.all() for comment in post.comment_set.all())
        self.rating = posts_rating + comments_rating + comments_to_posts_rating
        self.save()

    def can_publish(self):
        today = timezone.now().date()
        posts_count = Post.objects.filter(author=self, created_at__date=today).count()
        return posts_count < 3

    def add_to_authors_group(self):
        authors_group, _ = Group.objects.get_or_create(name='authors')
        self.user.groups.add(authors_group)
        self.assign_post_permissions()

    def remove_from_authors_group(self):
        authors_group, _ = Group.objects.get_or_create(name='authors')
        self.user.groups.remove(authors_group)

    def assign_post_permissions(self):
        # Получаем тип содержимого для модели Post
        content_type = ContentType.objects.get_for_model(Post)
        # Определяем разрешения для создания и изменения объектов Post
        create_permission = Permission.objects.get(codename='add_post', content_type=content_type)
        change_permission = Permission.objects.get(codename='change_post', content_type=content_type)
        # Получаем или создаем группу "authors"
        authors_group, _ = Group.objects.get_or_create(name='authors')
        # Назначаем разрешения группе "authors"
        authors_group.permissions.add(create_permission, change_permission)

    def __str__(self):
        return f'{self.user.username}: {self.rating}'

# Создание группы common при создании нового пользователя
@receiver(models.signals.post_save, sender=User)
def add_to_common_group(sender, instance, created, **kwargs):
    if created:
        common_group, _ = Group.objects.get_or_create(name='common')
        instance.groups.add(common_group)

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subscribers = models.ManyToManyField(User, related_name='subscribed_categories', blank=True)

    def __str__(self):
        return self.name.title()


class Post(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    POST_TYPE_CHOICES = [
        ('article', 'Статья'),
        ('news', 'Новость'),
    ]
    post_type = models.CharField(max_length=7, choices=POST_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(Category, through='PostCategory')
    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.IntegerField(default=0)

    def preview(self):
        return self.content[:124] + '...' if len(self.content) > 124 else self.content

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def can_edit(self, user):
        return user == self.author.user

    def __str__(self):
        return self.title

class PostCategory(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

@receiver(post_save, sender=Comment)
def update_author_rating(sender, instance, created, **kwargs):
    if created:
        instance.author.update_rating()

class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(Category, related_name='articles', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.send_notification()

    def send_notification(self):
        category = self.category
        subscribers = category.subscribers.all()
        for subscriber in subscribers:
            subject = f"Новая статья в категории {category.name}"
            message = render_to_string('email/new_article_notification.html', {
                'subscriber': subscriber,
                'article': self,
                'article_url': reverse_lazy('news_detail', kwargs={'pk': self.pk}),
            })
            send_mail(subject, message, 'your_email@example.com', [subscriber.email])
    class Meta:
        managed = False
        db_table = 'news_post'

    def __str__(self):
        return self.title

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Добавьте нужные вам поля профиля
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    # И другие поля, которые вы хотите хранить в профиле пользователя

    def __str__(self):
        return self.user.username + ' Profile'


