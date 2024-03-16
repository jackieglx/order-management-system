"""
使用说明：
1.在视图函数中
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

    queryset = models.Customer.objects.filter(**group.get_condition()).order_by("-id")
    return render(request, 'v2_demo.html', {"queryset": queryset, "row_list": group.get_row_list()})

2.在HTML中
    <link rel="stylesheet" href="{% static 'css/search-group.css' %}">

    {% include 'include/search_group.html' %}
"""

from django.db.models import ForeignKey, ManyToManyField


class Row(object):
    def __init__(self, opt_object, title, queryset_or_list, request):
        self.opt_object = opt_object
        self.title = title
        self.queryset_or_list = queryset_or_list
        self.query_dict = request.GET

    def __iter__(self):

        # self.opt_object.is_multi

        query_dict = self.query_dict.copy()
        query_dict._mutable = True

        yield '<div class="whole">'
        yield self.title
        yield '</div>'

        yield '<div class="others">'

        if query_dict.getlist(self.opt_object.field):
            query_dict.pop(self.opt_object.field)
            yield f"<a href='?{query_dict.urlencode()}'>全部</a>"
        else:
            yield f"<a class='active' href='?{query_dict.urlencode()}'>全部</a>"
        # [(1, '男'), (2, '女')]
        # [对象,对象,对象]
        # opt_object.is_choice
        for obj in self.queryset_or_list:
            # if self.opt_object.is_choice:
            #     text = obj[1]
            #     value = str(obj[0])
            # else:
            #     text = str(obj)  # obj.__str__
            #     value = str(obj.pk)

            # text = self.opt_object.text_func(obj)
            # value = self.opt_object.value_func(obj)
            text = self.opt_object.get_text(obj)
            value = self.opt_object.get_value(obj)

            if self.opt_object.is_multi:
                # 多选逻辑
                loop_query_dict = self.query_dict.copy()
                loop_query_dict._mutable = True
                old_list = loop_query_dict.getlist(self.opt_object.field)

                # http://127.0.0.1:8000/v2/demo/?level=4&level=5
                # old_list = ["5"]
                if value in old_list:
                    old_list.remove(value)
                    loop_query_dict.setlist(self.opt_object.field, old_list)
                    url = loop_query_dict.urlencode()
                    yield f"<a class='active' href='?{url}'>{text}</a>"  # 对象.__str__
                else:
                    # old_list = [4,5,1]
                    old_list.append(value)
                    loop_query_dict.setlist(self.opt_object.field, old_list)

                    url = loop_query_dict.urlencode()
                    yield f"<a href='?{url}'>{text}</a>"  # 对象.__str__

            else:
                # 读取原来的值  [3]  [4,3]
                loop_query_dict = self.query_dict.copy()
                loop_query_dict._mutable = True
                value_list = loop_query_dict.getlist(self.opt_object.field)
                query_dict.setlist(self.opt_object.field, [value])
                url = query_dict.urlencode()
                if value in value_list:
                    yield f"<a class='active' href='?{url}'>{text}</a>"  # 对象.__str__
                else:
                    yield f"<a href='?{url}'>{text}</a>"  # 对象.__str__

        yield '</div>'


class SearchGroup(object):
    def __init__(self, model_class, request, *options):
        # ("level", "creator")
        self.model_class = model_class
        self.request = request
        self.options = options  # [Option("level", True),   Option("creator", False)]

    def get_row_list(self):
        row_list = []
        for opt_object in self.options:
            # # [Option("level", True),   Option("creator", False), Option("gender")]

            # 获取字段关联的所有数据
            field_object = self.model_class._meta.get_field(opt_object.field)
            title = field_object.verbose_name
            if opt_object.is_choice:
                # [(1, '男'), (2, '女')]
                queryset_or_list = field_object.choices
            else:
                # print(field_object,type(field_object))
                if isinstance(field_object, ForeignKey) or isinstance(field_object, ManyToManyField):
                    # [对象,对象,对象]
                    # print(field_object.related_model)
                    # print(field_object.remote_field.model)
                    # queryset = field_object.related_model.objects.filter(**opt_object.db_condition)
                    queryset_or_list = opt_object.get_queryset(field_object.related_model, self.request)
                else:
                    # 当前表中的数据
                    # [Customer对象，Customer对象，Customer对象，Customer对象，]
                    queryset_or_list = self.model_class.objects.filter(**opt_object.db_condition)

            # print(queryset)
            # 将数据封装到row中
            obj = Row(opt_object, title, queryset_or_list, self.request)
            row_list.append(obj)
        return row_list

    # @property
    def get_condition(self):
        condition = {}
        # "level", "creator"
        for opt_object in self.options:
            field, value = opt_object.get_search_condition(self.request)
            if not value:
                continue
            condition[field] = value

        return condition


class Option(object):
    def __init__(self, field, is_multi=False, db_condition=None, is_choice=False, text_func=None, value_func=None):
        self.field = field
        self.is_multi = is_multi
        if not db_condition:
            db_condition = {}
        self.db_condition = db_condition
        self.is_choice = is_choice
        self.text_func = text_func
        self.value_func = value_func

    def get_search_condition(self, request):
        if self.is_multi:
            value = request.GET.getlist(self.field)
            return f"{self.field}__in", value
        else:
            value = request.GET.get(self.field)
            return self.field, value

    def get_queryset(self, related_model, request):
        return related_model.objects.filter(**self.db_condition)

    def get_text(self, obj_or_tuple):
        if self.text_func:
            return self.text_func(obj_or_tuple)

        if self.is_choice:
            return obj_or_tuple[1]

        return str(obj_or_tuple)

    def get_value(self, obj_or_tuple):
        if self.value_func:
            return self.value_func(obj_or_tuple)

        if self.is_choice:
            return str(obj_or_tuple[0])

        return str(obj_or_tuple.pk)
