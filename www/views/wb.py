from django.shortcuts import render, redirect
from utils.pager import Pagination

from www import models

from django.shortcuts import render, redirect, HttpResponse
from www import models
from django import forms
from utils.bootstrap import BootStrapForm
from utils.pager import Pagination
from django.http.request import QueryDict
from django.urls import path

from django.db.models import Q
from django.utils.safestring import mark_safe
from utils.encrypt import md5_string
from django.core.exceptions import ValidationError
from django.urls import reverse
from urllib.parse import quote_plus, unquote_plus


class BaseCurd(object):
    list_template_name = "wb_list.html"
    add_template = "form2.html"
    edit_template = "form2.html"

    search_list = []

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

        pager = Pagination(request, queryset)
        context = {
            "pager": pager,

            "url_add_name": f"{self.prefix}_add",
            "url_edit_name": f"{self.prefix}_edit",
            "url_delete_name": f"{self.prefix}_delete",

            "table_header": self.table_header,
            "table_field": self.table_field,

            "search_list": self.search_list,
            "keyword": keyword
        }
        return render(request, self.list_template_name, context)

    def add(self, request):
        form_class = self.add_form_class

        origin = request.GET.get("redirect")
        if request.method == "GET":
            form = form_class()
            return render(request, self.add_template, {"form": form})

        form = form_class(data=request.POST)
        if not form.is_valid():
            return render(request, self.add_template, {"form": form})

        self.add_save(form, request)

        return redirect(origin)

    def add_save(self, form, request):
        # self.request
        form.save()

    def get_instance(self, request, nid):
        return self.instance

    def edit(self, request, pk):
        origin = request.GET.get("redirect")
        # instance = models.Level.objects.filter(id=nid, active=1).first()
        instance = self.get_instance(request, pk)
        form_class = self.edit_form_class

        if request.method == "GET":
            form = form_class(instance=instance)
            return render(request, self.edit_template, {"form": form})

        form = form_class(data=request.POST, instance=instance)
        if not form.is_valid():
            return render(request, self.edit_template, {"form": form})

        # form.save()
        self.edit_save(form, request)

        return redirect(origin)

    def edit_save(self, form, request):
        form.save()

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


class Price4(BaseCurd):
    queryset = models.PricePolicy.objects.all().order_by("count")

    table_header = ["数量", "价格"]
    table_field = [("db", "count"), ("db", "price")]

    add_form_class = PriceModelForm
    edit_form_class = PriceModelForm

    # search_list = ["count__contains"]

    def get_instance(self, request, nid):
        return models.PricePolicy.objects.filter(id=nid).first()

    def do_delete(self, request, nid):
        models.PricePolicy.objects.filter(id=nid).delete()


# ################ 级别管理 ################
class LevelModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.Level
        fields = ["title", "percent"]


class Level4(BaseCurd):
    queryset = models.Level.objects.filter(active=1).order_by("-percent")

    search_list = ["title__contains"]

    table_header = ["标题", "百分比", "更多"]

    def more(instance):
        # return f"测试-{instance.title}-{instance.percent}"
        return mark_safe(f"<a href='#'>测试-{instance.title}-{instance.percent}</a>")

    # table_field = ["title", "percent"]
    table_field = [("db", "title"), ("db", "percent"), ("func", more)]

    add_form_class = LevelModelForm
    edit_form_class = LevelModelForm

    def get_instance(self, request, nid):
        return models.Level.objects.filter(id=nid).first()

    def do_delete(self, request, nid):
        models.Level.objects.filter(id=nid, active=1).update(active=0)


# ################ 客户管理 ################
class CustomerModelForm(BootStrapForm, forms.ModelForm):
    exclude_field_list = ['level']

    confirm_password = forms.CharField(
        label="重复密码",
        widget=forms.PasswordInput(render_value=True)
    )

    class Meta:
        model = models.Customer
        fields = ['level', "username", 'mobile', 'password', 'confirm_password', ]
        widgets = {
            'password': forms.PasswordInput(render_value=True),
            "level": forms.RadioSelect(attrs={'class': "form-radio"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['level'].queryset = models.Level.objects.filter(active=1)

    def clean_password(self):
        password = self.cleaned_data['password']

        return md5_string(password)

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = md5_string(self.cleaned_data.get('confirm_password', ''))

        if password != confirm_password:
            raise ValidationError("密码不一致")
        return confirm_password


class CustomerEditModelForm(BootStrapForm, forms.ModelForm):
    exclude_field_list = ['level']

    class Meta:
        model = models.Customer
        fields = ['level', "username", 'mobile', ]
        widgets = {
            "level": forms.RadioSelect(attrs={'class': "form-radio"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['level'].queryset = models.Level.objects.filter(active=1)


class CustomerResetModelForm(BootStrapForm, forms.ModelForm):
    confirm_password = forms.CharField(
        label="重复密码",
        widget=forms.PasswordInput(render_value=True)
    )

    class Meta:
        model = models.Customer
        fields = ['password', 'confirm_password', ]
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }

    def clean_password(self):
        password = self.cleaned_data['password']

        return md5_string(password)

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = md5_string(self.cleaned_data.get('confirm_password', ''))

        if password != confirm_password:
            raise ValidationError("密码不一致")
        return confirm_password


class Customer4(BaseCurd):
    add_template = "form.html"
    edit_template = "form.html"

    queryset = models.Customer.objects.filter(active=1).order_by("-id")
    search_list = ["username", "mobile__contains"]

    table_header = ["用户名", "手机号", "级别", "创建日期", "重置密码"]

    def get_level(request, instance):
        return f"{instance.level.title}（{instance.level.percent}%折扣）"

    def get_create_date(request, instance):
        return instance.create_date.strftime("%Y-%m-%d")

    def get_reset(request, instance):
        url = reverse(viewname=f"customer4_reset", kwargs={"pk": instance.id})
        # request获取当前请求地址
        current_url = request.get_full_path()
        param = quote_plus(current_url)
        return mark_safe(f"<a href='{url}?redirect={param}'>重置密码</a>")

    table_field = [("db", "username"), ("db", "mobile"), ("func", get_level), ("func", get_create_date),
                   ("func", get_reset)]

    add_form_class = CustomerModelForm
    edit_form_class = CustomerEditModelForm

    def get_instance(self, request, nid):
        return models.Customer.objects.filter(id=nid, active=1).first()

    def add_save(self, form, request):
        # form.instance.creator_id = self.request.nb_user.id
        form.instance.creator_id = request.nb_user.id
        form.save()

    def do_delete(self, request, pk):
        models.Customer.objects.filter(id=pk, active=1).update(active=0)

    def get_extra_url(self):
        return [
            path(f'reset/<int:pk>/', self.reset, name=f"{self.prefix}_reset")
        ]

    def reset(self, request, pk):
        origin = request.GET.get("redirect", "/home/")

        if request.method == "GET":
            form = CustomerResetModelForm()
            return render(request, "form.html", {"form": form})

        instance = models.Customer.objects.filter(id=pk, active=1).first()
        form = CustomerResetModelForm(data=request.POST, instance=instance)
        if not form.is_valid():
            return render(request, 'form.html', {'form': form})

        form.save()
        return redirect(origin)
