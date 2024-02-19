# 启动django
import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'day01_31.settings')
django.setup()  # 伪造让django启动

from app01 import models
from utils.encrypt import md5

models.Administrator.objects.create(username='root', password=md5("root"), mobile="1888888889")
