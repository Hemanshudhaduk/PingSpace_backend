from jose import JWTError ,jwt
from datetime import datetime , timedelta
SECRET_KEY = 'secret123'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTE = 60

def create_access_token(data):
        
        to_encode = data.copy()
        to_encode.update({'exp' : datetime.utcnow() + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTE)})
        # to_encode['exp']  = datetime.utcnow() + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTE)
        print(to_encode)
        
        return jwt.encode(to_encode , SECRET_KEY , algorithm=ALGORITHM)



def verify_access_token(token) :
        try :
                
            return jwt.decode(token , SECRET_KEY , algorithms=[ALGORITHM])
        except JWTError as e :
               return f'token is invalid or expired {e}'



# main = create_access_token({
#         'username' : 'harshit' , 
#         'pass' :'123'
# })
# verify = verify_access_token(main)
# print('verify : ' ,verify)