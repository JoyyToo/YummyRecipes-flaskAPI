# YummyRecipes-flaskAPI
[![Build Status](https://travis-ci.org/JoyyToo/YummyRecipes-flaskAPI.svg?branch=master)](https://travis-ci.org/JoyyToo/YummyRecipes-flaskAPI) [![Coverage Status](https://coveralls.io/repos/github/JoyyToo/YummyRecipes-flaskAPI/badge.svg?branch=master)](https://coveralls.io/github/JoyyToo/YummyRecipes-flaskAPI?branch=master)

A Flask RESTful API with Endpoints that enable users to:

- Register, login and manage their account.
- Create, update, view and delete a category.
- Add, update, view or delete recipes.
- Enable logging of data manipulation timestamps.

## Prerequisites

Python 2.6 or a later version

## Dependencies
Install all package requirements in your python virtual environment.
```
pip install -r requirements.txt
```

Activate virtual environment:

```
$ source .venv/bin/activate
```

To set up unit testing environment:

```
$ pip install nose
```

To execute a test file:

```
$ source .env
$ nosetests
```

## Start The Server
Start the server which listens at port 5000 by running the following command:
```
$ source .env
$ python run.py
```
