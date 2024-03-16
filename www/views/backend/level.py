from django.contrib import messages

from www import models
from utils.v3 import BaseCurd


class Level(BaseCurd):
    # 列表配置
    queryset = models.Level.objects.filter(active=1).order_by("percent")
    table_header = ["级别", "折扣"]
    table_field = [
        ("db", "title"),
        ("func", lambda req, ins: f"{ins.percent}%"),
    ]

    #  新增和编辑配置
    base_form_model = models.Level
    base_form_fields = ["title", "percent"]

    # # 新增配置
    # add_template = "v3/form.html"
    # add_form_model = models.Level
    # add_form_fields = ["title", "percent"]
    #
    # # 编辑配置
    # edit_template = "v3/form.html"
    # edit_form_model = models.Level
    # edit_form_fields = ["title", "percent"]

    # 删除
    def do_delete(self, request, pk):
        models.Level.objects.filter(active=1, id=pk).update(active=0)
        messages.add_message(request, messages.SUCCESS, "删除成功")
