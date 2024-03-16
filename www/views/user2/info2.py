from django import forms
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError

from utils.v3 import BaseCurd
from www import models
from utils.encrypt import md5_string
from utils.bootstrap import BootStrapForm


class ResetPasswordModelForm(BootStrapForm, forms.ModelForm):
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


class Info2(BaseCurd):

    def list(self, request):
        # 获取当前用户信息
        instance = models.Customer.objects.filter(id=request.nb_user.id, active=1).first()
        if request.method == "GET":
            # 生成Form表单
            form = ResetPasswordModelForm()
            context = {"instance": instance, 'form': form}
            return render(request, 'user2/info_list.html', context)

        form = ResetPasswordModelForm(instance=instance, data=request.POST)
        if not form.is_valid():
            context = {"instance": instance, 'form': form}
            return render(request, 'user2/info_list.html', context)

        form.save()
        messages.add_message(request, messages.SUCCESS, "更新成功")
        return redirect("info2_list")
