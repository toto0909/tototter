from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
import uuid as uuid_lib

#TODO 外部ストレージに保存先を変更
#Profileクラスでアバター画像のパスを返すメソッドを定義(外部に変更)
def apload_avatar_path(instance, filename):
    ext = filename.split('.')[-1] #拡張子
    return '/'.join(['avatars', str(instance.userProfile.id)+str(instance.nickName)+str(".")+str(ext)])

#TODO 外部ストレージに保存先を変更
#Postクラスで投稿画像のパスを返すメソッドを定義
def apload_post_path(instance, filename):
    ext = filename.split('.')[-1] #拡張子
    return '/'.join(['posts', str(instance.userPost.id)+str(instance.title)+str(".")+str(ext)])

#DjangoのデフォルトBaseUserManagerクラスにemailを使用できるよう一部オーバーライドしたクラス「UserManager」を作成
class UserManager(BaseUserManager):
    #ユーザー作成
    def create_user(self,  email, password = None):
        #emailが無い場合の例外処理
        if not email:
            raise ValueError('Email is Must.')
        #userインスタンス生成(emailを正規化する処理を含む)
        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user
    #superuserもデフォルトのものではemailが使用できないのでオーバーライドして定義し直す
    def create_superuser(self, email, password = None):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

#DjangoのデフォルトUserクラスemailを使用できるよう一部オーバーライドしたクラス(必要パラメータを既存Userクラスに追加)
class User(AbstractBaseUser, PermissionsMixin):
    #ユーザーID : UUIDでユニークに設定する
    uuid = models.UUIDField(
        default=uuid_lib.uuid4,
        primary_key=True,
        editable=False
    )
    #Eメール
    email = models.EmailField(
        max_length = 50,
        unique = True
    )
    #ログイン可能ユーザーか否か
    is_active = models.BooleanField(
        default = True
    )
    #管理ユーザー(adminログイン可能ユーザー)か否か
    is_staff = models.BooleanField(
        default = False
    )
    #Userクラスから上記で作成したUserManagerのメソッド・フィールドにアクセスできるようにネストさせたオブジェクトを持たせる
    objects = UserManager()
    #デフォルトでusernameを使用する所をemailにオーバーライドする
    USERNAME_FIELD = 'email'
    def __str__(self):
        return self.email

#ユーザーのプロフィールを定義するProfile Modelを作成
class Profile(models.Model):
    #ユーザー名
    username_validators = UnicodeUsernameValidator()
    user_name = models.CharField(
        "ユーザー名",
        max_length=10,
        unique=True,
        help_text="※10文字以下の文字や数字、一部の記号で入力してください。",
        validators = [username_validators],
        error_messages={
            "unique": "このユーザー名は既に使用されています。",
        },
    )
    #Userとprofileが1:1になるように定義(Aさん <=> プロフィールA)
    userProfile = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='userProfile',
        on_delete=models.CASCADE #Userが削除された時に紐づくProfileも同時に削除されるようにする
    )
    #所属勢力ID
    user_team_id = models.PositiveSmallIntegerField(
        null=False,
        default=0,
        editable=True,
    )
    #自己紹介文
    user_text = models.TextField(
        blank=True,
        null=True,
        default='',
        max_length=140,
    )
    #生成日時
    created_on = models.DateTimeField(
        auto_now_add=True
    )
    #プロフィール画像参照先
    img_path = models.ImageField(
        blank=True,
        null=True,
        upload_to=apload_avatar_path
    )
    def __str__(self):
        return self.user_name

#投稿を定義するPost Modelを作成
class Post(models.Model):
    #投稿文
    post_text = models.TextField(
        blank=False,
        null=False,
        default='',
        max_length=140,
    )
    #投稿日時
    created_on = models.DateTimeField(
        auto_now_add=True
    )
    #投稿画像参照先
    img = models.ImageField(
        blank=True,
        null=True,
        upload_to=apload_post_path
    )
    #UserとPostが1:多になるように定義(例 Aさん <=> 投稿1,2,3...)
    userPost = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='userPost',
        on_delete=models.CASCADE
    )
    #Postといいねしたユーザー(liked)が多:多になるように定義(例 投稿1 <=> いいねしたUser X, Y, Z / 投稿2 <=> いいねしたUser I, J, K)
    liked = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked',
        blank=True
    )
    def __str__(self):
        return self.post_text

#投稿に対するコメントを定義するComment Modelを作成
class Comment(models.Model):
    #コメント文
    comment_text = models.TextField(
        blank=False,
        null=False,
        default='',
        max_length=140,
    )
    #ユーザーとコメントが1:多になるように定義(例 Aさん <=> 過去に投稿したコメント1,2,3...)
    userComment = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='userComment',
        on_delete=models.CASCADE
    )
    #投稿とコメントか1:多になるように定義(例 投稿1 <=> コメント1,2,3...)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE
    )
    def __str__(self):
        return self.comment_text