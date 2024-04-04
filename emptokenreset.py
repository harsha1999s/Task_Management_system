from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
def token(empemail,seconds):
    s=Serializer('234567uihgdx',seconds)
    return s.dumps({'user':empemail}).decode('utf-8')