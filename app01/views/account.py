import random

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django_redis import get_redis_connection
from django.conf import settings

from app01 import models
from utils import huyi_sms
from utils.encrypt import md5
from utils.reponse import BaseResponse
from app01.forms.account import LoginForm, MobileForm, SmsLoginForm



# 验证用户输入的数据格式是否为空
# 1. 定义类
from django import forms


# def login(request):
#     if request.method == "GET":
#         form = LoginForm()
#         return render(request, "login.html", {"form": form})
#
#     # 1. 接收并获取数据
#     form = LoginForm(data=request.POST)
#     if not form.is_valid():
#         return render(request, "login.html", {"form": form})
#
#     role = form.cleaned_data.get("role")
#     username = form.cleaned_data.get("username")
#     password = form.cleaned_data.get("password")
#     password = md5(password)
#
#     # 2. 去数据库校验
#     # 登录的时候需要选择自己的角色是客户还是管理员，后台存储角色的值时 1--> 管理员 2--> 客户
#     # 需要导入models.py：from app01 import models
#     mapping = {
#         "1": "ADMIN",
#         "2": "CUSTOMER"
#     }
#     if role not in mapping:
#         return render(request, "login.html", {'form': form, 'error': "角色不存在"})
#
#     if role == 1:
#         user_object = models.Administrator.objects.filter(active=1, username=username, password=password).first()
#     else:
#         user_object = models.Customer.objects.filter(active=1, username=username, password=password).first()
#
#     #  2.1 校验失败
#     if not user_object:
#         return render(request, "login.html", {'form': form, 'error': "用户名或密码错误"})
#
#     #  2.2 校验成功
#     request.session['user_info'] = {
#         'role': mapping[role],
#         'name': user_object.username,
#         'id': user_object.id
#     }
#
#     return redirect(settings.LOGIN_HOME)

def login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "login.html", {"form": form})

    # 1.接收并获取数据(数据格式或是否为空验证 - Form组件 & ModelForm组件）
    form = LoginForm(data=request.POST)
    if not form.is_valid():
        return render(request, "login.html", {"form": form})

    # 2.去数据库校验  1管理员  2客户
    data_dict = form.cleaned_data
    role = data_dict.pop('role')
    if role == "1":
        user_object = models.Administrator.objects.filter(active=1).filter(**data_dict).first()
    else:
        user_object = models.Customer.objects.filter(active=1).filter(**data_dict).first()

    # 2.1 校验失败
    if not user_object:
        form.add_error("username", "用户名或密码错误")
        return render(request, "login.html", {'form': form})

    # 2.2 校验成功，用户信息写入session+进入项目后台
    mapping = {"1": "ADMIN", "2": "CUSTOMER"}
    request.session['user_info'] = {'role': mapping[role], 'name': user_object.username, 'id': user_object.id}

    return redirect(settings.LOGIN_HOME)
def sms_send(request):
    """ 发送短信  """
    res = BaseResponse()

    # 校验数据合法性：手机号的格式 + 角色
    form = MobileForm(data=request.POST)
    if not form.is_valid():
        res.detail = form.errors
        return JsonResponse(res.dict, json_dumps_params={"ensure_ascii": False})
    res.status = True
    return JsonResponse(res.dict)


def sms_login(request):
    if request.method == "GET":
        form = SmsLoginForm()
        return render(request, "sms_login.html", {'form': form})

    res = BaseResponse()
    # 1.手机格式校验
    form = SmsLoginForm(data=request.POST)
    if not form.is_valid():
        res.detail = form.errors
        return JsonResponse(res.dict)

    role = form.cleaned_data['role']
    mobile = form.cleaned_data['mobile']
    # 3.登录成功 + 注册  （监测手机号是否存在）
    #     - 未注册，自动注册
    #     - 已注册，直接登录
    if role == "1":
        user_object = models.Administrator.objects.filter(active=1, mobile=mobile).first()
    else:
        user_object = models.Customer.objects.filter(active=1, mobile=mobile).first()

    if not user_object:
        res.detail = {"mobile": ["手机号不存在"]}
        return JsonResponse(res.dict)

    # 2.2 校验成功，用户信息写入session+进入项目后台
    mapping = {"1": "ADMIN", "2": "CUSTOMER"}
    request.session['user_info'] = {'role': mapping[role], 'name': user_object.username, 'id': user_object.id}
    res.status = True
    res.data = settings.LOGIN_HOME
    return JsonResponse(res.dict)

def logout(request):
    """ 注销 """
    request.session.clear()
    return redirect(settings.NB_LOGIN_URL)
def home(request):
    return render(request, 'home.html')

