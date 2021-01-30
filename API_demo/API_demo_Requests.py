import requests

s = requests.Session()

Credentials = {"username":"test","password":"test"}
WrongCredentials = {"username":"stranger","password":"awierdPassword"}




def tryApiEndpoints(loginType,session):

    print("****************************************")
    # Try logging in with wrong credentials
    print( "%s - GET Requst to '/ga4gh/wes/user_status'"%(loginType) )
    response1= session.get("http://localhost:5000/ga4gh/wes/user_status")
    
    print("Status Code:",response1.status_code)
    print("Response:",response1.json())
    print("****************************************\n\n")
    
    print("****************************************")
    # Try logging in with wrong credentials
    print( "%s - GET-Requst to '/ga4gh/wes/v1/service-info'"%(loginType) )
    response2 = s.get("http://localhost:5000/ga4gh/wes/v1/service-info")
    
    print("Status Code:",response2.status_code)
    print("Response:",response2.json())
    print("****************************************\n\n")
    print("****************************************")
    print("%s - GET-Requst to '/ga4gh/wes/v1/runs/'"%( loginType))
    response3 = session.get("http://localhost:5000/ga4gh/wes/v1/runs")
    print("Status Code:",response3.status_code)
    print("Response:",response3.json())
    print("****************************************\n\n")
    
    print("****************************************")
    print("%s - GET-Requst to '/refresh'"%( loginType))
    response4 = session.post("http://localhost:5000/refresh")
    print("Status Code:",response4.status_code)
    print("Response:",response4.json())
    print("****************************************\n\n")
    
    print("****************************************")
    print("%s - GET-Requst to '/logout'"%( loginType))
    response5 = session.get("http://localhost:5000/logout")
    print("Status Code:",response5.status_code)
    print("Response:",response5.json())
    print("****************************************\n")
    

print("****************************************")
print("*        Test API without login        *")

tryApiEndpoints('without login ',s)
print("________________________________________________________________________________")




print("****************************************")
print("*        Test API with wrong login     *")
loginresponse = s.post("http://localhost:5000/login",json=WrongCredentials)
print("Status Code:",loginresponse.status_code)
print("Response:",loginresponse.json())
tryApiEndpoints('with wrong login ',s)
print("________________________________________________________________________________")

print("****************************************")
print("*        Test API with with correct login     *")
loginresponse = s.post("http://localhost:5000/login",json=Credentials)
print("Status Code:",loginresponse.status_code)
print("Response:",loginresponse.json())
tryApiEndpoints('with correct login ',s)
print("________________________________________________________________________________")

print("****************************************")
print("*      Try after Successful logout     *")
tryApiEndpoints('after logout ',s)
print("________________________________________________________________________________")

