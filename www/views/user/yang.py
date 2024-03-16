import random
import datetime

from django import forms
from django.conf import settings
from django.db import transaction
from django.db.models import Q, F
from django.contrib import messages
from django.shortcuts import render, redirect
from django_redis import get_redis_connection
from django.core.exceptions import ValidationError

from www import models
from utils.pager import Pagination
from utils.bootstrap import BootStrapForm


def yang_list(request):
    keyword = request.GET.get("keyword", "").strip()
    con = Q()
    if keyword:
        con.connector = "OR"
        con.children.append(("oid__contains", keyword))
        con.children.append(("url__contains", keyword))

    queryset = models.Order.objects.filter(active=1, customer_id=request.nb_user.id).filter(con).order_by("-id")
    pager = Pagination(request, queryset)
    context = {"pager": pager, "keyword": keyword}
    return render(request, 'user/yang_list.html', context)


class YangModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.Order
        fields = ['url', "count", 'memo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 生成价格策略的信息
        price_count_list = []
        text_list = []
        queryset = models.PricePolicy.objects.all().order_by("count")
        for row in queryset:
            unit_price = round(row.price / row.count, 3)
            line = f">={row.count} ¥{unit_price}/条"
            text_list.append(line)
            price_count_list.append((row.count, row.price))

        price_count_list.reverse()
        # print(price_count_list) # [(3000, Decimal('25.00')), (2000, Decimal('18.00')), (1000, Decimal('10.00'))]
        self.price_count_list = price_count_list
        self.fields['count'].help_text = "；".join(text_list)

    def clean_count(self):
        count = self.cleaned_data['count']

        if not self.price_count_list:
            raise ValidationError("请联系管理员设置价格")

        min_count = self.price_count_list[-1][0]
        if count < min_count:
            raise ValidationError(f"最低下单数量:{min_count}")
        return count


def yang_add(request):
    origin = request.GET.get("redirect", "/home/")

    if request.method == "GET":
        form = YangModelForm()
        return render(request, "user/form.html", {"form": form})

    form = YangModelForm(data=request.POST)
    if not form.is_valid():
        return render(request, "user/form.html", {"form": form})

    video_url = form.cleaned_data['url']
    count = int(form.cleaned_data['count'])

    # 1.原视频播放量采集
    from utils.video import get_old_view_count
    status, view_count = get_old_view_count(video_url)
    if not status:
        form.add_error("url", "视频原播放量采集失败")
        return render(request, "user/form.html", {"form": form})

    # 2.订单号
    while True:
        ctime = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        rand_number = random.randint(10000000, 99999999)
        oid = f"{ctime}{rand_number}"
        exists = models.Order.objects.filter(oid=oid).exists()
        if not exists:
            break

    # 3.价格
    for df_count, df_price in form.price_count_list:
        if count >= df_count:
            total_price = round(df_price / df_count * count, 2)
            break

    try:
        with transaction.atomic():
            cus_object = models.Customer.objects.filter(id=request.nb_user.id).select_for_update().first()
            real_price = round(total_price * cus_object.level.percent / 100, 2)
            if cus_object.balance < real_price:
                form.add_error("count", f"账户余额不足，余额：{cus_object.balance}，当前订单价格：{real_price}")
                return render(request, "user/form.html", {"form": form})

            # 创建订单
            form.instance.old_view_count = view_count
            form.instance.oid = oid
            form.instance.price = total_price
            form.instance.real_price = real_price
            form.instance.customer_id = request.nb_user.id
            form.save()

            # 客户账户扣款
            models.Customer.objects.filter(id=request.nb_user.id).update(balance=F("balance") - real_price)

            # 生成交易记录
            models.TransactionRecord.objects.create(
                charge_type=3,
                customer_id=request.nb_user.id,
                amount=real_price,
                order_oid=oid
            )

            # 将订单号加入队列（redis）    ->   [元素,]   ->
            conn = get_redis_connection("default")
            conn.lpush("nb_task_queue", oid)
    except Exception as e:
        form.add_error("count", "订单创建失败")
        return render(request, "user/form.html", {"form": form})

    return redirect(origin)


def yang_cancel(request, pk):
    origin = request.GET.get("redirect", "/home/")
    order_object = models.Order.objects.filter(id=pk, active=1, status=1, customer_id=request.nb_user.id).first()

    # 订单不存在，或已经撤单
    if not order_object:
        # message发送错误信息
        messages.add_message(request, settings.MESSAGE_DANDER_TAG, "订单不存在")
        return redirect(origin)

    # 撤单
    try:
        with transaction.atomic():
            models.Customer.objects.filter(id=request.nb_user.id).select_for_update()

            # 1.订单状态变已撤单
            models.Order.objects.filter(id=pk, active=1, status=1, customer_id=request.nb_user.id).update(status=5)

            # 2.归还余额
            models.Customer.objects.filter(id=request.nb_user.id).update(balance=F("balance") + order_object.real_price)

            # 3.交易记录（撤单）
            models.TransactionRecord.objects.create(
                charge_type=5,
                customer_id=request.nb_user.id,
                amount=order_object.real_price,
                order_oid=order_object.oid
            )

            # 提示
            messages.add_message(request, messages.SUCCESS, "撤单成功")
            return redirect(origin)
    except Exception as e:
        messages.add_message(request, settings.MESSAGE_DANDER_TAG, f"撤单失败，{e}")
        return redirect(origin)
