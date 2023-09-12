# SPDX-FileCopyrightText: 2023 The WESkit Team
#
# SPDX-License-Identifier: MIT

##########################################
#                                        #
#   This script helps to modify the      #
#   users.yaml savely                    #
#                                        #
##########################################


import sys
import argparse
import yaml
import hashlib
import uuid

################################################
# Load only valid entrys from disk             #
################################################


def loadValidated(yamlDict):
    filtered = {
        key: value for key, value in yamlDict.items() if
        type(value) is dict and
        len({
            'roles',
            'password',
            'salt'}.intersection(value)) == 3
    }

    # Verify that File on disc has no corruped entries
    if (len(filtered)) != len(yamlDict):
        print(
                ("Skiped %d Entrys from DBfile: "
                    "Invalid Format!") % (
                    len(yamlDict) - len(filtered))
        )
    return filtered


################################################
# Load the users.yaml database file from disk  #
################################################


def dbfile2dict(file):
    try:
        with open(file, 'r') as stream:
            return loadValidated(yaml.safe_load(stream))
    except FileNotFoundError:
        print(
            "File %s does not exists, trying to create one" %
            file
        )
        dict2dbfile(file, dict())
        return {}


################################################
# Write the users.yaml database file to disk   #
################################################

def dict2dbfile(file, users):
    try:
        with open(file, 'w') as stream:
            return yaml.dump(users, stream)
    except Exception as e:
        print(e)
        print("unable to write %s" % file)
        exit(0)


################################################
# Print User in pretty format                  #
################################################

def printUser(username, value):
    print("__________________")
    print(username)
    print("Roles: %s" % (','.join(value.get('roles', []))))


################################################
#  Setup argparse                              #
################################################

parser = argparse.ArgumentParser(
    usage="""python LocalUserManagement.py {function} Databasefile""",
    description='''
This tool is part of WESkit. In allows valid modifications of the users.yaml as
* list all users
* add users
* remove users
* change the roles of a user
''',
    epilog="""Thanks for using WESkit""")

parser.add_argument(
    'function',
    choices=[
        'list',
        'add',
        'remove',
        'changeRoles'
    ],
    help='the name of function to be used'
)

parser.add_argument('Databasefile', help='path to the users.yaml file')

args = parser.parse_args()


##########################################
#                                         #
#   Function Switch:   list               #
#       Show all users from Databasefile  #
##########################################

if (args.function == 'list'):
    # Load Database-File
    users = dbfile2dict(args.Databasefile)

    # How many Users are in the Database
    print("%d Users found in %s:" % (len(users), args.Databasefile))

    # Print all Usernames and their roles
    for username, value in users.items():
        printUser(username, value)

##########################################
#                                         #
#   Function Switch:   add                #
#       add user to DB                    #
##########################################

elif (args.function == 'add'):
    # Load Database-File
    users = dbfile2dict(args.Databasefile)

    # Ask for new Username
    newUser = input("New Username:")

    # Print a message if username is already in the DB
    if newUser in users:
        print(
            "User allready in DB. Use %s list to show all available users" %
            (sys.argv[0])
        )

        printUser(newUser, users[newUser])

    # If user is really new:
    else:
        # Define options to make user an Admin
        admin = ['Admin', 'default']
        userIsAdmin = {'y': admin, 'yes': admin, 'Y': admin, 'Yes': admin}

        # Check if Admin question is answered positive, else switch to default
        roles = userIsAdmin.get(
            input("Is new User Admin? (NO/yes) default no:"),
            ['default']
        )

        # Ask for new password
        password = input('Enter the new Password for the User:\n')

        # Generate new salt based on random uuid
        salt = str(uuid.uuid4())

        # hash the (password + salt)
        passwordhash = hashlib.sha256(
            (password+salt).encode("UTF-8")
        ).hexdigest()

        # Store password hash, salt and roles to dict
        users[newUser] = {
            'password': passwordhash,
            'salt': salt,
            'roles': roles
        }

        # Write changes to disk
        dict2dbfile(args.Databasefile, users)

        # Print Success Status
        print("New user added to the Database %s!" % (args.Databasefile))
        printUser(newUser, users[newUser])


##########################################
#                                         #
#   Function Switch:   remove             #
#       removes user from DB              #
###########################################

elif (args.function == 'remove'):
    # Load Database-File
    users = dbfile2dict(args.Databasefile)

    # Ask for Username that should be removed
    newUser = input("Username to remove:")

    # Print a message if username is not in DB
    if newUser not in users:
        print(
            ("%s is missing in DB %s. "
             "Use '%s list %s' to show all available users") %
            (newUser, args.Databasefile, sys.argv[0], args.Databasefile)
        )

    # Remove User from dict and write it to file
    else:
        users.pop(newUser)

        # Write changes to disk
        dict2dbfile(args.Databasefile, users)
        print(
            "User %s is removed from Database %s!" %
            (newUser, args.Databasefile)
        )

##########################################
#                                         #
#   Function Switch:   changeRoles        #
#      asks again if user should be admin #
###########################################
elif args.function == 'changeRoles':
    # Load Database-File
    users = dbfile2dict(args.Databasefile)

    # Ask for Username that should be changed
    newUser = input("Username to change:")

    # Print a message if username is not in DB
    if newUser not in users:
        print(
            ("%s is missing in DB %s. Use '%s list %s' "
             "to show all available users") %
            (newUser, args.Databasefile, sys.argv[0], args.Databasefile)
        )

    else:
        # Define options to make user an Admin
        admin = ['Admin', 'default']
        userIsAdmin = {'y': admin, 'yes': admin, 'Y': admin, 'Yes': admin}

        # Check if Admin question is answered positive, else switch to default
        roles = userIsAdmin.get(
            input("Is new User Admin? (NO/yes) default no:"), ['default'])

        users[newUser]['roles'] = roles

        # Write changes to disk
        dict2dbfile(args.Databasefile, users)
        printUser(newUser, users[newUser])
else:
    print('notfound')
