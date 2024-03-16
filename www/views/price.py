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


def price_list(request):
    # 去数据库中获取所有的级别列表
    queryset = models.PricePolicy.objects.all().order_by("count")
    pager = Pagination(request, queryset)
    return render(request, "price_list.html", {"pager": pager})




def price_add(request):
    origin = request.GET.get("redirect")
    if request.method == "GET":
        form = PriceModelForm()
        return render(request, "form2.html", {"form": form})

    form = PriceModelForm(data=request.POST)
    if not form.is_valid():
        return render(request, "form2.html", {"form": form})

    form.save()
    return redirect(origin)


def price_edit(request, nid):
    origin = request.GET.get("redirect")
    instance = models.PricePolicy.objects.filter(id=nid).first()

    if request.method == "GET":
        form = PriceModelForm(instance=instance)
        return render(request, "form2.html", {"form": form})

    form = PriceModelForm(data=request.POST, instance=instance)
    if not form.is_valid():
        return render(request, "form2.html", {"form": form})

    form.save()
    return redirect(origin)


def price_delete(request, nid):
    origin = request.GET.get("redirect")
    if request.method == "GET":
        return render(request, 'delete.html', {"origin": origin})

    models.PricePolicy.objects.filter(id=nid).delete()
    return redirect(origin)
