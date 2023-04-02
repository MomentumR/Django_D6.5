from django import forms
from .models import Post, Author, Comment
from allauth.account.forms import SignupForm, LoginForm
from django.contrib.auth.models import Group, User


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['type', 'category', 'title', 'text']
        labels = {
            'type': 'Тип поста',
            'category': 'Категории',
            'title': 'Название',
            'text': 'Текст'
        }

        widgets = {
            'type': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'title': forms.TextInput(attrs={'class': 'form-control',
                                            'placeholder': 'Введите название'}),
            'text': forms.Textarea(attrs={'class': 'form-control',
                                          'placeholder': 'Введите текст'}),
            'category': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 2}),
        }

class CustomSignupForm(SignupForm):
    become_author = forms.BooleanField(label='Стать автором', required=False,
                                       widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'type': 'checkbox'}))

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        common_group = Group.objects.get(name='common')
        common_group.user_set.add(user)
        if self.cleaned_data['become_author']:
            authors_group = Group.objects.get(name='authors')
            authors_group.user_set.add(user)
            Author.objects.create(author_user=user)
        return user


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']






