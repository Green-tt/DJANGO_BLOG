from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, request
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Q
from .forms import UserRegisterForm, UserLoginForm, PostForm, CommentForm, UserProfileForm, MessageForm
from .models import UserProfile, Post, Like, Comment, Favorite, Message


# Create your views here.
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Аккаунт {username} успешно создан")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, "app/register.html", {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Неправильное имя пользователя или пароль!")

    else:
        form = UserLoginForm()
    return render(request, 'app/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


def home(request):
    # Получаем все объекты Post из базы данных
    posts = Post.objects.all()

    # Передаем список posts в шаблон home.html через контекст
    context = {
        'posts': posts,  # 'posts' - это имя переменной, которое будет доступно в шаблоне
    }
    return render(request, 'app/home.html', context)


@login_required
def post_detail(request, post_id):
    # Получаем конкретный пост по ID или возвращаем 404, если не найден
    post = get_object_or_404(Post, id=post_id)

    user_liked = False
    if request.user.is_authenticated:
        post.user_liked = post.likes.filter(user=request.user).exists()
    user_favorite = post.favorite_by.filter(user=request.user).exists()
    all_comments = Comment.objects.filter(post=post).select_related("author").prefetch_related(
        "comment_likes").order_by("create_at")
    comment_tree = build_comment_tree(all_comments)

    comment_form = CommentForm(post_id=post_id)

    # Можно передать дополнительные данные, например, комментарии
    return render(request, 'app/post_detail.html', {
        'post': post,
        'user_liked': user_liked,
        'comment_form': comment_form,
        "comment_tree": comment_tree,
        'user_favorite ': user_favorite,
    })


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Пост успешно создан")
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'app/post_create.html', {'form': form})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        messages.error(request, "У вас нет прав для удаления этого поста")
        return redirect('home')

    if request.method == "POST":
        post_title = post.title
        post.delete()
        messages.success(request, f"Пост {post_title} успешно удален")
        return redirect('home')

    messages.warning(request, "Для удаления поста используйте кнопку на странице поста")
    return redirect('post_detail', post_id=post.id)


@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like_obj, created = Like.objects.get_or_create(user=request.user, post=post)

    if created:
        action = 'Liked'
    else:
        like_obj.delete()
        action = 'unliked'
    messages.info(request, f"Вы {action} пост {post.title}.")

    next_url = request.META.get('HTTP_REFERER', reverse('home'))
    return HttpResponseRedirect(next_url)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        messages.error(request, "У вас нет прав для редактирования этого поста")
        return redirect('home')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, f"Пост {post.title} успешно обновлен")
            return redirect("post_detail", post_id=post_id)

    else:
        form = PostForm(instance=post)
    return render(request, 'app/post_edit.html', {'form': form, 'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, post_id=post_id)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, f"Комментарий добавлен")
            return redirect('post_detail', post_id=post.id)  # Исправлено: post_id вместо post_id.id
    return redirect('post_detail', post_id=post.id)  # Исправлено: post_id вместо post_id.id


# Построение дерева коментариев
def build_comment_tree(comments):
    comment_dict = {}
    root_comments = []

    for comment in comments:
        comment_dict[comment.id] = {'comment': comment, 'replies': []}

    for item in comment_dict.values():
        comment_obj = item['comment']
        if comment_obj.parent_id:
            parent_item = comment_dict.get(comment_obj.parent_id)
            if parent_item:
                parent_item['replies'].append(item)
        else:
            root_comments.append(item)
    return root_comments


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=user)
    return render(request, 'app/profile_view.html', {'profile_user': user, 'profile': profile})


@login_required
def profile_edit(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обнавлен")
            return redirect('profile_view', username=request.user.username)

    else:
        form = UserProfileForm(instance=profile, user=request.user)
    return render(request, 'app/profile_edit.html', {"form": form})


@login_required
def my_posts(request):
    # Получаем только посты текущего пользователя
    posts = Post.objects.filter(author=request.user).select_related('author__profile').prefetch_related('likes',
                                                                                                        'comments')

    # Передаем список posts в шаблон my_posts.html
    context = {
        'posts': posts,
    }
    return render(request, 'app/my_posts.html', context)


@login_required
def favorites(request):
    favorite_entries = Favorite.objects.filter(user=request.user).select_related(
        'post__author__profile').prefeth_related('post__likes', 'post__comments')
    posts = [entry.post for entry in favorite_entries]
    return render(request, 'app/favorites.html', {'posts': posts})


@login_required
def toggle_favorite(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user:
        messages.error(request, "Нельзя добавить в избранное свой пост")
        next_url = request.META.get("HTTP_REFERER", reverse('home'))
        return HttpResponseRedirect(next_url)
    favorite_obj, created = Favorite.objects.get_or_create(user=request.user, post=post)

    action = "добавлен в избранное"
    if not created:
        favorite_obj.delete()
        action = "удален из"
    messages.info(request, f'Пост"{post.title} {action}"')
    next_url = request.META.get("HTTP_REFERER", reverse('home'))
    return HttpResponseRedirect(next_url)

@login_required
def messages_list(request, recipient_id=None):
    # Получаем список всех собеседников (людей, с которыми была переписка)
    sent_by_me = Message.objects.filter(sender=request.user).values_list('recipient_id', flat=True)
    sent_to_me = Message.objects.filter(recipient=request.user).values_list('sender_id', flat=True)
    all_contact_ids = set(list(sent_by_me) + list(sent_to_me))
    contacts = User.objects.filter(id__in=all_contact_ids).select_related('profile').distinct()
    # Подсчитываем непрочитанные сообщения *для каждого контакта*
    contacts_with_unread = []
    for contact in contacts:
        unread_count = Message.objects.filter(
            sender=contact,      # Сообщение отправлено *от* этого контакта
            recipient=request.user, # ... и адресовано *текущему пользователю*
            is_read=False        # ... и *ещё не прочитано*
        ).count()
        contacts_with_unread.append({
            'contact': contact,
            'unread_count': unread_count
        })
    # Сортировка контактов по времени последнего сообщения
    def get_last_message_time(contact):
        last_msg = Message.objects.filter(
            (Q(sender=request.user) & Q(recipient=contact)) |
            (Q(sender=contact) & Q(recipient=request.user))
        ).order_by('-timestamp').first()
        return last_msg.timestamp if last_msg else None
    sorted_contacts_with_unread = sorted(contacts_with_unread, key=lambda x: get_last_message_time(x['contact']), reverse=True)
    selected_conversation = None
    selected_recipient = None
    if recipient_id:
        selected_recipient = get_object_or_404(User, id=recipient_id)
        if selected_recipient.id in all_contact_ids:
            # Отмечаем сообщения от selected_recipient как прочитанные
            Message.objects.filter(recipient=request.user, sender=selected_recipient, is_read=False).update(is_read=True)
            selected_conversation = Message.objects.filter(
                (Q(sender=request.user) & Q(recipient=selected_recipient)) |
                (Q(sender=selected_recipient) & Q(recipient=request.user))
            ).select_related('sender__profile').order_by('timestamp')

    unread_count_total = Message.objects.filter(recipient=request.user, is_read=False).count()
    return render(request, 'app/messages_list.html', {
        'contacts_with_unread': sorted_contacts_with_unread,  # Передаём список словарей
        'selected_conversation': selected_conversation,
        'selected_recipient': selected_recipient,
        'unread_count': unread_count_total,
    })

@login_required
def send_message(request, recipient_id):
    recipient = get_object_or_404(User, id=recipient_id)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            messages.success(request, f'Сообщение для {recipient.username} отправлено.')

            # Редиректим на страницу с перепиской
            return redirect('messages_list', recipient_id=recipient.id)
    else:
        form = MessageForm()

    if request.method == 'GET':
        return redirect('messages_list', recipient_id=recipient.id)
    return render(request, 'app/send_message.html', {'form': form, 'recipient': recipient})
