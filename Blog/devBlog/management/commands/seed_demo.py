"""Tạo khoảng 20 tài khoản mẫu kèm bài viết, bình luận, lượt thích, theo dõi cho web đỡ trống.

    python manage.py seed_demo          # tạo (đã có rồi thì thôi)
    python manage.py seed_demo --xoa    # xóa sạch tài khoản mẫu và mọi thứ của họ

Tài khoản mẫu nhận ra bằng đuôi email DEMO_DOMAIN (email không hiện trên web).
Không đặt mật khẩu nên không ai đăng nhập vào được; không đụng tới tài khoản thật.
"""
import random
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from devBlog.models import Comment, Follow, Post, Tag, UserProfile

DEMO_DOMAIN = '@demo.perspect.vn'

# (họ, tên, chủ đề quan tâm, [(nội dung bài, [chủ đề], [bình luận])])
PEOPLE = [
    ('Trần', 'Minh Anh', ['Ẩm thực', 'Du lịch'], [
        ('Quán bún chả đầu ngõ nhà mình hôm nay đóng cửa, cả xóm ngơ ngác.\n\nBác chủ dán tờ giấy "nghỉ 3 hôm đi ăn cưới cháu". Ba hôm này chắc mình ăn mì gói.',
         ['Ẩm thực'], ['Haha y chang quán phở gần công ty mình, nghỉ cái là cả văn phòng mất phương hướng', 'Bác đi ăn cưới mà cả xóm nhịn đói 😂']),
        ('Lần đầu đi Đà Lạt một mình, không lên lịch gì cả.\n\nSáng ngủ dậy thấy sương thì đi bộ quanh hồ, đói thì ghé đại một quán. Hóa ra không có kế hoạch lại thoải mái hơn hẳn.',
         ['Du lịch'], ['Đi một mình mới thấy mình tự do thật sự', 'Quán nào ngon chỉ mình với, tháng sau mình lên', 'Sương Đà Lạt sáng sớm là đỉnh nhất']),
    ]),
    ('Nguyễn', 'Quốc Huy', ['Công nghệ', 'Game'], [
        ('Cuối cùng cũng sửa được cái bug làm mình mất ngủ 3 đêm.\n\nNguyên nhân là thiếu đúng một dấu phẩy trong file cấu hình. Không biết nên cười hay nên khóc.',
         ['Công nghệ'], ['Dân code ai cũng từng trải qua cảm giác này', 'Một dấu phẩy, ba đêm. Đau thật sự']),
        ('Tối qua chơi lại game hồi cấp 2, vẫn kẹt đúng màn cũ.\n\nMười năm trôi qua, kỹ năng không tiến bộ chút nào.',
         ['Game'], ['Game gì vậy bạn', 'Có những màn sinh ra để làm khó mình cả đời 😅']),
        ('Ai dùng bàn phím cơ lâu rồi cho mình hỏi switch nào gõ êm mà không ồn quá?\n\nMình ngồi chung phòng với đứa em, nó than suốt.',
         ['Công nghệ'], ['Switch đỏ nha bạn, êm mà nhẹ tay', 'Lắp thêm o-ring là đỡ ồn hẳn']),
    ]),
    ('Lê', 'Thu Hà', ['Âm nhạc', 'Sức khỏe'], [
        ('Sáng nay chạy được 5km mà không dừng lần nào.\n\nTháng trước chạy 1km đã thở không ra hơi. Ghi lại đây để tháng sau đọc lại cho có động lực.',
         ['Sức khỏe'], ['Giỏi quá, cố lên nha', 'Mình cũng đang tập, mới được 2km thôi', 'Kiên trì là được hết']),
        ('Nghe lại album cũ của Trịnh Công Sơn trong lúc trời mưa.\n\nCó những bài hồi nhỏ nghe không hiểu, giờ lớn lên nghe mới thấy thấm.',
         ['Âm nhạc'], ['Diễm xưa mỗi lần mưa là phải nghe', 'Đúng là phải trải qua mới hiểu']),
    ]),
    ('Phạm', 'Gia Bảo', ['Thể thao', 'Game'], [
        ('Đá bóng với hội bạn cũ sau hai năm không gặp.\n\nThua 7-2 nhưng cười cả buổi. Hẹn tháng sau đá tiếp, lần này phải gỡ.',
         ['Thể thao'], ['Thua mà vui là được', 'Lần sau rủ mình với, mình thủ môn tạm được']),
        ('Đêm qua thức xem chung kết, sáng nay đi làm như người mất hồn.\n\nNhưng trận đấu xứng đáng từng phút mất ngủ.',
         ['Thể thao'], ['Hiệp phụ căng thật sự', 'Mình ngủ quên đúng lúc ghi bàn 😭', 'Sáng nay cả văn phòng ai cũng thâm mắt']),
    ]),
    ('Võ', 'Ngọc Trâm', ['Ẩm thực', 'Giáo dục'], [
        ('Hôm nay học sinh tặng mình một bức vẽ, vẽ cô giáo mà tóc màu xanh lá.\n\nHỏi sao tóc xanh thì bé bảo "tại cô hiền như cái cây". Dán lên bàn làm việc luôn.',
         ['Giáo dục'], ['Trời ơi dễ thương xỉu', 'Hiền như cái cây 🥹', 'Mấy bé nghĩ gì nói nấy, đáng yêu ghê']),
        ('Thử làm bánh flan theo công thức của mẹ, lần thứ ba mới không bị rỗ.\n\nBí quyết là hấp lửa nhỏ, kê thêm cái khăn trên nắp nồi.',
         ['Ẩm thực'], ['Lưu lại liền, mình làm lần nào cũng rỗ', 'Mẹ mình cũng kê khăn y vậy']),
    ]),
    ('Đặng', 'Tuấn Kiệt', ['Du lịch', 'Phim ảnh'], [
        ('Đi xe máy từ Sài Gòn ra Phan Thiết, đường ven biển đẹp hơn mình tưởng.\n\nĐoạn qua Mũi Né có mấy đồi cát, dừng lại chụp mà nắng muốn cháy da.',
         ['Du lịch'], ['Cung đường này mình đi rồi, đẹp thật', 'Nhớ mang kem chống nắng nha bạn']),
        ('Xem lại phim Mắt Biếc lần thứ hai, vẫn khóc ở đúng cảnh cũ.\n\nCó lẽ phim hay là phim mình biết trước kết mà vẫn buồn.',
         ['Phim ảnh'], ['Ngạn ơi là Ngạn', 'Nhạc phim cũng hay nữa', 'Mình không dám xem lại luôn']),
    ]),
    ('Bùi', 'Khánh Linh', ['Phim ảnh', 'Âm nhạc'], [
        ('Rạp chiếu suất 10 giờ tối chỉ có mình với một bác lớn tuổi.\n\nHết phim bác quay sang hỏi "con thấy hay không", hai bác cháu đứng bàn phim thêm mười phút.',
         ['Phim ảnh'], ['Kỷ niệm dễ thương ghê', 'Suất khuya là chân ái, không ai làm ồn']),
        ('Mua được cái máy nghe đĩa than cũ ngoài chợ đồ cổ.\n\nTiếng hơi rè nhưng nghe ấm lắm, kiểu như có người đang hát trong phòng.',
         ['Âm nhạc'], ['Chợ nào vậy bạn, chỉ mình với', 'Đĩa than nghe là ghiền']),
    ]),
    ('Hoàng', 'Đức Thịnh', ['Công nghệ', 'Giáo dục'], [
        ('Dạy bố dùng điện thoại thông minh, buổi thứ tư vẫn ở bài gọi video.\n\nNhưng hôm qua bố tự gọi cho mình được, nhìn mặt bố vui mà mình cũng vui theo.',
         ['Công nghệ'], ['Kiên nhẫn ghê, mình dạy mẹ được hai buổi là cãi nhau', 'Bố bạn dễ thương quá']),
        ('Ôn thi cuối kỳ mà đọc mãi một trang không vào đầu.\n\nQuyết định đi ngủ, sáng mai dậy sớm học tiếp. Ai cùng cảnh thì điểm danh.',
         ['Giáo dục'], ['Điểm danh 🙋', 'Ngủ đủ mới học vô được, đúng rồi', 'Mình đang đọc trang đó lần thứ năm']),
    ]),
    ('Ngô', 'Phương Thảo', ['Sức khỏe', 'Ẩm thực'], [
        ('Một tuần không uống trà sữa, thấy người nhẹ hẳn.\n\nNói vậy thôi chứ chiều nay đi ngang quán vẫn đứng nhìn hơi lâu.',
         ['Sức khỏe'], ['Đứng nhìn thôi là giỏi lắm rồi 😂', 'Mình được ba ngày là gục']),
        ('Nấu canh chua cá lóc theo kiểu bà ngoại, nấu xong ngồi ăn mà nhớ bà.\n\nVẫn thiếu thiếu cái gì đó, chắc là thiếu bà ngồi bên cạnh.',
         ['Ẩm thực'], ['Đọc mà rưng rưng', 'Món của bà lúc nào cũng ngon nhất', 'Canh chua miền Tây là số một']),
    ]),
    ('Đỗ', 'Hải Nam', ['Thể thao', 'Du lịch'], [
        ('Leo Fansipan lần đầu, lên tới đỉnh thì mây che kín không thấy gì.\n\nNhưng lúc đi xuống mây tan, cả thung lũng hiện ra. Đáng từng bước chân.',
         ['Du lịch', 'Thể thao'], ['Đi bộ hay đi cáp treo vậy bạn', 'Mình lên cũng gặp mây y chang', 'Thung lũng lúc mây tan đẹp lắm']),
        ('Bơi buổi sáng ở hồ bơi công cộng, gặp một ông cụ 80 tuổi bơi nhanh hơn mình.\n\nCụ bảo bơi mỗi ngày từ hồi 30 tuổi. Thế là có động lực rồi.',
         ['Thể thao'], ['Cụ khỏe ghê', 'Đi bơi buổi sáng sướng thật']),
    ]),
    ('Trương', 'Mỹ Duyên', ['Giải trí', 'Âm nhạc'], [
        ('Đi hát karaoke với công ty, sếp hát bài Bolero mà cả phòng im phăng phắc.\n\nHóa ra sếp từng thi hát hồi sinh viên. Hôm nay mới biết.',
         ['Giải trí'], ['Sếp có tài lẻ ghê', 'Mấy anh chị lớn hát bolero là hay khỏi bàn']),
        ('Tập đàn ukulele được hai tuần, đầu ngón tay đau mà vẫn muốn tập.\n\nĐã đánh được trọn bài Happy Birthday, chuẩn bị đánh tặng sinh nhật mẹ.',
         ['Âm nhạc'], ['Cố lên, qua giai đoạn đau tay là sướng', 'Mẹ chắc vui lắm', 'Quay video lại đi bạn']),
    ]),
    ('Lý', 'Thanh Tùng', ['Công nghệ', 'Phim ảnh'], [
        ('Điện thoại rơi xuống nước, phơi trong thùng gạo hai ngày rồi vẫn chưa lên.\n\nAi có kinh nghiệm cứu điện thoại không chỉ mình với.',
         ['Công nghệ'], ['Mang ra tiệm sấy main đi bạn, thùng gạo không ăn thua đâu', 'Tháo pin ra trước đã']),
        ('Cày xong bộ phim tài liệu về đại dương, giờ nhìn con cá trong bể nhà cũng thấy khác.\n\nBiển sâu còn nhiều thứ con người chưa biết lắm.',
         ['Phim ảnh'], ['Tên phim là gì vậy bạn', 'Mình mê phim tài liệu kiểu này']),
    ]),
    ('Mai', 'Hồng Nhung', ['Du lịch', 'Ẩm thực'], [
        ('Ăn sáng ở chợ nổi Cái Răng, tô hủ tiếu bán ngay trên ghe.\n\nCô bán hàng chèo ghe lại gần, múc hủ tiếu đưa qua mà không đổ giọt nào. Nghề thật sự.',
         ['Du lịch', 'Ẩm thực'], ['Muốn đi chợ nổi quá', 'Phải dậy từ 5 giờ mới kịp đó', 'Hủ tiếu trên ghe ăn ngon lạ']),
        ('Hội An buổi tối mất điện, cả phố chỉ còn ánh đèn lồng.\n\nTự nhiên thấy phố cổ đẹp hơn bình thường.',
         ['Du lịch'], ['Nghe thôi đã thấy đẹp', 'Hội An là phải đi buổi tối']),
    ]),
    ('Châu', 'Văn Lộc', ['Game', 'Giải trí'], [
        ('Ba anh em ngồi chơi cờ tỷ phú từ tối tới gần sáng.\n\nĐứa em út phá sản ba lần mà vẫn đòi chơi tiếp. Tuổi thơ quay về.',
         ['Game', 'Giải trí'], ['Cờ tỷ phú là phá tình anh em 😂', 'Nhà mình chơi xong là giận nhau một tuần']),
        ('Hôm nay đi quán net ngày xưa, máy móc đổi hết, chỉ có ông chủ là vẫn vậy.\n\nÔng còn nhớ mặt mình, hỏi "lâu rồi không thấy ghé".',
         ['Game'], ['Kỷ niệm thanh xuân ghê', 'Ông chủ quán net nhớ dai thật']),
    ]),
    ('Tạ', 'Bích Ngọc', ['Giáo dục', 'Sức khỏe'], [
        ('Tự thưởng cho mình một buổi chiều không điện thoại.\n\nĐọc hết nửa cuốn sách, uống trà, ngắm mây. Không ngờ ba tiếng lại dài như vậy.',
         ['Sức khỏe'], ['Mình thử mà cứ năm phút lại cầm máy lên', 'Đọc sách gì vậy bạn']),
        ('Đậu học bổng rồi mọi người ơi!\n\nNộp hồ sơ bốn lần, tới lần thứ năm mới được. Ai đang nộp thì đừng bỏ cuộc nha.',
         ['Giáo dục'], ['Chúc mừng bạn!!!', 'Lần thứ năm luôn, phục thật', 'Đọc mà có thêm động lực']),
    ]),
    ('Huỳnh', 'Tấn Phát', ['Thể thao', 'Công nghệ'], [
        ('Đạp xe đi làm được một tháng, tiết kiệm tiền xăng mà còn giảm 3 ký.\n\nChỉ khổ mấy hôm mưa, tới công ty là ướt như chuột lột.',
         ['Thể thao'], ['Mua bộ áo mưa đạp xe đi bạn', 'Đạp xe giữa Sài Gòn cũng gan']),
        ('Ráp xong bộ máy tính đầu tiên, bấm nút nguồn mà tim đập thình thịch.\n\nMàn hình lên, quạt quay, không có mùi khét. Thành công.',
         ['Công nghệ'], ['Cảm giác máy lên lần đầu đã thật', 'Không có mùi khét là mừng rồi 😂', 'Cấu hình sao bạn']),
    ]),
    ('Kiều', 'Diễm My', ['Phim ảnh', 'Giải trí'], [
        ('Rủ cả nhà xem phim ma, cuối cùng chỉ có mình là sợ.\n\nBà nội xem tỉnh bơ, còn bình luận "con ma này hóa trang dở".',
         ['Phim ảnh', 'Giải trí'], ['Bà nội đỉnh quá', 'Người lớn tuổi không sợ ma đâu 😂']),
        ('Đi xem kịch lần đầu, không ngờ diễn viên đứng ngay trước mặt lại cuốn đến vậy.\n\nXem xong muốn đi xem tiếp vở khác.',
         ['Giải trí'], ['Kịch sân khấu có cái hay riêng', 'Sân khấu nào vậy bạn']),
    ]),
    ('La', 'Hoàng Long', ['Ẩm thực', 'Du lịch'], [
        ('Ăn thử bánh mì chảo ở Sài Gòn lúc 6 giờ sáng, đông nghẹt.\n\nĐứng chờ 15 phút nhưng ăn xong thấy đáng.',
         ['Ẩm thực'], ['Quán ở đường nào vậy', 'Bánh mì chảo buổi sáng là hết ý']),
        ('Đi Quy Nhơn mùa này biển vắng, nước trong vắt.\n\nNằm trên cát nghe sóng, không muốn về.',
         ['Du lịch'], ['Quy Nhơn đẹp mà chưa đông, đi liền', 'Mình mê Kỳ Co', 'Nhìn mà ghen tị']),
    ]),
    ('Phan', 'Thùy Dung', ['Âm nhạc', 'Giáo dục'], [
        ('Con mèo nhà mình cứ nghe mình tập piano là bỏ đi chỗ khác.\n\nKhông biết do mình đàn dở hay do nó không thích nhạc cổ điển.',
         ['Âm nhạc'], ['Chắc do bài khó nghe với mèo 😂', 'Mèo nhà mình thì nằm lên phím luôn']),
        ('Đi học thêm tiếng Nhật buổi tối sau giờ làm.\n\nMệt nhưng vui, cả lớp toàn người đi làm như mình, ai cũng có lý do riêng để học.',
         ['Giáo dục'], ['Cố lên bạn ơi', 'Mình cũng đang học, khó nhất là chữ Kanji']),
    ]),
    ('Vương', 'Nhật Minh', ['Game', 'Thể thao'], [
        ('Thua liền mười trận xếp hạng, quyết định tắt máy đi ngủ.\n\nCó những ngày chơi game cũng cần biết dừng.',
         ['Game'], ['Ngày đen thì nghỉ là khôn', 'Mai lên lại thôi']),
        ('Chiều nay ra công viên đánh cầu lông với ông hàng xóm.\n\nÔng 60 tuổi mà đập cầu mạnh hơn mình. Phải tập thêm thôi.',
         ['Thể thao'], ['Mấy ông chú công viên toàn cao thủ', 'Cầu lông vui mà ra mồ hôi nhiều']),
    ]),
]


class Command(BaseCommand):
    help = 'Tạo (hoặc xóa với --xoa) khoảng 20 tài khoản mẫu kèm bài viết, bình luận, lượt thích, theo dõi'

    def add_arguments(self, parser):
        parser.add_argument('--xoa', action='store_true', help='Xóa tài khoản mẫu và mọi thứ của họ')

    def handle(self, *args, **options):
        demo = User.objects.filter(email__endswith=DEMO_DOMAIN)
        if options['xoa']:
            n = demo.count()
            demo.delete()   # CASCADE kéo theo hồ sơ, bài, bình luận, theo dõi, thông báo
            self.stdout.write(self.style.SUCCESS(f'Đã xóa {n} tài khoản mẫu.'))
            return
        if demo.exists():
            self.stdout.write('Đã có tài khoản mẫu, không tạo thêm. Muốn làm lại: chạy --xoa trước.')
            return
        with transaction.atomic():
            self.seed()

    def seed(self):
        rnd = random.Random(2026)
        now = timezone.now()
        tags = {}

        def tag(name):
            if name not in tags:
                tags[name], _ = Tag.objects.get_or_create(name=name)
            return tags[name]

        users, posts = [], []
        for i, (last, first, interests, items) in enumerate(PEOPLE):
            joined = now - timedelta(days=rnd.randint(25, 40), hours=rnd.randint(0, 23))
            user = User(username='u' + uuid.uuid4().hex[:12], email=f'user{i + 1}{DEMO_DOMAIN}',
                        first_name=first, last_name=last, date_joined=joined)
            user.set_unusable_password()
            user.save()
            profile = UserProfile.objects.create(user=user)
            profile.interests.set([tag(t) for t in interests])
            users.append(user)
            for content, post_tags, comments in items:
                post = Post.objects.create(author=user, content=content)
                post.tags.set([tag(t) for t in post_tags])
                created = now - timedelta(days=rnd.randint(0, 20), hours=rnd.randint(0, 23),
                                          minutes=rnd.randint(0, 59))
                # auto_now_add/auto_now luôn ghi giờ hiện tại: dùng update() để lùi ngày đăng
                Post.objects.filter(pk=post.pk).update(created_at=created, updated_at=created)
                posts.append((post, created, comments))

        for post, created, comments in posts:
            others = [u for u in users if u != post.author]
            for text, who in zip(comments, rnd.sample(others, len(comments))):
                c = Comment.objects.create(post=post, author=who, content=text)
                at = min(created + timedelta(minutes=rnd.randint(5, 60 * 30)), now)
                Comment.objects.filter(pk=c.pk).update(created_at=at)
            post.likes.set(rnd.sample(others, rnd.randint(2, 12)))

        follows = 0
        for user in users:
            for target in rnd.sample([u for u in users if u != user], rnd.randint(3, 9)):
                Follow.objects.create(follower=user, following=target)
                follows += 1

        self.stdout.write(self.style.SUCCESS(
            f'Đã tạo {len(users)} tài khoản, {len(posts)} bài, '
            f'{Comment.objects.filter(author__in=users).count()} bình luận, {follows} lượt theo dõi.'
        ))
