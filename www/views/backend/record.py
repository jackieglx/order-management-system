from www import models
from utils.v3 import BaseCurd, get_datetime_field, get_choice_field, Option

from django.urls import reverse
from django.utils.safestring import mark_safe

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


class TransactionRecordModelForm(BootStrapForm, forms.ModelForm):
    charge_type = forms.TypedChoiceField(
        label="交易类型",
        choices=[(1, "充值"), (2, "扣款")],
        coerce=lambda val: int(val)
    )

    class Meta:
        model = models.TransactionRecord
        fields = ["customer", "charge_type", "amount"]


class Record(BaseCurd):
    # 列表配置
    queryset = models.TransactionRecord.objects.all().order_by("-id")

    table_header = ["日期", "客户", "金额", "交易类型", "订单号", "管理员"]

    def get_order_oid(request, instance):
        if instance.order_oid:
            url = reverse("yang2_list")
            return mark_safe(f'<a href="{url}?keyword={instance.order_oid}">订单号：{instance.order_oid}</a>')
        return "-"

    table_field = [
        # ("db", "create_datetime"),
        ("func", get_datetime_field("create_datetime", "%Y-%m-%d")),
        # ("db", "customer"),
        ("func", lambda req, ins: ins.customer.username),
        ("func", lambda req, ins: f"-{ins.amount}" if ins.charge_type in [2, 3] else f"+{ins.amount}"),
        ("func", get_choice_field("charge_type")),
        ("func", get_order_oid),
        # ("func", lambda req, ins: ins.creator if ins.creator else ""),
        ("func", lambda req, ins: ins.creator or ""),
    ]

    # 组合搜索
    search_group = [
        models.TransactionRecord,
        Option("charge_type", is_choice=True),
        Option("customer", False, db_condition={"active": 1}),
    ]

    # 关键字
    search_list = ["customer__username__contains", "order_oid__contains"]

    #  新增和编辑配置
    add_template = "v3/form.html"
    # add_form_model = models.TransactionRecord
    # add_form_fields = ["customer", "charge_type", "amount"]
    add_form_class = TransactionRecordModelForm

    def add_save(self, form, request):
        # 用户余额增加或减少
        customer = form.cleaned_data['customer']
        charge_type = form.cleaned_data['charge_type']
        amount = form.cleaned_data['amount']
        if amount < 0:
            form.add_error("amount", "金额不能小于零")
            return render(request, self.add_template, {"form": form})

        try:
            with transaction.atomic():
                if charge_type == 1:
                    models.Customer.objects.filter(id=customer.id).update(balance=F("balance") + amount)
                else:
                    models.Customer.objects.filter(id=customer.id).update(balance=F("balance") - amount)

                # 创建交易记录
                form.instance.creator_id = request.nb_user.id
                form.save()
        except Exception as e:
            form.add_error("amount", "新增失败")
            return render(request, self.add_template, {"form": form})
