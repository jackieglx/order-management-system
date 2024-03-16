import random
import datetime

from django import forms
from django.urls import path
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.contrib import messages
from django.shortcuts import render, redirect
from django_redis import get_redis_connection
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from www import models
from utils.bootstrap import BootStrapForm
from utils.video import get_old_view_count
from utils.v3 import BaseCurd, get_datetime_field, get_choice_field, gen_url, Option
from utils.encrypt import md5_string


class CustomerModelForm(BootStrapForm, forms.ModelForm):
    exclude_field_list = ['level']

    confirm_password = forms.CharField(
        label="重复密码",
        widget=forms.PasswordInput(render_value=True)
    )

    class Meta:
        model = models.Customer
        fields = ['level', "username", 'mobile', 'password', 'confirm_password', ]
        widgets = {
            'password': forms.PasswordInput(render_value=True),
            "level": forms.RadioSelect(attrs={'class': "form-radio"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['level'].queryset = models.Level.objects.filter(active=1)

    def clean_password(self):
        password = self.cleaned_data['password']

        return md5_string(password)

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = md5_string(self.cleaned_data.get('confirm_password', ''))

        if password != confirm_password:
            raise ValidationError("密码不一致")
        return confirm_password


class CustomerEditModelForm(BootStrapForm, forms.ModelForm):
    exclude_field_list = ['level']

    class Meta:
        model = models.Customer
        fields = ['level', "username", 'mobile', ]
        widgets = {
            "level": forms.RadioSelect(attrs={'class': "form-radio"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CustomerResetModelForm(BootStrapForm, forms.ModelForm):
    confirm_password = forms.CharField(
        label="重复密码",
        widget=forms.PasswordInput(render_value=True)
    )

    class Meta:
        model = models.Customer
        fields = ['password', 'confirm_password', ]
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }

    def clean_password(self):
        password = self.cleaned_data['password']

        return md5_string(password)

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = md5_string(self.cleaned_data.get('confirm_password', ''))

        if password != confirm_password:
            raise ValidationError("密码不一致")
        return confirm_password


class Customer(BaseCurd):
    # 客户列表，表格配置
    queryset = models.Customer.objects.filter(active=1).order_by("-id")
    table_header = ["用户名", "手机号","余额", "级别", "创建日期", "重置密码"]

    def get_reset(request, instance):
        url = gen_url(request, "customer_reset", kwargs={"pk": instance.pk})
        return mark_safe(f"<a href='{url}'>重置密码</a>")

    table_field = [
        ("db", "username"),
        ("db", "mobile"),
        ("db", "balance"),
        ("func", lambda req, ins: f"{ins.level.title}（{ins.level.percent}%折扣）"),
        ("func", get_datetime_field("create_date", "%Y-%m-%d")),
        ("func", get_reset)
    ]

    # 组合搜索
    search_group = [
        models.Customer,
        Option("level", False, {"active": 1}),
        Option("creator", False),
        Option("gender", is_choice=True),
        # Option("mobile", db_condition={"id__lte": 4}, text_func=lambda x: x.mobile, value_func=lambda x: x.mobile),
    ]
    # 关键字搜索
    search_list = ["username", "mobile__contains"]

    # 创建ModelForm
    add_template = "v3/form.html"
    add_form_class = CustomerModelForm

    def add_save(self, form, request):
        form.instance.creator_id = request.nb_user.id
        form.save()

    # 编辑
    edit_template = "v3/form.html"
    edit_form_class = CustomerEditModelForm

    # 删除
    def do_delete(self, request, pk):
        models.Customer.objects.filter(active=1, id=pk).update(active=0)

    # 重置密码
    def get_extra_url(self):
        return [
            path(f'reset/<int:pk>/', self.dispatch(self.reset), name=f"customer_reset")
        ]

    def reset(self, request, pk):
        origin = request.GET.get("redirect", "/home/")

        if request.method == "GET":
            form = CustomerResetModelForm()
            return render(request, "v3/form.html", {"form": form})

        instance = models.Customer.objects.filter(id=pk, active=1).first()
        form = CustomerResetModelForm(data=request.POST, instance=instance)
        if not form.is_valid():
            return render(request, 'v3/form.html', {'form': form})

        form.save()
        return redirect(origin)
