from django.shortcuts import render, redirect
from www import models
from django import forms

from utils.bootstrap import BootStrapForm
from utils.pager import Pagination


class LevelModelForm(BootStrapForm, forms.ModelForm):
    class Meta:
        model = models.Level
        fields = ["title", "percent"]


def level_list(request):
    queryset = models.Level.objects.filter(active=1).order_by("-percent")
    pager = Pagination(request, queryset)
    return render(request, "level_list.html", {"pager": pager})


def level_add(request):
    origin = request.GET.get("redirect")
    if request.method == "GET":
        form = LevelModelForm()
        return render(request, "form2.html", {"form": form})

    form = LevelModelForm(data=request.POST)
    if not form.is_valid():
        return render(request, "form2.html", {"form": form})

    form.save()
    return redirect(origin)


def level_edit(request, nid):
    origin = request.GET.get("redirect")
    instance = models.Level.objects.filter(id=nid, active=1).first()

    if request.method == "GET":
        form = LevelModelForm(instance=instance)
        return render(request, "form2.html", {"form": form})

    form = LevelModelForm(data=request.POST, instance=instance)
    if not form.is_valid():
        return render(request, "form2.html", {"form": form})

    form.save()
    return redirect(origin)


def level_delete(request, nid):
    origin = request.GET.get("redirect")
    if request.method == "GET":
        return render(request, 'delete.html', {"origin": origin})

    # models.Level.objects.filter(id=nid, active=1).delete()
    models.Level.objects.filter(id=nid, active=1).update(active=0)
    return redirect(origin)
