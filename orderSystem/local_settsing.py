from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.mysql',
        'NAME': 'orders_management',  #让ORM去连接的你创建的数据库的名字
        'USER':'root', # mysql的账户名
        'PASSWORD': '', # mysql的密码
        'HOST': '127.0.0.1', # 数据库安装在哪台服务器上，如果是自己的本机服务器就写127.0.0.1
        'PORT': 3306,
        'POOL_OPTIONS':{
            'POOL_SIZE': 10, # 最小连接次数
            'MAX_OVERFLOW': 10, # 在最小的基础上，还可以增加10个，即：最大20个
            'RECYCLE': 24 * 60 * 60, # 连接可以被重复用多久，超过时间会重新创建，-1表示永久
            'TIMEOUT': 30, # 连接在空闲30秒后可能会被回收
        }
    }
}

#########
# CACHE #
#########
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": 'redis://192.168.176.131:6379/1',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            "PASSWORD": "",
        }
    }
}