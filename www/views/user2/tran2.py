from django.utils.safestring import mark_safe
from django.urls import reverse

from www import models
from utils.v3 import BaseCurd, get_datetime_field, get_choice_field, Option


class Tran2(BaseCurd):
    table_header = ["日期", "金额", "交易类型", "订单号", "管理员"]

    def get_order_oid(request, instance):
        if instance.order_oid:
            url = reverse("yang2_list")
            return mark_safe(f'<a href="{url}?keyword={instance.order_oid}">订单号：{instance.order_oid}</a>')
        return "-"

    table_field = [
        # ("db", "create_datetime"),
        ("func", get_datetime_field("create_datetime", "%Y-%m-%d")),
        ("func", lambda req, ins: f"-{ins.amount}" if ins.charge_type in [2, 3] else f"+{ins.amount}"),
        ("func", get_choice_field("charge_type")),
        ("func", get_order_oid),
        # ("func", lambda req, ins: ins.creator if ins.creator else ""),
        ("func", lambda req, ins: ins.creator or ""),
    ]

    def get_queryset(self, request):
        return models.TransactionRecord.objects.filter(customer_id=request.nb_user.id).order_by("-id")

    search_group = [
        models.TransactionRecord,
        Option("charge_type", is_choice=True),
    ]
