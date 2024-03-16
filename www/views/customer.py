from django.shortcuts import render, redirect
from www import models
from django import forms
from django.core.exceptions import ValidationError

from utils.bootstrap import BootStrapForm
from utils.pager import Pagination
from utils.encrypt import md5_string

from django.db.models import Q


def customer_list(request):
    keyword = request.GET.get("keyword", "").strip()

    # 传统的筛选
    # models.Customer.objects.filter(active=1).filter(username__contains=keyword,mobile__contains=keyword).order_by("-id")

    # Q查询
    con = Q()
    if keyword:
        con.connector = "OR"
        con.children.append(("username__contains", keyword))
        con.children.append(("mobile__contains", keyword))
        con.children.append(("level__title__contains", keyword))

    queryset = models.Customer.objects.filter(active=1).filter(con).order_by("-id")
    pager = Pagination(request, queryset)

    from django.contrib.messages.api import get_messages
    # messages = get_messages(request)
    # print(messages)
    # for msg in messages:
    #     from django.contrib.messages.storage.base import Message
    #     # print("每个msg->", type(msg), msg)
    #     print("每个msg->", msg.level, msg.message)

    return render(request, "customer_list.html", {"pager": pager, "keyword": keyword})


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


def customer_add(request):
    origin = request.GET.get("redirect", "/home/")

    if request.method == "GET":
        form = CustomerModelForm()
        return render(request, "form.html", {"form": form})

    form = CustomerModelForm(data=request.POST)
    if not form.is_valid():
        return render(request, "form.html", {"form": form})

    form.instance.creator_id = request.nb_user.id
    form.save()

    from django.contrib import messages
    messages.add_message(request, messages.SUCCESS, "新建客户成功")

    return redirect(origin)


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


def customer_edit(request, pk):
    origin = request.GET.get("redirect", "/home/")
    instance = models.Customer.objects.filter(id=pk, active=1).first()

    if request.method == "GET":
        form = CustomerEditModelForm(instance=instance)
        return render(request, "form.html", {"form": form})

    form = CustomerEditModelForm(data=request.POST, instance=instance)
    if not form.is_valid():
        return render(request, "form.html", {"form": form})

    form.save()
    return redirect(origin)


def customer_delete(request, pk):
    origin = request.GET.get("redirect", "/home/")

    if request.method == "GET":
        return render(request, 'delete.html', {"origin": origin})

    models.Customer.objects.filter(id=pk, active=1).update(active=0)
    return redirect(origin)


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


def customer_reset(request, pk):
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
