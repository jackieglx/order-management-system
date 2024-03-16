"""
URL configuration for orderSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from www.views import account
from www.views import level
from www.views import price
from www.views import nb
from www.views import customer
from www.views import db
from www.views import wb
from www.views import v1
from www.views import v2
from www.views import v3

from www.views.user import info
from www.views.user import yang
from www.views.user import mine

from www.views.user2 import info2
from www.views.user2 import yang2
from www.views.user2 import tran2
from www.views.backend import level
from www.views.backend import price
from www.views.backend import customer
from www.views.backend import record

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('login/', account.login, name='login'),
    path('logout/', account.logout, name='logout'),
    path('sms/login/', account.sms_login, name='sms_login'),
    path('send/sms/', account.send_sms, name='send_sms'),
    path('home/', account.home, name='home'),

    # 传统：客户相关(user)
    path('info/list/', info.info_list, name='info_list'),
    path('yang/list/', yang.yang_list, name='yang_list'),
    path('yang/add/', yang.yang_add, name='yang_add'),
    path('yang/cancel/<int:pk>/', yang.yang_cancel, name='yang_cancel'),
    path('mine/tran/', mine.mine_tran, name='mine_tran'),

    # 组件：客户相关(user2)
    path('info2/', info2.Info2.urls(view_list=["list"], prefix="info2")),
    path('yang2/', yang2.Yang2.urls(view_list=["list", 'add'], prefix="yang2")),
    path('tran2/', tran2.Tran2.urls(view_list=["list"], prefix="tran2")),

    # 管理员相关 backend
    path('level/', level.Level.urls()),
    path('price/', price.Price.urls()),
    path('customer/', customer.Customer.urls()),
    path('record/', record.Record.urls(view_list=["list", 'add'])),


    # path('user/', account.user, name='user'),
    # path('add/user/', account.add_user, name='add_user'),
    # path('multi/import/', account.multi_import, name='multi_import'),
    # path('edit/user/<int:uid>', account.edit_user, name='edit_user'),
    #
    # path('level/list/', level.level_list, name='level_list'),
    # path('level/add/', level.level_add, name='level_add'),
    # path('level/edit/<int:nid>/', level.level_edit, name='level_edit'),
    # path('level/delete/<int:nid>/', level.level_delete, name='level_delete'),
    #
    # path('price/list/', price.price_list, name='price_list'),
    # path('price/add/', price.price_add, name='price_add'),
    # path('price/edit/<int:nid>/', price.price_edit, name='price_edit'),
    # path('price/delete/<int:nid>/', price.price_delete, name='price_delete'),
    #
    # path('level2/list/', nb.LevelCurd.list, name='level2_list'),
    # path('level2/add/', nb.LevelCurd.add, name='level2_add'),
    # path('level2/edit/<int:nid>/', nb.LevelCurd.edit, name='level2_edit'),
    # path('level2/delete/<int:nid>/', nb.LevelCurd.delete, name='level2_delete'),
    #
    # path('price2/list/', nb.PriceCurd.list, name='price2_list'),
    # path('price2/add/', nb.PriceCurd.add, name='price2_add'),
    # path('price2/edit/<int:nid>/', nb.PriceCurd.edit, name='price2_edit'),
    # path('price2/delete/<int:nid>/', nb.PriceCurd.delete, name='price2_delete'),
    #
    # path('price3/', db.Price3.urls()),
    # path('level3/', db.Level3.urls()),
    #
    # path('customer/list/', customer.customer_list, name='customer_list'),
    # path('customer/add/', customer.customer_add, name='customer_add'),
    #
    # path('customer/edit/<int:pk>/', customer.customer_edit, name='customer_edit'),
    # path('customer/delete/<int:pk>/', customer.customer_delete, name='customer_delete'),
    # path('customer/reset/<int:pk>/', customer.customer_reset, name='customer_reset'),
    #
    # path('price4/', wb.Price4.urls()),
    # path('level4/', wb.Level4.urls()),
    #
    # path('customer4/', wb.Customer4.urls()),
    #
    # path('v1/demo/', v1.demo, name="v1_demo"),
    # path('v2/demo/', v2.demo, name="v2_demo"),
    #
    # path('v3/', v3.V3.urls()),
    #
    # path('depart/', v3.Depart.urls()),
    # path('info/', v3.Info.urls()),
]
