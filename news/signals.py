from django.core.exceptions import PermissionDenied
from django.db.models.signals import m2m_changed, pre_save, post_save
from django.dispatch import receiver
from django.core.cache import cache

from news.models import Post, Category
from news.utils import send_sub_emails
from django.utils import timezone


@receiver(m2m_changed, sender=Post.category.through)
def notify_subscribers(sender, instance, action, **kwargs):
    if action == 'post_add':
        send_sub_emails(instance)


@receiver(pre_save, sender=Post)
def limit_posts_per_day(sender, instance, **kwargs):
    author = instance.author
    posts_today = Post.objects.filter(author=author, publish_time__date=timezone.now().date()).count()
    if posts_today >= 3:
        # На странице ошибки выводим заголовок и текст поста чтобы пользователь мог его сохранить.
        raise PermissionDenied('Превышен лимит на количество постов в день.<br>'
                               'Попробуйте опубликовать новый пост завтра или удалите один из трех ваших последних постов<br><br>'
                               f'Вот заголовок и текст вашего поста:<br>Заголовок: {instance.title}<br>Текст:<br>{instance.text}')
