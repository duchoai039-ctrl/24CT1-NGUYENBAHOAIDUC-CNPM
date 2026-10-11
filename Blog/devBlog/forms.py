import re
import uuid

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
# pyrefly: ignore [missing-import]
from .models import Post, Comment, Tag, UserProfile


def normalize_phone(value):
    """Số di động Việt Nam về dạng 0xxxxxxxxx; sai định dạng thì trả None.
    Nhận cả dấu cách, chấm, gạch và đầu +84 / 84."""
    digits = re.sub(r'[\s.\-()]', '', value or '')
    if digits.startswith('+84'):
        digits = '0' + digits[3:]
    elif digits.startswith('84') and len(digits) == 11:
        digits = '0' + digits[2:]
    return digits if re.fullmatch(r'0[35789]\d{8}', digits) else None


PASSWORD_ERRORS = {
    'password_too_short': 'Mật khẩu quá ngắn, cần ít nhất 8 ký tự.',
    'password_too_common': 'Mật khẩu này quá phổ biến, dễ bị đoán.',
    'password_entirely_numeric': 'Mật khẩu không được toàn là số.',
    'password_too_similar': 'Mật khẩu quá giống Gmail.',
}


class RegisterForm(forms.Form):
    email = forms.EmailField(label='Gmail', error_messages={
        'required': 'Hãy nhập Gmail.', 'invalid': 'Gmail chưa đúng định dạng.',
    })
    phone = forms.CharField(label='Số điện thoại', max_length=20, error_messages={
        'required': 'Hãy nhập số điện thoại.',
    })
    password = forms.CharField(widget=forms.PasswordInput, label='Mật khẩu', error_messages={
        'required': 'Hãy nhập mật khẩu.',
    })

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Gmail này đã có tài khoản. Hãy đăng nhập.')
        return email

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data['phone'])
        if not phone:
            raise forms.ValidationError('Số điện thoại chưa đúng. Ví dụ: 0912 345 678.')
        if UserProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Số điện thoại này đã có tài khoản. Hãy đăng nhập.')
        return phone

    def clean_password(self):
        # Áp dụng AUTH_PASSWORD_VALIDATORS trong settings (độ dài, giống email, quá phổ biến, toàn số)
        password = self.cleaned_data['password']
        try:
            validate_password(password, User(email=self.data.get('email', '')))
        except forms.ValidationError as e:
            # Bản dịch tiếng Việt của Django còn thiếu vài câu: tự viết theo mã lỗi
            raise forms.ValidationError([PASSWORD_ERRORS.get(err.code, err) for err in e.error_list])
        return password

    def save(self):
        # Không còn tên đăng nhập: username của Django chỉ là mã ẩn, không ai thấy hay gõ.
        user = User.objects.create_user(
            username='u' + uuid.uuid4().hex[:12],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
        )
        UserProfile.objects.create(user=user, phone=self.cleaned_data['phone'])
        return user


class IntroForm(forms.Form):
    """Bước sau đăng ký: "Mọi người có thể biết đến bạn thông qua" Họ + Tên, kèm chủ đề quan tâm."""
    last_name = forms.CharField(label='Họ', max_length=150, error_messages={'required': 'Hãy nhập họ.'})
    first_name = forms.CharField(label='Tên', max_length=150, error_messages={'required': 'Hãy nhập tên.'})
    interests = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Bạn quan tâm chủ đề nào?'
    )

    def clean_last_name(self):
        return ' '.join(self.cleaned_data['last_name'].split())   # bỏ khoảng trắng thừa

    def clean_first_name(self):
        return ' '.join(self.cleaned_data['first_name'].split())


class PostForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Thẻ bài viết'
    )

    class Meta:
        model = Post
        fields = ['content', 'image', 'tags']  # tiêu đề tự lấy từ nội dung (xem Post.save)

    MIN_TEXT_ONLY = 10   # bài không ảnh mà ngắn hơn thì người đọc không hiểu bạn muốn nói gì

    def clean(self):
        cleaned = super().clean()
        content = (cleaned.get('content') or '').strip()
        has_image = cleaned.get('image') or (self.instance.pk and self.instance.image)
        if content and not has_image and len(content) < self.MIN_TEXT_ONLY:
            self.add_error('content', f'Bài hơi ngắn. Viết ít nhất {self.MIN_TEXT_ONLY} ký tự, hoặc đăng kèm một ảnh.')
        return cleaned


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['content']
        labels = {
            'content': 'Nội dung bình luận'
        }
