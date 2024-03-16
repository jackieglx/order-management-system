import hashlib


def md5_string(data_string):
    obj = hashlib.md5("asdfadfou2k30a980dfjadf".encode('utf-8'))
    obj.update(data_string.encode('utf-8'))
    return obj.hexdigest()


if __name__ == '__main__':
    res = md5_string("qwe123")
    print(res)