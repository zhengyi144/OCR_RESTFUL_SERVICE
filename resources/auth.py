import hashlib
from flask import request,jsonify
from datetime import datetime

def createSignature(userId,timeStamp):
    """
    根据参数进行签名:userId&timeStamp{userId}{timeStamp}
    """
    msg="userId&timeStamp"
    rule=f'{msg}{userId}{timeStamp}'
    md5=hashlib.md5()
    md5.update(rule.encode('utf-8'))
    return md5.hexdigest()

def validsign(requireSign=True):
    """
    校验签名
    """
    def decorator(func):
        def wrapper():
            try:
                if requireSign:
                    userId=request.form.get("userId")
                    timeStamp=request.form.get("timeStamp")
                    sign=request.form.get("sign")
                    csign=createSignature(userId,timeStamp)
                    #print(csign)
                    if csign!=sign:
                        return jsonify({"code":504,"msg":"signature error"})
            except Exception as e:
                return jsonify({"code":500,"msg":"signature error"})
            return func()
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

if __name__=="__main__":
    timeStamp=int(datetime.now().timestamp())
    print(timeStamp)
    userId=1123356641100
    sign=createSignature(userId,timeStamp)
    print(sign)
    