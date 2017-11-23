# YummyRecipes-flaskAPI
[![Build Status](https://travis-ci.org/JoyyToo/YummyRecipes-flaskAPI.svg?branch=master)](https://travis-ci.org/JoyyToo/YummyRecipes-flaskAPI) [![Coverage Status](https://coveralls.io/repos/github/JoyyToo/YummyRecipes-flaskAPI/badge.svg)](https://coveralls.io/github/JoyyToo/YummyRecipes-flaskAPI) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/0d508bcb432b4ca983a56ee409e42549)](https://www.codacy.com/app/JoyyToo/YummyRecipes-flaskAPI?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=JoyyToo/YummyRecipes-flaskAPI&amp;utm_campaign=Badge_Grade)

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
