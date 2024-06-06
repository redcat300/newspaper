from django.core import mail
from django.test import TestCase

class EmailTest(TestCase):
    def test_send_email(self):
        # Предположим, у вас есть код, который отправляет электронное письмо
        # Здесь вызовите этот код
        send_email_function()

        # Проверяем, что было отправлено одно письмо
        self.assertEqual(len(mail.outbox), 1)

        # Проверяем тему письма
        self.assertEqual(mail.outbox[0].subject, 'Тема вашего письма')

        # Проверяем адресата
        self.assertEqual(mail.outbox[0].to, ['recipient@example.com'])

        # Проверяем содержимое письма
        self.assertIn('Текст вашего письма', mail.outbox[0].body)
