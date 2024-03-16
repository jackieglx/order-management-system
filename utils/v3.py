from django.shortcuts import render, redirect
from utils.pager import Pagination
from django.urls import path
from django import forms

from django.db.models import Q
from django.urls import reverse
from urllib.parse import quote_plus, unquote_plus
from utils.bootstrap import BootStrapForm

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


def get_datetime_field(field, fmt):
    def inner(request, instance):
        return getattr(instance, field).strftime(fmt)

    return inner


def get_choice_field(field):
    def inner(request, instance):
        # 对象.get_field_display  ()
        # return getattr(instance, field).strftime(fmt)
        return getattr(instance, f"get_{field}_display")()

    return inner


def gen_url(request, name, kwargs):
    prev = reverse(name, kwargs=kwargs)
    current_url = request.get_full_path()
    param = quote_plus(current_url)
    return f"{prev}?redirect={param}"


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
    def __init__(self, request, model_class, *options):
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


class BaseCurd(object):
    list_template_name = "v3/list.html"
    add_template = "v3/form2.html"
    edit_template = "v3/form2.html"
    delete_template = "v3/delete.html"

    search_list = []

    search_group = []

    base_form_model = None
    base_form_fields = None

    add_form_class = None
    add_form_model = None
    add_form_fields = None

    edit_form_class = None
    edit_form_model = None
    edit_form_fields = None

    def __init__(self, view_list, prefix):
        self.view_list = view_list
        self.prefix = prefix

    def dispatch(self, func):
        def inner(request, *args, **kwargs):
            self.request = request
            res = func(request, *args, **kwargs)
            return res

        return inner

    @classmethod
    def urls(cls, view_list=None, prefix=None):
        if not view_list:
            view_list = ["list", "add", "edit", "delete"]
        if not prefix:
            prefix = cls.__name__.lower()

        # 实例化对象
        instance = cls(view_list, prefix)

        router = []
        for item in view_list:
            func = getattr(instance, item)
            if item in ["list", "add"]:
                # router.append(path(f'{item}/', func, name=f"{prefix}_{item}"))
                router.append(path(f'{item}/', instance.dispatch(func), name=f"{prefix}_{item}"))
            else:
                router.append(path(f'{item}/<int:pk>/', instance.dispatch(func), name=f"{prefix}_{item}"))

        extra_router = instance.get_extra_url()
        if extra_router:
            router.extend(extra_router)

        return router, None, None

    def get_extra_url(self):
        pass

    def get_queryset(self, request):
        return self.queryset

    def list(self, request):
        keyword = request.GET.get("keyword", "").strip()
        queryset = self.get_queryset(request)

        # 如果加入关键字搜索  queryset = queryset.filter(Q对象)
        if self.search_list:
            con = Q()
            if keyword:
                con.connector = "OR"
                for fd in self.search_list:
                    con.children.append((fd, keyword))
            queryset = queryset.filter(con)

        search_row_list = []
        if self.search_group:
            group = SearchGroup(
                request,
                *self.search_group
            )
            queryset = queryset.filter(**group.get_condition())
            search_row_list = group.get_row_list()

        pager = Pagination(request, queryset)
        context = {
            "pager": pager,

            "url_add_name": f"{self.prefix}_add",
            "url_edit_name": f"{self.prefix}_edit",
            "url_delete_name": f"{self.prefix}_delete",

            "table_header": self.table_header,
            "table_field": self.table_field,

            "search_list": self.search_list,
            "keyword": keyword,

            "search_group": self.search_group,
            "search_row_list": search_row_list
        }
        return render(request, self.list_template_name, context)

    def get_add_form_class(self):
        if self.add_form_class:
            return self.add_form_class

        # 用户未指定add_form_class，动态生成
        meta_cls = type("Meta", (object,), {"model": self.add_form_model or self.base_form_model,
                                            "fields": self.add_form_fields or self.base_form_fields})
        model_form_cls = type("DynamicModelForm", (BootStrapForm, forms.ModelForm), {"Meta": meta_cls})
        return model_form_cls

    def add(self, request):
        form_class = self.get_add_form_class()

        origin = request.GET.get("redirect")
        if request.method == "GET":
            form = form_class()
            return render(request, self.add_template, {"form": form})

        form = form_class(data=request.POST)
        if not form.is_valid():
            return render(request, self.add_template, {"form": form})

        res = self.add_save(form, request)
        if res:
            return res
        return redirect(origin)

    def add_save(self, form, request):
        form.save()

    def get_instance(self, request, pk):
        # return self.instance
        queryset = self.get_queryset(request)
        instance = queryset.filter(id=pk).first()
        return instance

    def get_edit_form_class(self):
        if self.edit_form_class:
            return self.edit_form_class

        # 用户未指定add_form_class，动态生成
        meta_cls = type("Meta", (object,), {"model": self.add_form_model or self.base_form_model,
                                            "fields": self.add_form_fields or self.base_form_fields})
        model_form_cls = type("DynamicModelForm", (BootStrapForm, forms.ModelForm), {"Meta": meta_cls})
        return model_form_cls

    def edit(self, request, pk):
        origin = request.GET.get("redirect")
        # instance = models.Level.objects.filter(id=nid, active=1).first()
        instance = self.get_instance(request, pk)
        form_class = self.get_edit_form_class()

        if request.method == "GET":
            form = form_class(instance=instance)
            return render(request, self.edit_template, {"form": form})

        form = form_class(data=request.POST, instance=instance)
        if not form.is_valid():
            return render(request, self.edit_template, {"form": form})

        # form.save()
        res = self.edit_save(form, request)
        return res or redirect(origin)

    def edit_save(self, form, request):
        form.save()

    def delete(self, request, pk):
        origin = request.GET.get("redirect")
        if request.method == "GET":
            return render(request, self.delete_template, {"origin": origin})

        res = self.do_delete(request, pk)
        return res or redirect(origin)

    def do_delete(self, request, pk):
        queryset = self.get_queryset(request)
        queryset.filter(id=pk).delete()
