from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Post


class PostOwnershipTests(TestCase):
    """Chỉ tác giả mới được sửa / xóa bài của mình."""

    def setUp(self):
        self.author = User.objects.create_user('tacgia', password='Hoa-Sen!2026')
        self.other = User.objects.create_user('nguoikhac', password='Hoa-Sen!2026')
        self.post = Post.objects.create(title='Tiêu đề gốc', content='Nội dung gốc', author=self.author)
        self.edit_url = reverse('edit_post', args=[self.post.id])
        self.delete_url = reverse('delete_post', args=[self.post.id])
        self.detail_url = reverse('post_detail', args=[self.post.id])

    def test_nguoi_khac_khong_sua_duoc_bai(self):
        self.client.force_login(self.other)

        response = self.client.get(self.edit_url)
        self.assertRedirects(response, self.detail_url)

        response = self.client.post(self.edit_url, {'title': 'Bị sửa', 'content': 'Bị sửa'})
        self.assertRedirects(response, self.detail_url)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Tiêu đề gốc')
        self.assertEqual(self.post.content, 'Nội dung gốc')

    def test_nguoi_khac_khong_xoa_duoc_bai(self):
        self.client.force_login(self.other)

        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.detail_url)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_chua_dang_nhap_khong_sua_xoa_duoc(self):
        self.client.post(self.edit_url, {'title': 'Bị sửa', 'content': 'Bị sửa'})
        self.client.post(self.delete_url)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Tiêu đề gốc')

    def test_tac_gia_sua_va_xoa_duoc_bai(self):
        self.client.force_login(self.author)

        response = self.client.post(self.edit_url, {'title': 'Tiêu đề mới', 'content': 'Nội dung mới'})
        self.assertRedirects(response, self.detail_url)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Tiêu đề mới')

        response = self.client.post(self.delete_url)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
