from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
# pyrefly: ignore [missing-import]
from .models import Post, Comment, Tag


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        error_messages={'required': 'Email không được để trống.'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Mật khẩu'
    )
    interests = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Chọn thẻ nội dung bạn quan tâm'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_password(self):
        # Áp dụng AUTH_PASSWORD_VALIDATORS trong settings (độ dài, giống username, quá phổ biến, toàn số)
        password = self.cleaned_data['password']
        user = User(
            username=self.cleaned_data.get('username'),
            email=self.cleaned_data.get('email'),
        )
        validate_password(password, user)
        return password


class PostForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Thẻ bài viết'
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'tags']


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['content']
        labels = {
            'content': 'Nội dung bình luận'
        }
