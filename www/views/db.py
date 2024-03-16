from django.shortcuts import render, redirect
from utils.pager import Pagination

from www import models

from django.shortcuts import render, redirect
from www import models
from django import forms
from utils.bootstrap import BootStrapForm
from utils.pager import Pagination
from django.http.request import QueryDict
from django.urls import path


class BaseCurd(object):
    list_template_name = "db_list.html"

    def __init__(self, view_list, prefix):
        self.view_list = view_list
        self.prefix = prefix

    def dispatch(self, func):
        def inner(request, *args, **kwargs):
            # self.request = request
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
        queryset = self.get_queryset(request)
        pager = Pagination(request, queryset)
        context = {
            "pager": pager,

            "url_add_name": f"{self.prefix}_add",
            "url_edit_name": f"{self.prefix}_edit",
            "url_delete_name": f"{self.prefix}_delete",

            "table_header": self.table_header,
            "table_field": self.table_field
        }
        return render(request, self.list_template_name, context)

    def add(self, request):
        form_class = self.form_class

        origin = request.GET.get("redirect")
        if request.method == "GET":
            form = form_class()
            return render(request, "form2.html", {"form": form})

        form = form_class(data=request.POST)
        if not form.is_valid():
            return render(request, "form2.html", {"form": form})

        form.save()
        return redirect(origin)

    def get_instance(self, request, nid):
        return self.instance

    def edit(self, request, pk):
        origin = request.GET.get("redirect")
        # instance = models.Level.objects.filter(id=nid, active=1).first()
        instance = self.get_instance(request, pk)
        form_class = self.form_class

        if request.method == "GET":
            form = form_class(instance=instance)
            return render(request, "form2.html", {"form": form})

        form = form_class(data=request.POST, instance=instance)
        if not form.is_valid():
            return render(request, "form2.html", {"form": form})

        form.save()
        return redirect(origin)

    def delete(self, request, pk):
        origin = request.GET.get("redirect")
        if request.method == "GET":
            return render(request, 'delete.html', {"origin": origin})

        # models.PricePolicy.objects.filter(id=nid).delete()
        self.do_delete(request, pk)
        return redirect(origin)

    def do_delete(self, request, pk):
        pass


# ################ 价格管理 ################
class PriceModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.PricePolicy
        fields = ["count", "price"]


class Price3(BaseCurd):
    queryset = models.PricePolicy.objects.all().order_by("count")

    table_header = ["数量", "价格"]
    table_field = ["count", "price"]

    form_class = PriceModelForm

    def get_instance(self, request, nid):
        return models.PricePolicy.objects.filter(id=nid).first()

    def do_delete(self, request, nid):
        models.PricePolicy.objects.filter(id=nid).delete()


# ################ 级别管理 ################
class LevelModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.Level
        fields = ["title", "percent"]


class Level3(BaseCurd):
    queryset = models.Level.objects.filter(active=1).order_by("-percent")

    table_header = ["标题", "百分比"]
    table_field = ["title", "percent"]
    # table_field = [("db", "title"), ("db", "percent"), ("func", more)]

    form_class = LevelModelForm

    def get_instance(self, request, nid):
        return models.Level.objects.filter(id=nid).first()

    def do_delete(self, request, nid):
        models.Level.objects.filter(id=nid, active=1).update(active=0)
