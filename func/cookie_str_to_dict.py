# 将 cookie 字符串转换为结构化列表
def cookie_str_to_dict(cookie):
    result = {}
    for item in cookie.split("; "):
        if "=" in item:
            k, v = item.split("=", 1)
            result[k] = v
    return result