from django.urls import path
from . import views

urlpatterns = [
    path('', views.fetch_posts, name='blogs_home'),
]