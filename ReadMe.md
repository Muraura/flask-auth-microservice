### PORT 9000
Version : v1

Append the Version Number to all the routes

###### USER SIGN UP
```python 
@app.route('/signup', methods=['POST'])
def userSignup():
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    phone_number = request.json['phone_number']
    user_type = request.json['user_type']
    password = request.json['password']
```

###### GET ALL USERS
```python
@app.route('/users')
auth_header = request.headers.get('Authorization')
```

###### LOGIN
```python
@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
```

### Get a user
```python
@app.route('/user/<public_id>')
```

####### USERTYPES
```python
@app.route('/usertypes')
```
####### SINGLE USERTYPE
```python
@app.route('/single/usertype/<public_id>')
```

### Make A Password request
```python
''' The Url you hit to make a password request, it will send you an email '''
@app.route('/password/reset', methods=['POST'])
def passwordReset():
    email_address = request.json['email']
```

### Password Change
```python
@app.route('/password/reset/<public_id>', methods=['POST'])
def resetPassword(public_id):
    reset_header = request.headers.get('Authorization')
    new_password = request.json['new_password']
```

### delete a usertype
```python
@app.route('/delete/usertype/<public_id>', methods=['DELETE'])
```
### update user type
```python
@app.route('/update/usertype/<public_id>', methods=['POST'])
    name = request.json['name']
    desc = request.json['description']
```

### add usertype
```python
@app.route('/add/usertype', methods=['POST'])
    name = request.json['name']
    desc = request.json['description']
```

### update a user
```python
@app.route('/user/update/<public_id>', methods=['POST'])
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        email = request.json['email']
        phone_number = request.json['phone_number']
        user_type = request.json['user_type']
```

### delete a user
```python
@app.route('/user/delete/<public_id>', methods=['DELETE'])
```

### Get users from a user_id array
```python
    @app.route('/users/array', methods=['POST'])
    user_id = request.json['users_ids']
```

### Retrieve All Menus
```python
    @app.route('/menus')
```

### Add a new menu
```python
    @app.route('/menu/add', methods=['POST'])
    name = request.json['name']
    description = request.json['description']
```

### Update a new menu
```python
    @app.route('/menu/update/<public_id>', methods=['POST'])
    name = request.json['name']
    descsription = request.json['description']
```

### Retrieve single menu
```python
@app.route('/menu/<public_id>')
```

### Retrieve all roles
```python 
    @app.route('/roles')
```

### Add Roles
```python 
    @app.route('/role/add', methods=['POST'])
        name = request.json['name']
        description = request.json['description']
```

### Update Role
```python 
    @app.route('/role/update/<public_id>', methods=['POST'])
        name = request.json['name']
        description = request.json['description']
```

### Add a feature
```python
@app.route('/feature/add', methods=['POST'])
    name = request.json['name']
    url = request.json['url']
    description = request.json['description']
    menu_public_id = request.json['menu_public_id']
```

### Get features associated with a role
```python
    @app.route('/features/role/<public_id>')
```

### Get all features associated with a role
```python
    @app.route('/role/feature/<public_id>')
```

### Get feature that the role isn't selected in
```python
# Get feature that the role isn't selected in
# params public_id (role_id)
@app.route('/feature/notassigned/<public_id>')
```

### Associate a feature with a role
```python
    @app.route('/role/feature/add', methods=['POST'])
    def addRelationshipRoleToFeature():
        role_public_id = request.json['role_public_id']
        feature_public_id = request.json['feature_public_id']
```

### Detach a feature with a role
```python
@app.route('/role/feature/detach', methods=['POST'])
def detachAttachement():
    role_public_id = request.json['role_public_id']
    feature_public_id = request.json['feature_public_id']
```

### register a partner user
```python
@app.route('/partner/user', methods=['POST'])
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    phone_number = request.json['phone_number']
    user_type = request.json['user_type']
    partner_public_id = request.json['partner_public_id']
```


### get users belonging to a particular partner
```python
@app.route('/users/institution/<public_id>')
```
### Countries
```python
    /v1/countries

    # Single
    /v1/country/<public_id>
```

### Gender
```python
    /v1/genders

    # Single
    /v1/gender/<public_id>
```