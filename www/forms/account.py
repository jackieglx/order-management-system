import random

from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from utils.encrypt import md5_string
from www import models
from utils import tencent
from django_redis import get_redis_connection
from utils.bootstrap import BootStrapForm


class LoginForm(BootStrapForm, forms.Form):
    # exclude_field_list = ['username']
    role = forms.ChoiceField(
        label="character",
        required=True,
        choices=(("2", "customer"), ("1", "admin"),)
    )

    username = forms.CharField(
        label="username",
        widget=forms.TextInput
    )
    # forms.CharField 的默认行为是要求输入非空数据，默认情况下 required=True。这意味着如果用户在登录时没有输入用户名Django表单会认为这是一个验证错误

    password = forms.CharField(
        label="password",
        widget=forms.PasswordInput(render_value=True)
    )

    def clean_password(self):
        old = self.cleaned_data['password']
        return md5_string(old)
    # Django 表单在执行校验（validation）时，会自动调用以 clean_ 开头的方法，这些方法用于对单个字段进行定制的清理和验证。
    # 所以，当你定义了 clean_password 方法时，Django 在表单校验的过程中会自动调用这个方法。
    # 将密码加密，查询的时候和数据库里的密文对应

class SmsLoginForm(BootStrapForm, forms.Form):
    role = forms.ChoiceField(
        label="character",
        required=True,
        choices=(("2", "customer"), ("1", "admin"),)
    )

    mobile = forms.CharField(
        label="mobile phone",
        validators=[RegexValidator(r'^1[3578]\d{9}$', 'Invalid phone number'), ],
        widget=forms.TextInput
    )
    # 在django里每个表单字段都会自动生成一个HTML id
    # 字段mobile，Django会自动生成id_mobile作为mobile字段的id

    code = forms.CharField(
        label="verification code",
        validators=[RegexValidator(r'^[0-9]{4}$', 'Invalid verification code'), ], # 定义了验证规则
        widget=forms.TextInput
    )

    def clean_code(self):
        mobile = self.cleaned_data.get('mobile')
        code = self.cleaned_data['code']
        if not mobile:
            return code

        conn = get_redis_connection("default")
        # get_redis_connection("default") 是 Django 中的一个函数，用于获取到默认配置的 Redis 连接对象。
        # 在 Django 中，可以配置多个 Redis 数据库，而 "default" 通常是指定的默认数据库。
        cache_code = conn.get(mobile)  # 从 Redis 缓存中获取存储在键 mobile 下的数据
        if not cache_code:
            raise ValidationError("未发送或已失效")
        if code != cache_code.decode('utf-8'):
            raise ValidationError("验证码错误")

        # 将redis中的键值对删除 key=mobile
        conn.delete(mobile)

        return code


class SendSmsForm(forms.Form):
    role = forms.ChoiceField(
        label="character",
        required=True,
        choices=(("2", "customer"), ("1", "admin"),)
    )

    mobile = forms.CharField(
        label="mobile phone",
        widget=forms.TextInput,
        required=True,
        validators=[RegexValidator(r'^1[3578]\d{9}$', 'Invalid phone number'), ]
    )

    # 这个网站仅供内部使用，所以只有针对开户的手机号才能登陆，所以还要去数据库里查看这个手机号是否注册了
    def clean_mobile(self):
        role = self.cleaned_data['role']
        old = self.cleaned_data['mobile']

        # 去数据库查询，手机号是否已注册？
        if role == "1":
            exists = models.Administrator.objects.filter(active=1).filter(mobile=old).exists()
        else:
            exists = models.Customer.objects.filter(active=1).filter(mobile=old).exists()

        if not exists:
            raise ValidationError("The phone number does not exist.")

        # 生成短信验证码 + 发送短信
        sms_code = str(random.randint(1000, 9999))
        print("随机短信验证码：", sms_code)
        is_ok = tencent.send_sms(old, sms_code)
        if not is_ok:
            raise ValidationError("SMS delivery failed.")

        # 短信验证码写入redis中+超时时间
        from django_redis import get_redis_connection
        conn = get_redis_connection("default")
        conn.set(old, sms_code, ex=5 * 60)

        return old
