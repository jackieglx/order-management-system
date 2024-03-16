from django.shortcuts import render, redirect
from utils.pager import Pagination

from www import models

from django.shortcuts import render, redirect
from www import models
from django import forms
from utils.bootstrap import BootStrapForm
from utils.pager import Pagination
from django.http.request import QueryDict


class PriceModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.PricePolicy
        fields = ["count", "price"]


class LevelModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.Level
        fields = ["title", "percent"]


class BaseCurd(object):
    list_template_name = "nb_list.html"

    @classmethod
    def list(cls, request):
        # cls=LevelCurd  PriceCurd
        queryset = cls.get_queryset(request)
        pager = Pagination(request, queryset)
        context = {
            "pager": pager,
            "url_add_name": cls.url_add_name,
            "url_edit_name": cls.url_edit_name,
            "url_delete_name": cls.url_delete_name,
            "table_header": cls.table_header,
            "table_field": cls.table_field
        }
        return render(request, cls.list_template_name, context)

    @classmethod
    def get_queryset(cls, request):
        return cls.queryset

    @classmethod
    def add(cls, request):
        form_class = cls.form_class

        origin = request.GET.get("redirect")
        if request.method == "GET":
            form = form_class()
            return render(request, "form2.html", {"form": form})

        form = form_class(data=request.POST)
        if not form.is_valid():
            return render(request, "form2.html", {"form": form})

        form.save()
        return redirect(origin)

    @classmethod
    def edit(cls, request, nid):
        origin = request.GET.get("redirect")
        # instance = models.Level.objects.filter(id=nid, active=1).first()
        instance = cls.get_instance(request, nid)
        form_class = cls.form_class

        if request.method == "GET":
            form = form_class(instance=instance)
            return render(request, "form2.html", {"form": form})

        form = form_class(data=request.POST, instance=instance)
        if not form.is_valid():
            return render(request, "form2.html", {"form": form})

        form.save()
        return redirect(origin)

    @classmethod
    def get_instance(cls, request, nid):
        return cls.instance

    @classmethod
    def delete(cls, request, nid):
        origin = request.GET.get("redirect")
        if request.method == "GET":
            return render(request, 'delete.html', {"origin": origin})

        # models.PricePolicy.objects.filter(id=nid).delete()
        cls.do_delete(request, nid)
        return redirect(origin)

    @classmethod
    def do_delete(cls, request, nid):
        pass


class LevelCurd(BaseCurd):
    url_add_name = "level2_add"
    url_edit_name = "level2_edit"
    url_delete_name = "level2_delete"

    table_header = ["标题", "折扣"]
    table_field = ["title", "percent"]

    queryset = models.Level.objects.filter(active=1).order_by("-percent")

    form_class = LevelModelForm

    @classmethod
    def get_instance(cls, request, nid):
        return models.Level.objects.filter(id=nid, active=1).first()

    @classmethod
    def do_delete(cls, request, nid):
        models.Level.objects.filter(id=nid, active=1).update(active=0)


class PriceCurd(BaseCurd):
    url_add_name = "price2_add"
    url_edit_name = "price2_edit"
    url_delete_name = "price2_delete"

    table_header = ["数量", "价格"]
    table_field = ["count", "price"]

    queryset = models.PricePolicy.objects.all().order_by("count")

    form_class = PriceModelForm

    @classmethod
    def get_instance(cls, request, nid):
        return models.PricePolicy.objects.filter(id=nid).first()

    @classmethod
    def do_delete(cls, request, nid):
        models.PricePolicy.objects.filter(id=nid).delete()


class CustomerCurd(BaseCurd):
    url_add_name = None
    url_edit_name = "price_edit"
    url_delete_name = "price_delete"

    table_header = ["用户名", "手机"]
    table_field = ["username", "mobile"]

    queryset = models.Customer.objects.all().order_by("id")
