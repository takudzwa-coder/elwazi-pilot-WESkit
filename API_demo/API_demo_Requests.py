import requests
import os

s = requests.session()

Credentials = {"username":"test","password":"test"}
WrongCredentials = {"username":"stranger","password":"awierdPassword"}

# Test with HTTPS
baseURL="https://localhost:5000"

current_file=os.path.dirname(os.path.abspath(__file__))
# Set path for self signed certificate
s.verify= os.path.normpath(os.path.join(current_file,'../uWSGI_Server/certs/weskit.pem'))
a=os.path.normpath(os.path.join(current_file,'../uWSGI_Server/certs/weskit.pem'))


# without HTTPS
#baseURL="http://localhost:5000"

def tryApiEndpoints(loginType,session):

    print("****************************************")
    # Try logging in with wrong credentials
    print( "%s - GET Requst to '/ga4gh/wes/user_status'"%(loginType) )
    response1= session.get("%s/ga4gh/wes/user_status"%(baseURL),verify=a)
    
    print("Status Code:",response1.status_code)
    print("Response:",response1.json())
    print("****************************************\n\n")
    
    print("****************************************")
    # Try logging in with wrong credentials
    print( "%s - GET-Requst to '/ga4gh/wes/v1/service-info'"%(loginType) )
    response2 = s.get("%s/ga4gh/wes/v1/service-info"%(baseURL))
    
    print("Status Code:",response2.status_code)
    print("Response:",response2.json())
    print("****************************************\n\n")
    print("****************************************")
    print("%s - GET-Requst to '/ga4gh/wes/v1/runs/'"%( loginType))
    response3 = session.get("%s/ga4gh/wes/v1/runs"%(baseURL))
    print("Status Code:",response3.status_code)
    print("Response:",response3.json())
    print("****************************************\n\n")
    
    print("****************************************")
    print("%s - GET-Requst to '/refresh'"%( loginType))
    response4 = session.post("%s/refresh"%(baseURL))
    print("Status Code:",response4.status_code)
    print("Response:",response4.json())
    print("****************************************\n\n")
    
    print("****************************************")
    print("%s - GET-Requst to '/logout'"%( loginType))
    response5 = session.get("%s/logout"%(baseURL))
    print("Status Code:",response5.status_code)
    print("Response:",response5.json())
    print("****************************************\n")
    

print("****************************************")
print("*        Test API without login        *")

tryApiEndpoints('without login ',s)
print("________________________________________________________________________________")




print("****************************************")
print("*        Test API with wrong login     *")
loginresponse = s.post("%s/login"%(baseURL),json=WrongCredentials)
print("Status Code:",loginresponse.status_code)
print("Response:",loginresponse.json())
tryApiEndpoints('with wrong login ',s)
print("________________________________________________________________________________")

print("****************************************")
print("*        Test API with with correct login     *")
loginresponse = s.post("%s/login"%(baseURL),json=Credentials)
print("Status Code:",loginresponse.status_code)
print("Response:",loginresponse.json())
tryApiEndpoints('with correct login ',s)
print("________________________________________________________________________________")

print("****************************************")
print("*      Try after Successful logout     *")
tryApiEndpoints('after logout ',s)
print("________________________________________________________________________________")

