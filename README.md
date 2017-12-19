# YummyRecipes-flaskAPI
[![Build Status](https://travis-ci.org/JoyyToo/YummyRecipes-flaskAPI.svg?branch=master)](https://travis-ci.org/JoyyToo/YummyRecipes-flaskAPI) [![Coverage Status](https://coveralls.io/repos/github/JoyyToo/YummyRecipes-flaskAPI/badge.svg)](https://coveralls.io/github/JoyyToo/YummyRecipes-flaskAPI) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/0d508bcb432b4ca983a56ee409e42549)](https://www.codacy.com/app/JoyyToo/YummyRecipes-flaskAPI?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=JoyyToo/YummyRecipes-flaskAPI&amp;utm_campaign=Badge_Grade)

A Flask RESTful API with Endpoints that enable users to:

- Register, login and manage their account.
- Create, update, view and delete a category.
- Add, update, view or delete recipes.
- Enable logging of data manipulation timestamps.

## Example request with response
```
Curl
curl -X POST --header 'Content-Type: multipart/form-data' --header 'Accept: application/json' -F username=user1 -F password=useruser -F email=user%40mail.com  'http://127.0.0.1:5000/api/v1/auth/auth/register'
Request URL
http://127.0.0.1:5000/api/v1/auth/auth/register
Response Body
{
  "message": "You registered successfully. Please log in.",
  "status": "success"
}
Response Code
201
Response Headers
{
  "date": "Thu, 07 Dec 2017 12:53:49 GMT",
  "server": "Werkzeug/0.12.2 Python/2.7.12",
  "content-length": "87",
  "content-type": "application/json"
}
```

## Prerequisites

Python 2.6 or a later version

## Dependencies
Install all package requirements in your python virtual environment.
```
pip install -r requirements.txt
```
## Env
Rename .env.sample into .env

## Virtual environment
Activate virtual environment:

```
$ source .venv/bin/activate
```

## Testing
To set up unit testing environment:

```
$ pip install nose
```

To execute a test file:

```
$ source .env
$ nosetests
```

## Testing API

*Note* After user login, ensure you  specify the generated token in the header:

- In postman header **key** : `token` **value** : <token>
- While testing on the browser, key in the `<token>` in Authorize header.

## Initialize the database
You need to initialize database and tables by running migrations.

```
python manager.py db init

python manager.py db migrate

python manager.py db upgrade

```

## Start The Server
Start the server which listens at port 5000 by running the following command:
```
source .env
python run.py
```

## Pagination

The API enables pagination by passing in *page* and *limit* as arguments in the request url as shown in the following example:

```
http://127.0.0.1:5000/category?page=1&limit=10

```

## Searching

The API implements searching based on the name using a GET parameter *q* as shown below:

```
http://127.0.0.1:5000/category?q=example
```


### Api endpoints

| url | Method|  Description| Authentication |
| --- | --- | --- | --- |
| /register | POST | Registers new user | FALSE
| /login | POST | Handles POST request for /auth/login | FALSE
| /logout | GET | Logs out a user | TRUE
| /reset-password | POST | Reset user password | TRUE
| /category | GET | Get every category of logged in user|TRUE
| /category/{category_id} | GET | Get a single category|TRUE
| /category | POST | Create a new category|TRUE
| /category/{category_id}  | PUT | Update a single category|TRUE
| /category/{category_id} | DELETE | Delete a single category|TRUE
| /category/{category_id}/recipes | POST | Creates a recipe|TRUE
| /category/{category_id}/recipes/{_id} | GET | Gets a single recipe|TRUE
| /category/{category_id}/recipes/{_id} | PUT | Updates a single recipe|TRUE
| /category/{category_id}/recipes/{_id} | DELETE | Deletes a single recipe|TRUE


### Testing and API documentation

[https://yummy-recipe-flaskapi.herokuapp.com/](https://yummy-recipe-flaskapi.herokuapp.com/)
