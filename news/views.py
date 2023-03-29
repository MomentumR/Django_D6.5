from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils import timezone

from .models import *
from .filter import PostFilter
from .utils import get_filter_params
from .forms import *


menu = [{'title': 'Home', 'url_name': 'home'},
        {'title': 'Search', 'url_name': 'search'},
        {'title': 'Add post', 'url_name': 'add'},
        {'title': 'Add category', 'url_name': 'add_category'},
        {'title': 'About Us', 'url_name': ''},
        {'title': 'Contact Us', 'url_name': ''},
        {'title': 'Login', 'url_name': 'account_login'},
        {'title': 'Logout', 'url_name': 'account_logout'},]


class News(ListView):
    model = Post
    template_name = 'news/postList.html'
    context_object_name = 'news'
    queryset = Post.objects.order_by('-publish_time')
    extra_context = {'menu': menu}
    paginate_by = 10


class PostView(DetailView):
    model = Post
    template_name = 'news/postDetails.html'
    context_object_name = 'post'
    extra_context = {'menu': menu}


class PostUpdateView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    permission_required = ('news.change_post',)
    model = Post
    template_name = 'news/postAdd.html'
    form_class = PostForm
    extra_context = {'menu': menu}

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        # Проверка является ли user автором поста
        if post.author.author_user != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    permission_required = 'news.delete_post'
    model = Post
    context_object_name = 'post'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        #Проверка является ли user автором поста
        if post.author.author_user != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        #Делаем редирект на ту же страницу из которой было вызвано представление
        referer = self.request.META.get('HTTP_REFERER')
        if referer and referer != self.request.build_absolute_uri():
            return referer

        return super().get_success_url()


class SearchPost(ListView):
    model = Post
    template_name = 'news/postSearch.html'
    context_object_name = 'search'
    paginate_by = 4

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = menu
        context['filter'] = PostFilter(self.request.GET, queryset=self.get_queryset())
        context['filter_params'] = get_filter_params(self.request)

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        return PostFilter(self.request.GET, queryset=queryset).qs


class AddPost(PermissionRequiredMixin, LoginRequiredMixin, CreateView):
    permission_required = ('news.add_post',)

    form_class = PostForm
    template_name = 'news/postAdd.html'
    extra_context = {'menu': menu}
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = self.request.user
        author = get_object_or_404(Author, author_user=user)
        form.instance.author = author
        response = super().form_valid(form)

        return response

@login_required
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
        data = {
            'success': True,
            'comment_id': comment.pk,
            'comment_text': comment.text,
            'comment_publish_time': comment.publish_time.astimezone(timezone.get_default_timezone()).strftime('%d.%m.%Y %H:%M:%S'),
            'comment_user': comment.user.username,
            'comment_delete_url': comment.get_delete_url()
        }
    else:
        data = {
            'success': False,
            'errors': form.errors,
        }
    return JsonResponse(data)

@login_required
@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.user != comment.user:
        raise PermissionDenied('Удалять комментарии могут только их авторы (или админ)')
    comment.delete()
    return JsonResponse({'deleted': True})

@login_required
def upgrade_to_author(request):
    user = request.user
    common_group = Group.objects.get(name='common')
    authors_group = Group.objects.get(name='authors')

    #Если юзер не в группе common (например, он зашел через Google), то добавляем его сразу в обе группы
    if not request.user.groups.filter(name='common').exists():
        common_group.user_set.add(user)
    if not request.user.groups.filter(name='authors').exists():
        Author.objects.create(author_user=user)
        authors_group.user_set.add(user)

    return redirect('home')

@login_required
@require_POST
def remove_subscriber(request, pk):
    category = Category.objects.get(pk=pk)
    user = request.user
    category.subscribers.remove(user)
    data = {
        'success': True,
        'url': category.subscribe()
    }
    return JsonResponse(data)

@login_required
@require_POST
def add_subscriber(request, pk):
    category = Category.objects.get(pk=pk)
    user = request.user
    #Так как в промежуточной модели нет полей кроме category и user можно проигнорировать это предупреждение.
    #Если бы поля были, тогда нужно было передавать эти поля и их значения в through_defaults в дополнении к category и user через менеджер модели CategorySubscriber
    #category.subscribers.through.objects.create(user=user, category=category, **through_defaults)
    category.subscribers.add(user)
    data = {
        'success': True,
        'url': category.unsubscribe()
    }
    return JsonResponse(data)

@permission_required('news.add_category', raise_exception=True)
@login_required
@require_POST
def add_category(request):
    name = request.POST.get('name')
    category = Category.objects.create(name=name)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def permission_denied_view(request, exception=None):
    context = {'message': str(exception), 'menu': menu}
    return render(request, '403.html', context=context, status=403)

def page_not_found_view(request, exception=None):
    context = {'message': str(exception), 'menu': menu}
    return render(request, '404.html', context=context, status=404)