import json
import copy
from django.http import QueryDict
from django.template import Library
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from urllib.parse import quote_plus, unquote_plus
from www import models

register = Library()


@register.simple_tag()
def loop_counter(request, counter):
    page = request.GET.get("page", "1")
    if not page.isdecimal():
        page = "1"
    page = int(page)
    if page < 1:
        page = 1

    return (page - 1) * 20 + counter


@register.simple_tag()
def url_plus(request, name, *args, **kwargs):
    prev = reverse(name, args=args, kwargs=kwargs)
    # param = quote_plus("/level/list/?page=19&xx=10")

    # 获取当前请求的URL
    from django.core.handlers.wsgi import WSGIRequest
    current_url = request.get_full_path()
    param = quote_plus(current_url)

    return f"{prev}?redirect={param}"


@register.simple_tag()
def getattr_plus(obj, name):
    # 字符串 -> getattr(obj, name) / 函数 -> 执行获取返回值
    return getattr(obj, name)


@register.simple_tag()
def render_td(request, obj, group):
    # 字符串 -> getattr(obj, name) / 函数 -> 执行获取返回值
    category, name_func = group
    if category == "db":
        return getattr(obj, name_func)

    return name_func(request, obj)


@register.simple_tag()
def tran_amount(charge_type, amount):
    if charge_type in [2, 3]:
        return f"-{amount}"
    return f"+{amount}"


@register.simple_tag()
def tran_color_class(charge_type):
    return models.TransactionRecord.charge_type_class_mapping[charge_type]
