from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(email,seconds):
    s=Serializer('234567uihgdx',seconds)
    return s.dumps({'user':email}).decode('utf-8')
