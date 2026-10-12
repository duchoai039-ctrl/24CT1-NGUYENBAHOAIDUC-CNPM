from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .forms import normalize_phone
from .models import Post, Comment, UserProfile, Follow, Tag, Notification
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

        response = self.client.post(self.delete_url, follow=True)
        self.assertRedirects(response, reverse('home'))
        self.assertContains(response, 'Đã xóa bài.')
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_dang_bai_xong_ve_bai_vua_dang(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('create_post'), {'content': 'Bài mới. Câu hai.'}, follow=True)
        post = Post.objects.latest('id')
        self.assertRedirects(response, reverse('post_detail', args=[post.id]))
        self.assertContains(response, 'Đã đăng bài.')

    def test_bai_khong_anh_qua_ngan_bi_chan(self):
        self.client.force_login(self.author)
        before = Post.objects.count()
        response = self.client.post(reverse('create_post'), {'content': 'd'})
        self.assertContains(response, 'Bài hơi ngắn')
        self.assertEqual(Post.objects.count(), before)


class EditInfoTests(TestCase):
    """Đã có tên thì trang điền tên thành trang "Sửa thông tin", lưu xong về trang cá nhân."""

    def test_sua_thong_tin(self):
        user = User.objects.create_user('u1', password='Hoa-Sen!2026', first_name='An', last_name='Lê')
        self.client.force_login(user)
        self.assertContains(self.client.get(reverse('complete_profile')), 'Sửa thông tin')
        response = self.client.post(reverse('complete_profile'), {'last_name': 'Lê', 'first_name': 'Bình'}, follow=True)
        self.assertRedirects(response, reverse('profile'))
        self.assertContains(response, 'Đã lưu thông tin.')
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Bình')


class TopicSearchTests(TestCase):
    """Đang xem một chủ đề thì tìm kiếm chỉ lấy bài trong chủ đề đó."""

    def test_tim_trong_chu_de(self):
        user = User.objects.create_user('u1', password='Hoa-Sen!2026', first_name='An', last_name='Lê')
        travel = Tag.objects.get(name='Du lịch')   # có sẵn từ migration 0009
        inside = Post.objects.create(author=user, content='Đà Lạt mùa sương.')
        inside.tags.add(travel)
        Post.objects.create(author=user, content='Đà Lạt ngoài chủ đề.')
        self.client.force_login(user)

        everywhere = self.client.get(reverse('home'), {'q': 'Đà Lạt'})
        self.assertEqual(everywhere.context['posts'].paginator.count, 2)

        scoped = self.client.get(reverse('home'), {'q': 'Đà Lạt', 'tag': travel.id})
        self.assertEqual([p.id for p in scoped.context['posts']], [inside.id])
        self.assertContains(scoped, 'trong Du lịch')
        self.assertContains(scoped, 'class="side-nav"')   # menu trái có mặt khi đã đăng nhập

        # tag rác thì bỏ qua, không lỗi
        self.assertEqual(self.client.get(reverse('home'), {'q': 'Đà Lạt', 'tag': 'abc'}).status_code, 200)


class CsrfFailureTests(TestCase):
    """Mã CSRF cũ: đăng xuất vẫn thoát được, form khác vẫn bị chặn (không hiện trang 403)."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user('u1', password='Hoa-Sen!2026', first_name='An', last_name='Lê')
        self.client.force_login(self.user)

    def test_dang_xuat_bang_ma_cu(self):
        response = self.client.post(reverse('logout'), {'csrfmiddlewaretoken': 'cu'})
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_form_khac_van_bi_chan(self):
        post = Post.objects.create(author=self.user, content='Bài.')
        response = self.client.post(reverse('post_detail', args=[post.id]), {'content': 'Lạ', 'csrfmiddlewaretoken': 'cu'},
                                    HTTP_REFERER='https://web-la.example/')
        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)   # không theo Referer ra web lạ
        self.assertFalse(post.comments.exists())


class PostLeadTests(TestCase):
    """Bảng tin tách câu mở đầu (to hơn) khỏi phần còn lại của đoạn trích."""

    def post(self, content):
        return Post(content=content)

    def test_tach_cau_mo_dau(self):
        p = self.post('  Câu mở đầu. Câu hai.\nDòng ba.')
        self.assertEqual(p.lead, 'Câu mở đầu.')
        self.assertEqual(p.excerpt_rest, 'Câu hai.\nDòng ba.')

    def test_bai_mot_cau(self):
        self.assertEqual(self.post('Chỉ một câu').excerpt_rest, '')

    def test_cau_dau_qua_dai(self):
        p = self.post('a' * 400 + '. Câu hai.')
        self.assertEqual(p.excerpt_rest, '')
        self.assertEqual(p.rest, 'Câu hai.')   # trang chi tiết không mất chữ nào


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

    @patch('devBlog.views.SUGGESTION_LIMIT', 10)   # giao diện chỉ hiện 3; ở đây xem đủ thứ tự xếp hạng
    def test_thu_tu_goi_y(self):
        me, ban, theo_doi_toi, ban_chung, cung_chu_de, viet_nhieu, dang_ky_do, tai_khoan_cu = (
            self.make(n) for n in ('me', 'ban', 'theodoitoi', 'banchung', 'cungchude', 'vietnhieu',
                                   'u0123456789ab', 'taikhoancu'))
        User.objects.filter(id__in=[dang_ky_do.id, tai_khoan_cu.id]).update(first_name='', last_name='')
        Follow.objects.create(follower=me, following=ban)              # đã theo dõi -> không gợi ý
        Follow.objects.create(follower=theo_doi_toi, following=me)     # đang theo dõi mình
        Follow.objects.create(follower=ban, following=ban_chung)       # bạn của bạn
        tag = Tag.objects.get(name='Du lịch')   # có sẵn từ migration 0009
        me.profile.interests.add(tag)
        cung_chu_de.profile.interests.add(tag)
        Post.objects.create(author=viet_nhieu, content='Một bài.')

        # Vừa đăng ký dở (mã ẩn, chưa tên) thì không gợi ý; tài khoản cũ chưa tên vẫn gợi ý (xếp cuối: chưa có bài)
        names = [u.username for u in people_you_may_know(me)]
        self.assertEqual(names, ['theodoitoi', 'banchung', 'cungchude', 'vietnhieu', 'taikhoancu'])


class NotificationTests(TestCase):
    """Chuông: bình luận, thích, theo dõi, bài mới của người mình theo dõi."""

    def setUp(self):
        self.an = User.objects.create_user('an', password='x', first_name='An', last_name='Lê')
        self.binh = User.objects.create_user('binh', password='x', first_name='Bình', last_name='Trần')
        self.post = Post.objects.create(content='Bài của An.', author=self.an)
        self.client.force_login(self.binh)

    def kinds(self, user):
        return sorted(user.notifications.values_list('kind', flat=True))

    def test_binh_luan_thich_theo_doi_bao_cho_chu(self):
        self.client.post(reverse('post_detail', args=[self.post.id]), {'content': 'Hay quá'})
        self.client.post(reverse('like_post', args=[self.post.id]))
        self.client.post(reverse('toggle_follow', args=[self.an.id]))
        self.assertEqual(self.kinds(self.an), ['comment', 'follow', 'like'])

    def test_bo_thich_bo_theo_doi_rut_thong_bao(self):
        for _ in range(2):
            self.client.post(reverse('like_post', args=[self.post.id]))
            self.client.post(reverse('toggle_follow', args=[self.an.id]))
        self.assertEqual(self.kinds(self.an), [])

    def test_bai_moi_bao_cho_nguoi_theo_doi(self):
        Follow.objects.create(follower=self.an, following=self.binh)
        self.client.post(reverse('create_post'), {'content': 'Bài mới của Bình.'})
        self.assertEqual(self.kinds(self.an), ['post'])
        self.assertEqual(self.kinds(self.binh), [])   # không tự báo cho mình

    def test_mo_trang_thi_da_doc(self):
        Notification.objects.create(recipient=self.binh, actor=self.an, kind='follow')
        self.assertContains(self.client.get(reverse('home')), '<span class="notif-num">1</span>')
        response = self.client.get(reverse('notifications'))
        self.assertContains(response, 'is-unread')
        self.assertFalse(self.binh.notifications.filter(read=False).exists())

    def test_dem_so_chua_doc(self):
        Notification.objects.create(recipient=self.binh, actor=self.an, kind='follow')
        self.assertEqual(self.client.get(reverse('notification_count')).json(), {'unread': 1})


class PhoneLayoutTests(TestCase):
    def test_thanh_duoi_va_trang_tim_kiem(self):
        user = User.objects.create_user('u1', password='x', first_name='An', last_name='Lê')
        self.client.force_login(user)
        self.assertContains(self.client.get(reverse('home')), 'class="bottom-nav"')
        self.assertContains(self.client.get(reverse('explore')), 'name="q"')


class DeleteCommentTests(TestCase):
    """Chỉ người viết bình luận mới xóa được, và chỉ bằng POST."""

    def setUp(self):
        self.an = User.objects.create_user('an', password='Hoa-Sen!2026', first_name='An', last_name='Lê')
        self.binh = User.objects.create_user('binh', password='Hoa-Sen!2026', first_name='Bình', last_name='Trần')
        post = Post.objects.create(author=self.an, content='Bài của An.')
        self.comment = Comment.objects.create(post=post, author=self.binh, content='Hay quá')
        self.url = reverse('delete_comment', args=[self.comment.id])

    def test_nguoi_viet_xoa_duoc(self):
        self.client.force_login(self.binh)
        self.client.post(self.url)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_nguoi_khac_khong_xoa_duoc(self):
        self.client.force_login(self.an)   # chủ bài nhưng không phải người viết bình luận
        self.client.post(self.url)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

    def test_get_khong_xoa(self):
        self.client.force_login(self.binh)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())


class NotFoundAndMetaTests(TestCase):
    def test_trang_404_rieng(self):
        response = self.client.get('/khong-co-trang-nay/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Không tìm thấy trang này', status_code=404)

    def test_the_meta_chia_se(self):
        response = self.client.get('/')
        self.assertContains(response, 'property="og:image"')
        self.assertContains(response, 'name="description"')


class SeedDemoTests(TestCase):
    """Lệnh seed_demo tạo dữ liệu mẫu, không tạo trùng, và --xoa xóa sạch mà không đụng tài khoản thật."""

    def test_tao_roi_xoa(self):
        from io import StringIO
        from django.core.management import call_command
        real = User.objects.create_user('that', first_name='Thật', last_name='Người')
        call_command('seed_demo', stdout=StringIO())
        demo = User.objects.filter(email__endswith='@demo.perspect.vn')
        self.assertEqual(demo.count(), 20)
        self.assertTrue(all(u.first_name and u.last_name for u in demo.all()))   # không bị kẹt ở bước giới thiệu
        self.assertGreater(Comment.objects.count(), 0)
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(demo.count(), 20)
        call_command('seed_demo', '--xoa', stdout=StringIO())
        self.assertFalse(demo.exists())
        self.assertFalse(Post.objects.exists())
        self.assertTrue(User.objects.filter(pk=real.pk).exists())
