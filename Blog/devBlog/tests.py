from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import normalize_phone
from .models import Post, UserProfile, Follow, Tag
from .views import people_you_may_know


class PostOwnershipTests(TestCase):
    """Chỉ tác giả mới được sửa / xóa bài của mình."""

    def setUp(self):
        self.author = User.objects.create_user('tacgia', password='Hoa-Sen!2026', first_name='Tác', last_name='Giả')
        self.other = User.objects.create_user('nguoikhac', password='Hoa-Sen!2026', first_name='Người', last_name='Khác')
        self.post = Post.objects.create(content='Nội dung gốc', author=self.author)
        self.edit_url = reverse('edit_post', args=[self.post.id])
        self.delete_url = reverse('delete_post', args=[self.post.id])
        self.detail_url = reverse('post_detail', args=[self.post.id])

    def test_nguoi_khac_khong_sua_duoc_bai(self):
        self.client.force_login(self.other)

        response = self.client.get(self.edit_url)
        self.assertRedirects(response, self.detail_url)

        response = self.client.post(self.edit_url, {'content': 'Bị sửa'})
        self.assertRedirects(response, self.detail_url)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'Nội dung gốc')

    def test_nguoi_khac_khong_xoa_duoc_bai(self):
        self.client.force_login(self.other)

        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.detail_url)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_chua_dang_nhap_khong_sua_xoa_duoc(self):
        self.client.post(self.edit_url, {'content': 'Bị sửa'})
        self.client.post(self.delete_url)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'Nội dung gốc')

    def test_tac_gia_sua_va_xoa_duoc_bai(self):
        self.client.force_login(self.author)

        response = self.client.post(self.edit_url, {'content': 'Nội dung mới. Câu hai.'})
        self.assertRedirects(response, self.detail_url)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'Nội dung mới. Câu hai.')
        self.assertEqual(self.post.title, 'Nội dung mới.')   # tiêu đề tự lấy từ câu đầu

        response = self.client.post(self.delete_url)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())


class AccountTests(TestCase):
    """Đăng ký bằng Gmail + số điện thoại, đăng nhập bằng một trong hai, rồi bắt buộc điền Họ + Tên."""
    PASSWORD = 'Hoa-Sen!2026'

    def register(self, email='minh@gmail.com', phone='0912 345 678', password=PASSWORD):
        return self.client.post(reverse('register'), {'email': email, 'phone': phone, 'password': password})

    def test_chuan_hoa_so_dien_thoai(self):
        self.assertEqual(normalize_phone('0912 345 678'), '0912345678')
        self.assertEqual(normalize_phone('+84 912.345.678'), '0912345678')
        self.assertEqual(normalize_phone('84912345678'), '0912345678')
        self.assertIsNone(normalize_phone('12345'))
        self.assertIsNone(normalize_phone('0212345678'))   # đầu số không phải di động
        self.assertIsNone(normalize_phone('abc'))

    def test_dang_ky_roi_dien_ten(self):
        response = self.register(email='Minh@Gmail.com')
        self.assertRedirects(response, reverse('complete_profile'))
        user = User.objects.get(email='minh@gmail.com')   # email lưu chữ thường
        self.assertEqual(user.profile.phone, '0912345678')

        # Chưa điền tên thì vào đâu cũng bị đưa về bước giới thiệu
        self.assertRedirects(self.client.get(reverse('home')), reverse('complete_profile'))

        response = self.client.post(reverse('complete_profile'), {'last_name': ' Nguyễn  Văn ', 'first_name': 'Minh'})
        self.assertRedirects(response, reverse('home'))
        user.refresh_from_db()
        self.assertEqual((user.last_name, user.first_name), ('Nguyễn Văn', 'Minh'))
        self.assertContains(self.client.get(reverse('home')), 'Nguyễn Văn Minh')

    def test_khong_cho_trung_email_hoac_so(self):
        self.register()
        self.client.logout()
        response = self.register(email='MINH@gmail.com', phone='0987654321')
        self.assertContains(response, 'Gmail này đã có tài khoản')
        response = self.register(email='khac@gmail.com', phone='+84912345678')
        self.assertContains(response, 'Số điện thoại này đã có tài khoản')
        self.assertEqual(User.objects.count(), 1)

    def test_loi_mat_khau_bang_tieng_viet(self):
        response = self.register(password='123')
        self.assertContains(response, 'Mật khẩu quá ngắn')
        self.assertContains(response, 'không được toàn là số')

    def test_so_sai_dinh_dang(self):
        response = self.register(phone='12345')
        self.assertContains(response, 'Số điện thoại chưa đúng')
        self.assertFalse(User.objects.exists())

    def test_dang_nhap_bang_email_hoac_so(self):
        self.register()
        self.client.logout()
        for ident in ('minh@gmail.com', 'MINH@GMAIL.COM', '0912345678', '+84 912 345 678'):
            response = self.client.post(reverse('login'), {'ident': ident, 'password': self.PASSWORD})
            self.assertEqual(response.status_code, 302, ident)
            self.client.logout()
        response = self.client.post(reverse('login'), {'ident': '0912345678', 'password': 'sai-mat-khau'})
        self.assertContains(response, 'Sai Gmail / số điện thoại hoặc mật khẩu')

    def test_tai_khoan_cu_dang_nhap_bang_email(self):
        # Tài khoản tạo trước khi đổi cách đăng ký: có username + email, chưa có số và tên
        User.objects.create_user('Hoaiduc', email='duc@gmail.com', password=self.PASSWORD)
        response = self.client.post(reverse('login'), {'ident': 'duc@gmail.com', 'password': self.PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(self.client.get(reverse('home')), reverse('complete_profile'))
        # username cũ không còn dùng để đăng nhập (trừ quản trị viên vào /admin/)
        self.client.logout()
        response = self.client.post(reverse('login'), {'ident': 'Hoaiduc', 'password': self.PASSWORD})
        self.assertEqual(response.status_code, 200)

    def test_trang_ca_nhan_theo_ma_so(self):
        self.register()
        self.client.post(reverse('complete_profile'), {'last_name': 'Trần', 'first_name': 'An'})
        user = User.objects.get()
        response = self.client.get(reverse('user_profile', args=[user.id]))
        self.assertContains(response, 'Trần An')


class PeopleYouMayKnowTests(TestCase):
    def make(self, name):
        u = User.objects.create_user(name, password='x', first_name=name, last_name='Lê')
        UserProfile.objects.create(user=u)
        return u

    def test_thu_tu_goi_y(self):
        me, ban, theo_doi_toi, ban_chung, cung_chu_de, viet_nhieu, chua_ten = (
            self.make(n) for n in ('me', 'ban', 'theodoitoi', 'banchung', 'cungchude', 'vietnhieu', 'chuaten'))
        chua_ten.first_name = ''
        chua_ten.save()
        Follow.objects.create(follower=me, following=ban)              # đã theo dõi -> không gợi ý
        Follow.objects.create(follower=theo_doi_toi, following=me)     # đang theo dõi mình
        Follow.objects.create(follower=ban, following=ban_chung)       # bạn của bạn
        tag = Tag.objects.create(name='Du lịch')
        me.profile.interests.add(tag)
        cung_chu_de.profile.interests.add(tag)
        Post.objects.create(author=viet_nhieu, content='Một bài.')

        names = [u.first_name for u in people_you_may_know(me)]
        self.assertEqual(names, ['theodoitoi', 'banchung', 'cungchude', 'vietnhieu'])
