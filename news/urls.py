from django.urls import path
from django.views.generic import TemplateView

from .views import *

urlpatterns = [
    path('', News.as_view(), name='home'),
    path('<int:pk>/', PostView.as_view(), name='post'),
    path('search/', SearchPost.as_view(), name='search'),
    path('add/', AddPost.as_view(), name='add'),
    path('<int:pk>/edit/', PostUpdateView.as_view(), name='post_update'),
    path('<int:pk>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path('upgrade/', upgrade_to_author, name='upgrade'),
    path('subscribe/<int:pk>/', add_subscriber, name='subscribe'),
    path('unsubscribe/<int:pk>/', remove_subscriber, name='unsubscribe'),
    path('add_category/', add_category, name='add_category'),
    path('<int:pk>/add_comment/', add_comment, name='add_comment'),
    path('delete_comment/<int:pk>/', delete_comment, name='delete_comment'),
]
