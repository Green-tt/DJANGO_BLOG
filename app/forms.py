from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Post, Comment, UserProfile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'row': 5}),
            'image': forms.FileInput(attrs={'class': 'form-control-file'}),

        }

        labels = {
            'title': "Заголовок",
            'content': "Содержание",
            'image': 'Изображение (опционально)'
        }


class CommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control h', 'row': 3, 'placeholder': 'Напишите коментарий...'}),
        }

        labels = {
            'content': '',
        }

    def __init__(self, *args, **kwargs):
        self.post_id = kwargs.pop('post_id', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        if not self.post_id:
            raise ValueError("post_id br provided to CommentForm")
        comment = super().save(commit=False)
        comment.post_id = self.post_id
        if self.cleaned_data.get('parent_id'):
            parent_id = self.cleaned_data['parent_id']
            try:
                comment.parent = Comment.objects.get(id=parent_id, post_id=self.post_id)
            except Comment.DoesNoExist:
                comment.parent = None

        if commit:
            comment.save()
        return comment


class UserProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['avatar', 'birth_date', 'first_name', 'last_name', 'bio']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.username

    def save(self, commit=True):
        user_profile = super().save(commit=False)
        user = user_profile.user

        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            user_profile.save()
        return user_profile

