from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from www.forms.account import LoginForm, SmsLoginForm, SendSmsForm
from www import models
from django.shortcuts import HttpResponse


def login(request):
    # 1.GET请求看到登录页面
    if request.method == "GET":
        form = LoginForm()  # 创建一个 LoginForm 类的实例，该实例将用于在登录页面上渲染登录表单。
        return render(request, "login.html", {"form": form})
                                                                # 在模板中，你可以通过 form 这个键来访问 LoginForm 实例

    # 2.用户提交
    # 2.1 是否为空
    form = LoginForm(data=request.POST) # 在Django中，表单类的实例化通常需要传递一个data参数，为了将用户通过 POST 方法提交的数据传递给表单实例进行处理
    if not form.is_valid():
        return render(request, "login.html", {"form": form})
    # is_valid()是 Django表单类提供的方法，用于检查表单字段的数据是否符合字段定义的验证规则，
    # Django 表单在处理数据时会默认进行一些基本的验证，包括检查是否有必填字段为空



    # 2.2 去数据库校验：客户表？管理员表？
    data_dict = form.cleaned_data
    # cleaned_data是Django 表单类的一个属性，cleaned_data是一个字典，包含了表单中每个字段的验证成功的值，比如{role：1, username:11, passwrod:123}
    # 在Django中，当你调用 form.is_valid() 进行表单验证成功后，可以通过 form.cleaned_data 来获取验证成功的数据。

    role = data_dict.pop("role") # 从字典里弹出"role"对应的值，pop的目的是为了在下面验证的时候能使用**data_dict，只验证用户名和密码
    if role == "1":
        user_object = models.Administrator.objects.filter(**data_dict).filter(active=1).first()
    #     在 Administrator 表中查询一个符合特定条件的用户对象，并将结果存储在 user_object 变量中
    else:
        user_object = models.Customer.objects.filter(**data_dict).filter(active=1).first()


    # 2.3 数据不存在
    if not user_object:
        form.add_error("password", "Incorrect username or password")
        # 将自定义的错误消息 "用户名或密码错误" 与 "password" 字段关联
        # 自定义的错误信息会被添加到 Django 表单对象的 errors 字典中，key是表单中的字段名称，value是与该字段相关的错误信息列表，{"password": ["用户名或密码错误"]}
        # 在模板中，你可以通过 {{ form.errors.password }} 来访问这个字段的错误信息。

        return render(request, "login.html", {"form": form})

    # 2.4 数据存在，将用户信息存储session
    mapping = {"1": "ADMIN", "2": "CUSTOMER"}
    request.session[settings.NB_SESSION_KEY] = {
        "role": mapping[role],  # "ADMIN"  "CUSTOMER"
        "id": user_object.id,
        "name": user_object.username,
    }
    # request.session[settings.NB_SESSION_KEY] 是将用户信息存储到 Django 的 session 中的一种方式
    # settings.py里设置了NB_SESSION_KEY = "user_info"

    # 2.5 成功，跳转后台
    return redirect(settings.HOME_URL)


def logout(request):
    request.session.clear()
    return redirect("login")


def sms_login(request):
    # 1.GET请求看到登录页面
    if request.method == "GET":
        form = SmsLoginForm()
        return render(request, "sms_login.html", {"form": form})

    print(request.META)
    # 2.格式校验（手机号+验证码）
    # 3.验证码是否正确？手机号去redis中校验
    form = SmsLoginForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"status": False, "msg": form.errors})
    # is_valid()是 Django表单类提供的方法，用于检查表单字段的数据是否符合字段定义的验证规则，
    # 比如说SmsLoginForm里，code变量 validators=[RegexValidator(r'^[0-9]{4}$', 'Invalid verification code'), ]就是在定义验证规则

    # 4.去数据库中读取用户信息 + 保存Session
    role = form.cleaned_data['role']
    mobile = form.cleaned_data['mobile']
    if role == "1":
        user_object = models.Administrator.objects.filter(mobile=mobile).filter(active=1).first()
    else:
        user_object = models.Customer.objects.filter(mobile=mobile).filter(active=1).first()

    # 5.数据不存在
    if not user_object:
        return JsonResponse({"status": False, "msg": {"mobile": ["手机号不存在"]}})

    # 2.4 数据存在，将用户信息存储session
    mapping = {"1": "ADMIN", "2": "CUSTOMER"}
    request.session[settings.NB_SESSION_KEY] = {
        "role": mapping[role],  # "ADMIN"  "CUSTOMER"
        "id": user_object.id,
        "name": user_object.username,
    }
    return JsonResponse({"status": True, "msg": "OK", "data": settings.HOME_URL})


@csrf_exempt
# 允许发送短信的请求不受 CSRF 保护的限制
def send_sms(request):
    """ 发送短信"""
    # 1.校验手机格式是否正确（是否已经注册？）
    # 2.校验手机号发送频率（第三方短信平台）
    # 3.生成短信验证码 + 发送
    form = SendSmsForm(data=request.POST)
    if not form.is_valid():
        return JsonResponse({"status": False, "msg": form.errors})

    return JsonResponse({"status": True, "msg": "OK"})


def home(request):
    return render(request, "home.html")


def user(request):
    # return HttpResponse("USER")
    return render(request, "user.html")


def add_user(request):
    # return HttpResponse("USER")
    return render(request, "add_user.html")


def multi_import(request):
    # return HttpResponse("multi_import")
    return render(request, "multi_import.html")


def edit_user(request, uid):
    return HttpResponse("edit_user")
