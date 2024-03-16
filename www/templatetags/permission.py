from django.http import QueryDict
from django.template import Library
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

register = Library()


@register.inclusion_tag("tag/breadcrumb.html")
def nb_breadcrumb(request):
    permission_dict = settings.NB_PERMISSIONS[request.nb_user.role]
    url_name = request.resolver_match.url_name
    text_list = []
    current_dict = permission_dict.get(url_name)
    text_list.insert(0, {"text": current_dict['text'], "name": url_name})
    parent = current_dict['parent']
    while parent:
        loop = permission_dict[parent]
        # text_list.insert(0, loop['text'])
        text_list.insert(0, {"text": loop['text'], "name": parent})
        parent = loop['parent']

    text_list.insert(0, {"text": "Homepage", "name": "home"})
    return {'text_list': text_list}


@register.filter
def has_permission(request, name):
    # print(request, name)

    # 获取当前用户所有的权限
    permission_dict = settings.NB_PERMISSIONS[request.nb_user.role]

    # 是否有权限
    if name in permission_dict:
        return True
    return False


@register.filter
def has_no_permission(request, name_string):
    # print(request, name)

    # 获取当前用户所有的权限
    permission_dict = settings.NB_PERMISSIONS[request.nb_user.role]

    # 是否有权限
    if name_string in permission_dict:
        return True
    return False



@register.simple_tag()
def gen_and_permission(request, name, title, *args, **kwargs):
    # 1.校验是否有权限
    permission_dict = settings.NB_PERMISSIONS[request.nb_user.role]
    if name not in permission_dict:
        return ""

    # 2.生成HTML链接
    url = reverse(name, args=args, kwargs=kwargs)
    html = f'<a href="{url}">{title}</a>'

    return mark_safe(html)
