from django.shortcuts import render
from www import models
from django.utils.safestring import mark_safe
from django.db.models import ForeignKey, ManyToManyField
from utils.search_group import SearchGroup, Option


def demo(request):
    # 只支持FK组件："level"  "creator"
    group = SearchGroup(
        models.Customer,
        request,
        Option("level", False, {"active": 0, "id__gt": 3}),
        Option("creator", False),
        Option("gender", is_choice=True),
        Option("mobile", db_condition={"id__lte": 4}, text_func=lambda x: x.mobile, value_func=lambda x: x.mobile),
        Option("hbs", True, text_func=lambda x: x.title)
    )

    row_list = group.get_row_list()
    condition = group.get_condition()

    queryset = models.Customer.objects.filter(**condition).order_by("-id")
    return render(request, 'v2_demo.html', {"queryset": queryset, "row_list": row_list})
