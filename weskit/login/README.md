# **WESkit Login System**

# WESkit Login Endpoints

The WESkit Login System provides 4 endpoints. Login Examples via script can be found here: [WESkit/API_demo/API_demo_Requests.py](../../API_demo/API_demo_Requests.py)

## /login for Machienes
Send a post request to `/login` with a json dict containing:
```json
{"username":"test",
"password": "test"}
```
Ensure that the request header contains `application/json`!

If the login was successfull status `200` is returned and the json string `{"login":true}`
Furthermore, a JWT access cookie and a JWT refresh cookie where transfered to the client.

If the login was unsuccessfull status `403` is returned and the json string `{"login":false}`

If you get `302` you using a form instead of json for submitting the credentials!

## /login for Humans
Visit / or / login with your browser and provide there your credentials.

If the login is correct the JWT cookies will be set and you will be redirected to `/ga4gh/wes/user_status`.
Otherwise the the page reloads.

## /logout
Throw a GET or POST request to this endpoint and your cookies will be deleted on the client and server.

## /refresh

Throw a POST request to this endpoint and your will recieve a new JWT access cookie. Be aware that this dependent on the `JWT_COOKIE_CSRF_PROTECT` defined in the WESkit config file!

## /ga4gh/wes/user_status
At GET request this endpoind shows the name of the user and its roles.

# Configuration
The WESkit Login System is configured by two files:
* WESkit `config.yaml` file
* `users.yaml`

## config.yaml
The WESkit login part of the WESkit config should look similar to:
```yaml
# If this block is missing WESkit will act without login

jwt:
    # Only allow JWT cookies to be sent over https. In production, this
    # should likely be True
    JWT_COOKIE_SECURE: true
    
    # Enable csrf double submit protection. See this for a thorough
    # explanation: http://www.redotheweb.com/2015/11/09/api-security.html
    # If true: getting a new access token while the old one is valid is blocked.
    JWT_COOKIE_CSRF_PROTECT: true
    
    # Set the secret key to sign the JWTs with
    # 'super-secret' musst be replaced by a long random string !!!!!!
    JWT_SECRET_KEY: 'super-secret'  # Change this!!!!!!
    
    
# This block is only used if the jwt is present! and enabled=True
# It allows the switch the auth backend in the future.
localAuth:
  enabled: true    # currently always true!
  yamlPath: 'users.yaml'  # Path to users.yaml should not be changed if `docker stack` is used!
```
### jwt Block
A missing jwt block will be interpreted as "open WESkit". No login is required. In the most cases you want to set this block!

***enabled **

required boolean will enable or disable jwt functions

**JWT_COOKIE_SECURE**

Session Cookies will be only distributed via SSL secured connections. If you do not use a reverse proxy this should be `true`!

**JWT_COOKIE_CSRF_PROTECT**

While this option is false it is possible to get a new access by calling `{host}/refresh` token while the old one is valid. In the most cases this is an unwanted behavior. Set it to `true`!

**JWT_SECRET_KEY**

**Important:** this option musst be replaced by a very long random string!!  If this string could be guessed or gets lost attackers can authenticate as arbitary user! 

**localAuth**
This block should be untouched. Its a feature for further login methods. If WESkit runs outside an container you can change the path of the user user.yaml

## users.yaml
The `users.yaml` file contains a dictionary of each username(key) and a mandatory list of user attributs:
* roles (list of one or more roles of currently `['Admin','default']`)
* salt (long random string)
* password (hashed string of `sha256(password+salt)`)

Invalid Entrys were skipted at while loading the users.yaml by WESkit.
Changes of the `users.yaml` were tracked by the WESkit login system. Therefore, changes are immediatly loaded into WESkit. This file is read-only mounted into the docker stack. Changes on the host takes immediatly effect on the container.

**Important:** Remove the test user in an productive environment!

 


# `LocalUserManagement.py`
There is a comfort tool `LocalUserManagement.py` to edit the users.yaml file. It is able to:
* add users
* remove users
* list all users
* changeRoles of a user

## Example:

```bash
python LocalUserManagement.py add users.yaml
    New Username:OTP
    Is new User Admin? (NO/yes) default no:yes
    Enter the new Password for the User:
    realyB4dP455w0Rd
    New user added to the Database users.yaml!
    __________________
    OTP
    Roles: Admin,default
```

