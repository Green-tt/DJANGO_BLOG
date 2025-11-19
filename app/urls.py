from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('my-posts/', views.my_posts, name='my_posts'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('post/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/create', views.post_create, name='post_create'),
    path('post/<int:post_id>/delete', views.post_delete, name='post_delete'),
    path('post/<int:post_id>/like', views.toggle_like, name='toggle_like'),
    path('post/<int:post_id>/comment', views.add_comment, name='add_comment'),
    path('favorites/', views.favorites, name='favorites'),
    path('post/<int:post_id>/toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('profile', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
]
