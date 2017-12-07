from functools import wraps

from flask import request, jsonify
import re
from flask_bcrypt import Bcrypt
from app import api, Resource, reqparse
from app.models import Users, Categories, Recipes, Sessions

# namespaces
auth_namespace = api.namespace('auth', description="Authentication/Authorization operations.")
category_namespace = api.namespace('category', description="Category operations.")


def token_required(f):
    @wraps(f)
    def validate_user(*args, **kwargs):
        user_id = None
        auth_header = request.headers.get('Authorization')
        access_token = auth_header.split(" ")[1] if auth_header else None
        if access_token:
            user_id = Users.decode_token(access_token)
            if user_id:
                if isinstance(user_id, int):
                    if not Sessions.login_status(user_id):
                        return {
                                   "message": "Session not available, Please login",
                                   "status": "error"
                               }, 403
                if isinstance(user_id, str):
                    return user_id
        else:
            return {
                "message": "Unauthorized, Please login or register",
                "status": "error"
            }, 403

        return f(user_id, *args, **kwargs)

    return validate_user


# Enables adding and parsing of multiple arguments in the context of a single request
registration_parser = api.parser()
registration_parser.add_argument('email', type=str, help='Email', location='form', required=True)
registration_parser.add_argument('username', type=str, help='username', location='form', required=True)
registration_parser.add_argument('password', type=str, help='Password', location='form', required=True)


@auth_namespace.route('/register')
class UserRegistration(Resource):
    @api.expect(registration_parser)
    def post(self):
        """Handles POST request for auth/register"""
        args = registration_parser.parse_args()
        # check if user already exists
        user = Users.query.filter_by(email=args['email']).first()

        if not user:
            # There is no user, try to register them
            try:

                email = args['email']
                username = args['username']
                password = args['password']
                regex = r"(^[a-zA-Z0-9_.]+@[a-zA-Z0-9-]+\.[a-z]+$)"
                if re.match(regex, email):
                    if username and password:

                        if len(password) < 6:
                            response = jsonify({
                                "message": "Password must be more than 6 characters.",
                                "status": "error"})
                            response.status_code = 400
                            return response

                        user = Users(email=email, username=username, password=password)
                        user.save()
                        session = Sessions(user.id)
                        session.save()

                        response = jsonify({
                            "message": "You registered successfully. Please log in.",
                            "status": "success"
                        })
                        response.status_code = 201
                        return response
                    else:
                        response = jsonify({
                            "message": "Please fill all fields",
                            "status": "error"
                        })
                        response.status_code = 400
                        return response
                response = jsonify({
                    "message": "Please enter a valid email address",
                    "status": "error"
                })
                response.status_code = 400
                return response

            except Exception as e:
                # Error occured during registration, return error
                response = jsonify({
                    "message": str(e),
                    "status": "error"
                })
                response.status_code = 401
                return response
        else:
            # User already exists
            response = jsonify({
                "message": "User already exists. Please login",
                "status": "error"
            })
            response.status_code = 409

            return response


login_parser = api.parser()
login_parser.add_argument('email', type=str, help='Email', location='form', required=True)
login_parser.add_argument('password', type=str, help='Password', location='form', required=True)


@auth_namespace.route('/login')
class UserLogin(Resource):
    @api.expect(login_parser)
    def post(self):
        """Handles POST request for /auth/login"""
        data = login_parser.parse_args()

        try:
            # check if user exists, email is unique to each user
            user = Users.query.filter_by(email=data['email']).first()

            if user and user.password_is_valid(data['password']):
                # generate access token
                access_token = user.generate_token(user.id)
                session = Sessions.login(user.id)
                if access_token and session:
                    response = jsonify({
                        "message": "You logged in successfully.",
                        "jwt_token": access_token.decode(),
                        "status": "success"
                    })
                    response.status_code = 200
                    return response
            else:
                # User does not exist or invalid password
                response = jsonify({
                    "message": "Invalid email or password, Please try again",
                    "status": "error"
                })
                response.status_code = 401
                return response
        except Exception as e:
            response = jsonify({
                "message": str(e),
                "status": "error"
            })
            response.status_code = 500
            return response


@auth_namespace.route('/logout')
class UserLogout(Resource):
    method_decorators = [token_required]

    def get(self, user_id):
        """Handles GET request for /auth/logout"""
        session = Sessions.logout(user_id)

        response = jsonify({
            "message": "You logged out successfully.",
            "status": "success"
        })
        response.status_code = 200
        return response


reset_parser = api.parser()
reset_parser.add_argument('email', type=str, help='Email', location='form', required=True)
reset_parser.add_argument('new password', type=str, help='Password', location='form', required=True)


@auth_namespace.route('/reset-password')
class ResetPasswordView(Resource):
    method_decorators = [token_required]

    @api.expect(reset_parser)
    def post(self, user_id):
        """Handles POST request for /auth/reset-password"""
        data = reset_parser.parse_args()
        email = data['email']
        password = data['new password']
        regex = r"(^[a-zA-Z0-9_.]+@[a-zA-Z0-9-]+\.[a-z]+$)"
        if re.match(regex, email) and email.strip():
            if len(password.strip()) >= 6:
                user = Users.query.filter_by(email=email).first()
                if user:
                    user.password = Bcrypt().generate_password_hash(password).decode()
                    user.save()
                    response = jsonify({
                        'message': "Password reset. You can now login with new password."
                    })
                    response.status_code = 200
                    return response
                else:
                    response = jsonify({
                        'message': "User email does not exist."
                    })
                    response.status_code = 404
                    return response
            else:
                response = jsonify({
                    'message': "Password must be 6 or more characters."
                })
                response.status_code = 400
                return response
        else:
            response = jsonify({
                'message': "Email Invalid. Do not include special characters."
            })
            response.status_code = 400
            return response


category_get_parser = api.parser()
category_parser = api.parser()
category_get_parser.add_argument('q', type=str, help='Search')
category_get_parser.add_argument('page', type=int, help='Page number, default=1')
category_get_parser.add_argument('limit', type=int, help='Limit per page, default=5')
category_parser.add_argument('name', type=str, help='Category name', location='form', required=True)
category_parser.add_argument('desc', type=str, help='Category Description', location='form', required=True)


@category_namespace.route('', methods=['GET', 'POST'])
class UserCategory(Resource):
    method_decorators = [token_required]

    @api.doc(parser=category_get_parser)
    def get(self, user_id, _id=None):
        """Gets all categories [ENDPOINT] GET /category"""
        args = category_get_parser.parse_args()
        q = args['q']
        page = args['page']
        limit = args['limit']

        if page:
            try:
                page = int(page)
                if page < 1:
                    return {
                               "message": "Page number must be a positive integer!! "
                           }, 400
            except Exception:
                return {
                           "message": "Invalid page value!!"
                       }, 400
        else:
            page = 1

        if limit:
            try:
                limit = int(limit)
                if limit < 1:
                    return {
                               "message": "Limit number must be a positive integer!! "
                           }, 400
            except Exception:
                return {
                           "message": "Invalid limit value!!"
                       }, 400
        else:
            limit = 5

        if q:
            _categories = Categories.query. \
                filter(Categories.name.like('%' + q + '%')).paginate(page, limit)
            user_categories = []
            for x in _categories.items:
                if x.user_id == user_id:
                    user_categories.append(x)
            if user_categories:
                categories = []
                for category in user_categories:
                    obj = {
                        "id": category.id,
                        "name": category.name,
                        "desc": category.desc,
                        "date_created": category.date_created,
                        "date_modified": category.date_modified,
                        "user_id": category.user_id
                    }
                    categories.append(obj)
                response = jsonify({
                    "categories": categories,
                    "status": "success"
                })
                response.status_code = 200
                return response
            else:
                response = jsonify({
                    "message": "Category '{}' not found".format(q),
                    "status": "error"
                })
                response.status_code = 401
                return response

        try:
            _category = Categories.query.filter_by(user_id=user_id).paginate(page, limit, error_out=True)
        except Exception as e:
            response = jsonify({
                "message": str(e).split(".")[0]+'.',
                "status": "error"
            })
            response.status_code = 401
            return response

        if _category:
            _user_categories = []
            for category in _category.items:
                obj = {
                          "id": category.id,
                          "name": category.name,
                          "desc": category.desc,
                          "date_created": category.date_created,
                          "date_modified": category.date_modified,
                          "user_id": category.user_id
                      }
                _user_categories.append(obj)
            response = jsonify({
                                   "categories": _user_categories,
                                   "status": "success"
                               })
            response.status_code = 200
            return response
        response = jsonify({
                               "message": "No categories available at the moment",
                               "status": "error"
                           })
        response.status_code = 401
        return response

    @api.expect(category_parser)
    def post(self, user_id, _id=None):
        """Handles adding a new category [ENDPOINT] POST /category"""
        post_data = category_parser.parse_args()

        category = Categories.query.filter_by(name=post_data['name']).first()

        if not category:

            if post_data:
                name = post_data['name']
                desc = post_data['desc']

                if name and desc:
                    category = Categories(name=name, desc=desc, user_id=user_id)
                    category.save()
                    obj = {
                        "id": category.id,
                        "name": category.name,
                        "desc": category.desc,
                        "date_created": category.date_created,
                        "date_modified": category.date_modified,
                        "user_id": category.user_id
                    }

                    response = jsonify({
                        "message": "Category added successfully",
                        "status": "success",
                        "category": obj
                    })
                    response.status_code = 201
                    return response
            response = jsonify({
                "message": "Name or description cannot be empty",
                "status": "error"
            })
            response.status_code = 400
            return response
        else:
            response = jsonify({
                "message": "Category already exists",
                "status": "error"
            })
            response.status_code = 400
            return response


category_parser = api.parser()
category_parser.add_argument('name', type=str, help='Category name', location='form', required=True)
category_parser.add_argument('desc', type=str, help='Category Description', location='form', required=True)


@category_namespace.route('/<int:_id>', methods=['GET', 'PUT', 'DELETE'])
class UserCategories(Resource):
    method_decorators = [token_required]

    def get(self, user_id, _id=None):
        """Gets all categories or a single category by id [ENDPOINT] GET /category and GET /category/<id>"""

        if _id:
            category = Categories.get_single(_id)
            if not category:
                response = jsonify({
                    "message": "Category not found",
                    "status": "error"
                })
                response.status_code = 401
                return response
            obj = {
                "id": category.id,
                "name": category.name,
                "desc": category.desc,
                "date_created"
                "": category.date_created,
                "date_modified": category.date_modified,
                "user_id": category.user_id
            }
            response = jsonify({
                "category": obj,
                "status": "success",
            })
            response.status_code = 200
            return response

    @api.expect(category_parser)
    def put(self, user_id, _id):
        """Handles adding updating an existing category [ENDPOINT] PUT /category/<id>"""

        category = Categories.get_single(_id)

        if category:
            post_data = category_parser.parse_args()
            if post_data:
                name = post_data['name']
                desc = post_data['desc']
                if name and desc:
                    category.update(name, desc, _id)
                    obj = {
                        "id": category.id,
                        "name": category.name,
                        "desc": category.desc,
                        "date_created": category.date_created,
                        "date_modified": category.date_modified,
                        "user_id": category.user_id
                    }
                    response = jsonify({
                        "message": "Category updated successfully",
                        "status": "success",
                        "category": obj
                    })
                    response.status_code = 200
                    return response

            response = jsonify({
                "message": "Name or description cannot be empty",
                "status": "error"
            })
            response.status_code = 400
            return response
        response = jsonify({
            "message": "Category does not exist",
            "status": "error"
        })

        response.status_code = 401
        return response

    def delete(self, user_id, _id):
        """Handles deleting an existing category [ENDPOINT] DELETE /category/<id>"""

        category = Categories.get_single(_id)
        if category:
            category.delete()
            response = jsonify({
                "message": "Category deleted successfully",
                "status": "success"
            })
            response.status_code = 200
            return response
        response = jsonify({
            "message": "Category does not exist",
            "status": "error"
        })
        response.status_code = 401
        return response


recipe_parser = api.parser()
recipe_get_parser = api.parser()
recipe_get_parser.add_argument('q', type=str, help='Search')
recipe_get_parser.add_argument('page', type=int, help='Page number, default=1')
recipe_get_parser.add_argument('limit', type=int, help='Limit per page, default=5')
recipe_parser.add_argument('name', type=str, help='Recipe name', location='form', required=True)
recipe_parser.add_argument('time', type=str, help='Expected time', location='form', required=True)
recipe_parser.add_argument('ingredients', type=str, help='Ingredients', location='form', required=True)
recipe_parser.add_argument('direction', type=str, help='Directions', location='form', required=True)


@category_namespace.route('/<int:category_id>/recipes', methods=['GET', 'POST'])
class UserRecipe(Resource):
    method_decorators = [token_required]

    @api.doc(parser=recipe_get_parser)
    def get(self, user_id, category_id, _id=None):
        """Gets all Recipes or a single recipe by id [ENDPOINT] GET /category/<int:category_id>/recipes/<int:_id> """
        args = recipe_get_parser.parse_args()
        q = args['q']
        page = args['page']
        limit = args['limit']

        if not Categories.get_single(category_id):
            response = jsonify({
                "message": "Category does not exist",
                "status": "error"
            })
            response.status_code = 401
            return response

        if page:
            try:
                page = int(page)
                if page < 1:
                    return {
                               "message": "Page number must be a positive integer!! "
                           }, 400
            except Exception:
                return {
                           "message": "Invalid page value!!"
                       }, 400
        else:
            page = 1

        if limit:
            try:
                limit = int(limit)
                if limit < 1:
                    return {
                               "message": "Limit number must be a positive integer!! "
                           }, 400
            except Exception:
                return {
                           "message": "Invalid limit value!!"
                       }, 400
        else:
            limit = 5

        if q:
            _recipes = Recipes.query. \
                filter(Recipes.name.like('%' + q + '%')).paginate(page, limit)
            user_recipes = []
            for x in _recipes.items:
                if x.category_id == category_id:
                    user_recipes.append(x)
            if user_recipes:
                recipes = []
                for recipe in user_recipes:
                    obj = {
                        "id": recipe.id,
                        "name": recipe.name,
                        "time": recipe.time,
                        "ingredients": recipe.ingredients,
                        "direction": recipe.direction,
                        "category_id": recipe.category_id,
                        "date_created": recipe.date_created,
                        "date_modified": recipe.date_modified,
                    }
                    recipes.append(obj)

                response = jsonify({
                    "recipes": recipes,
                    "status": "success"
                })
                response.status_code = 200
                return response
            else:
                response = jsonify({
                    "message": "Recipe '{}' not found".format(q),
                    "status": "error"
                })
                response.status_code = 401
                return response
        try:
            _urecipes = Recipes.query.filter_by(category_id=category_id).paginate(page, limit, error_out=True)
        except Exception as e:
            response = jsonify({
                "message": str(e).split(".")[0]+'.',
                "status": "error"
            })
            response.status_code = 401
            return response

        if _urecipes:
            recipe = Recipes.get_all(category_id)
            if not recipe:
                response = jsonify({
                    "message": "Recipe not available at the moment",
                    "status": "error"
                })
                response.status_code = 401
                return response
            _recipes2 = []
            for rec in _urecipes.items:
                obj = {
                    "id": rec.id,
                    "name": rec.name,
                    "time": rec.time,
                    "ingredients": rec.ingredients,
                    "direction": rec.direction,
                    "category_id": rec.category_id,
                    "date_created": rec.date_created,
                    "date_modified": rec.date_modified,
                }
                _recipes2.append(obj)

            response = jsonify({
                "recipes": _recipes2,
                "status": "success"
            })
            response.status_code = 200
            return response
        response = jsonify({
            "message": "Recipes not available at the moment",
            "status": "error"
        })
        response.status_code = 401
        return response

    @api.expect(recipe_parser)
    def post(self, user_id, category_id):
        """Handles adding a new recipe [ENDPOINT] POST /categories/<category_id>/recipe"""
        post_data = recipe_parser.parse_args()
        if post_data:
            name = post_data['name']
            time = post_data['time']
            ingredients = post_data['ingredients']
            direction = post_data['direction']

            if name and time and ingredients and direction:
                recipe = Recipes(name=name, time=time, ingredients=ingredients, direction=direction,
                                 category_id=category_id)
                recipe.save()
                obj = {
                    "id": recipe.id,
                    "name": recipe.name,
                    "time": recipe.time,
                    "ingredients": recipe.ingredients,
                    "direction": recipe.direction,
                    "category_id": recipe.category_id,
                    "date_created": recipe.date_created,
                    "date_modified": recipe.date_modified,
                }
                response = jsonify({
                    "message": "Recipe added successfully",
                    "status": "success",
                    "recipe": obj
                })

                response.status_code = 201
                return response
        response = jsonify({
            "message": "Name or time or ingredients or direction cannot be empty",
            "status": "error"
        })
        response.status_code = 400
        return response


recipe_parser = api.parser()

recipe_parser.add_argument('name', type=str, help='Recipe name', location='form', required=True)
recipe_parser.add_argument('time', type=str, help='Expected time', location='form', required=True)
recipe_parser.add_argument('ingredients', type=str, help='Ingredients', location='form', required=True)
recipe_parser.add_argument('direction', type=str, help='Directions', location='form', required=True)


@category_namespace.route('/<int:category_id>/recipes/<int:_id>', methods=['GET', 'PUT', 'DELETE'])
class UserRecipes(Resource):
    method_decorators = [token_required]

    def get(self, user_id, category_id, _id=None):
        """Gets all Recipes or a single recipe by id [ENDPOINT] GET /category/<int:category_id>/recipes/<int:_id> """

        if not Categories.get_single(category_id):
            response = jsonify({
                "message": "Category does not exist",
                "status": "error"
            })
            response.status_code = 401
            return response

        if _id:
            recipe = Recipes.get_single(_id, category_id)
            if not recipe:
                response = jsonify({
                    "message": "Recipe not available at the moment",
                    "status": "error"
                })
                response.status_code = 401
                return response

            obj = {
                "id": recipe.id,
                "name": recipe.name,
                "time": recipe.time,
                "ingredients": recipe.ingredients,
                "direction": recipe.direction,
                "category_id": recipe.category_id,
                "date_created": recipe.date_created,
                "date_modified": recipe.date_modified,
            }
            response = jsonify({
                "recipes": obj,
                "status": "success"
            })
            response.status_code = 200
            return response

    @api.expect(recipe_parser)
    def put(self, user_id, category_id, _id):
        """Handles updating an existing recipe [ENDPOINT] PUT /categories/<category_id>/recipes/<id>"""
        recipe = Recipes.get_single(_id, category_id)
        if recipe:
            post_data = recipe_parser.parse_args()
            if post_data:
                name = post_data['name']
                time = post_data['time']
                ingredients = post_data['ingredients']
                direction = post_data['direction']

                recipe = Recipes.update(name=name, time=time, ingredients=ingredients,
                                        direction=direction, _id=_id)

                obj = {
                    "id": recipe.id,
                    "name": recipe.name,
                    "time": recipe.time,
                    "ingredients": recipe.ingredients,
                    "direction": recipe.direction,
                    "category_id": recipe.category_id,
                    "date_created": recipe.date_created,
                    "date_modified": recipe.date_modified,
                }
                response = jsonify({
                    "message": "Recipe updated successfully",
                    "status": "success",
                    "recipe": obj
                })
                response.status_code = 200
                return response
            response = jsonify({
                "message": "Name or time or ingredients or direction cannot be empty",
                "status": "error"
            })
            response.status_code = 400
            return response
        response = jsonify({
            "message": "Recipe not found",
            "status": "error"
        })
        response.status_code = 401
        return response

    def delete(self, user_id, category_id, _id):
        """Deletes a single recipe by id [ENDPOINT] DELETE /category/<int:category_id>/recipes/<int:_id> """
        recipe = Recipes.get_single(_id, category_id)
        if recipe:
            recipe.delete()
            response = jsonify({
                "message": "Recipe deleted successfully",
                "status": "success"
            })
            response.status_code = 200
            return response
        response = jsonify({
            "message": "Recipe does not exist",
            "status": "error"
        })
        response.status_code = 401
        return response

