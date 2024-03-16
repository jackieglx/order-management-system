from django.shortcuts import render
from www import models
from django.utils.safestring import mark_safe


class Row(object):
    def __init__(self, option, title, queryset, request):
        self.option = option
        self.title = title
        self.queryset = queryset
        self.query_dict = request.GET

    def __iter__(self):
        query_dict = self.query_dict.copy()
        query_dict._mutable = True

        yield '<div class="whole">'
        yield self.title
        yield '</div>'

        yield '<div class="others">'

        if query_dict.getlist(self.option):
            query_dict.pop(self.option)
            yield f"<a href='?{query_dict.urlencode()}'>全部</a>"
        else:
            yield f"<a class='active' href='?{query_dict.urlencode()}'>全部</a>"

        for obj in self.queryset:
            # 读取原来的值  [3]  [4,3]
            loop_query_dict = self.query_dict.copy()
            loop_query_dict._mutable = True

            value_list = loop_query_dict.getlist(self.option)

            query_dict.setlist(self.option, [obj.pk])
            url = query_dict.urlencode()
            if str(obj.pk) in value_list:
                yield f"<a class='active' href='?{url}'>{obj}</a>"  # 对象.__str__
            else:
                yield f"<a href='?{url}'>{obj}</a>"  # 对象.__str__

        yield '</div>'


class SearchGroup(object):
    def __init__(self, model_class, request, *options):
        # ("level", "creator")
        self.model_class = model_class
        self.request = request
        self.options = options

    def get_row_list(self):
        row_list = []
        for option in self.options:
            # 获取字段关联的所有数据
            field_object = self.model_class._meta.get_field(option)

            title = field_object.verbose_name
            # print(field_object.related_model)
            # print(field_object.remote_field.model)
            queryset = field_object.related_model.objects.all()
            # print(queryset)
            # 将数据封装到row中
            obj = Row(option, title, queryset, self.request)
            row_list.append(obj)
        return row_list

    def get_condition(self):
        condition = {}

        # "level", "creator"
        for option in self.options:
            value = self.request.GET.get(option)
            if not value:
                continue
            condition[option] = value
        return condition


def demo(request):
    # 只支持FK组件："level"  "creator"
    group = SearchGroup(models.Customer, request, "level", "creator")
    row_list = group.get_row_list()
    condition = group.get_condition()

    queryset = models.Customer.objects.filter(**condition).order_by("-id")
    return render(request, 'v1_demo.html', {"queryset": queryset, "row_list": row_list})
