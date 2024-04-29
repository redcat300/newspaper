# Импорт
from django.contrib.auth.models import User
from your_app.models import Author, Category, Post, PostCategory, Comment

# Создание двух пользователей
user1 = User.objects.create_user(username='user1')
user2 = User.objects.create_user(username='user2')

# Создание двух объектов модели Author, связанных с пользователями
author1 = Author.objects.create(user=user1)
author2 = Author.objects.create(user=user2)

# Добавление 4 категорий в модель Category
category1 = Category.objects.create(name='Спорт')
category2 = Category.objects.create(name='Политика')
category3 = Category.objects.create(name='Наука')
category4 = Category.objects.create(name='Технологии')

# Добавление 2 статей и 1 новости
post1 = Post.objects.create(author=author1, post_type='article', title='Статья 1', content='Текст статьи 1', rating=0)
post2 = Post.objects.create(author=author2, post_type='article', title='Статья 2', content='Текст статьи 2', rating=0)
post3 = Post.objects.create(author=author1, post_type='news', title='Новость 1', content='Текст новости 1', rating=0)

# Присвоение категорий статьям и новости
post1.categories.add(category1, category2)
post2.categories.add(category3, category4)
post3.categories.add(category1, category3)

# Создание 4 комментариев к разным объектам   Post
comment1 = Comment.objects.create(post=post1, user=user1, text='Комментарий к статье 1', rating=0)
comment2 = Comment.objects.create(post=post2, user=user2, text='Комментарий к статье 2', rating=0)
comment3 = Comment.objects.create(post=post1, user=user2, text='Второй комментарий к статье 1', rating=0)
comment4 = Comment.objects.create(post=post3, user=user1, text='Комментарий к новости 1', rating=0)

# Применение функций like() и dislike() к статьям/новостям и комментариям
post1.like()
post2.dislike()
comment1.like()
comment2.dislike()

# Обновление рейтингов пользователей
author1.update_rating()
author2.update_rating()

# Вывод username и рейтинга лучшего пользователя
best_author = Author.objects.order_by('-rating').first()
print("Лучший пользователь:", best_author.user.username)
print("Рейтинг:", best_author.rating)

# Вывод даты добавления, username автора, рейтинга, заголовка и превью лучшей статьи
best_post = Post.objects.order_by('-rating').first()
print("Дата добавления:", best_post.created_at)
print("Автор:", best_post.author.user.username)
print("Рейтинг:", best_post.rating)
print("Заголовок:", best_post.title)
print("Превью:", best_post.preview())

# Вывод всех комментариев к этой статье
comments_to_best_post = Comment.objects.filter(post=best_post)
for comment in comments_to_best_post:
    print("Дата:", comment.created_at)
    print("Пользователь:", comment.user.username)
    print("Рейтинг:", comment.rating)
    print("Текст:", comment.text)
