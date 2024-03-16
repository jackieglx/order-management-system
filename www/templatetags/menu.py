import json
import copy
from django.http import QueryDict
from django.template import Library
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

register = Library()


@register.inclusion_tag("tag/menu.html")
def nb_menu(request):
    current_url = request.path_info

    # 读取配置文件中的菜单的配置
    menu_list = copy.deepcopy(settings.NB_MENUS[request.nb_user.role])
    for item in menu_list:
        # item['class'] = "hide"
        for child in item['children']:
            if child['url'] == current_url:
                child['class'] = "active"
                # item['class'] = ""

    # print(menu_list)
    # print(json.dumps(menu_list, indent=2))
    return {"menu_list": menu_list}
