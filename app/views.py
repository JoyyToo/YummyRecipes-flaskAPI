from functools import wraps
from flask import request, jsonify
import re
from flask_bcrypt import Bcrypt
from app import api, Resource, reqparse, app
from app.models import Users, Categories, Recipes, Sessions

INVALID_CHAR = re.compile(r"[<>/{}[\]~`*!@#$%^&()=+]")


# namespaces
auth_namespace = api.namespace('auth', description="Authentication/Authorization operations.")
category_namespace = api.namespace('category', description="Category operations.", path="/category")
recipe_namespace = api.namespace('recipe', description="Recipe operations.",
                                 path="/category/<int:category_id>/recipes")


def token_required(f):
    @wraps(f)
    def validate_user(*args, **kwargs):
        user_id = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header:
            try:
                access_token = auth_header.split(" ")[1]
            except IndexError:
                return {
                           "message": "Please Use Bearer before adding token [Bearer <token>]",
                           "status": "error"
                       }, 403
        else:
            return{
                "message": "Unauthorized, Please login or register",
                "status": "error"
            }, 403

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

                email = args['email'].strip()
                username = args['username'].strip()
                password = args['password'].strip()
                regex = r"(^[a-zA-Z0-9_.]+@[a-zA-Z0-9-]+\.[a-z]+$)"
                if re.match(regex, email):
                    if username and password:
                        if INVALID_CHAR.search(username):
                            response = jsonify({
                                "message": "Username contains invalid characters",
                                "status": "error"})
                            response.status_code = 400
                            return response

                        if len(password) < 6:
                            response = jsonify({
                                "message": "Password must be more than 6 characters.",
                                "status": "error"})
                            response.status_code = 400
                            return response

                        user = Users(email=email, username=username,
                                     password=password)
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

    @staticmethod
    def get(user_id):
        """Handles GET request for /auth/logout"""
        Sessions.logout(user_id)

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
        if re.match(regex, email) and email.strip(' '):
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
        q = request.values.get('q', '').strip().lower()
        page = args['page']
        limit = args['limit']

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

        if page:
            usrcategories = Categories.get_all(user_id).count()
            pages = int(usrcategories / limit)
            if page > pages:
                return {
                           "message": "Page not found"
                       }, 404
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
                        "name": category.name.title(),
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
                "message": str(e),
                "status": "error"
            })
            response.status_code = 401
            return response

        if _category:
            _user_categories = []
            for category in _category.items:
                obj = {
                          "id": category.id,
                          "name": category.name.title(),
                          "desc": category.desc,
                          "date_created": category.date_created,
                          "date_modified": category.date_modified,
                          "user_id": category.user_id
                      }
                _user_categories.append(obj)
            response = jsonify({'Next Page': _category.next_num,
                                'Prev Page': _category.prev_num,
                                'Has next': _category.has_next,
                                'Has previous': _category.has_prev}, _user_categories
                               )
            response.status_code = 200

            if not _user_categories:
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

        category = Categories.query.filter_by(name=post_data['name'].strip().lower()).filter_by(user_id=user_id).first()
        if not category:

            if post_data:
                name = post_data['name'].strip().lower()
                desc = post_data['desc'].strip().lower()

                if name and desc:
                    if Categories.validate_input(name=name, desc=desc):
                        response = jsonify({
                            "message": "{} contains invalid characters".format(
                                Categories.validate_input(name=name, desc=desc)),
                            "status": "error"})
                        response.status_code = 400
                        return response
                    category = Categories(name=name, desc=desc, user_id=user_id)
                    category.save()
                    obj = {
                        "id": category.id,
                        "name": category.name.title(),
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

    @staticmethod
    def get(user_id, _id=None):
        """Gets a single category by id [ENDPOINT] GET /category/<id>"""

        if _id:
            category = Categories.query.filter_by(id=_id).filter_by(user_id=user_id).first()
            if category:

                obj = {
                    "id": category.id,
                    "name": category.name.title(),
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
            response = jsonify({
                "message": "Category not found",
                "status": "error"
            })
            response.status_code = 401
            return response

    @api.expect(category_parser)
    def put(self, user_id, _id):
        """Handles adding updating an existing category [ENDPOINT] PUT /category/<id>"""

        category = Categories.query.filter_by(id=_id).filter_by(user_id=user_id).first()

        if category:
            post_data = category_parser.parse_args()
            if post_data:
                name = post_data['name'].strip().lower()
                desc = post_data['desc'].strip().lower()
                category_check = Categories.query.filter_by(name=name.strip().lower()).\
                    filter_by(user_id=user_id).first()

                if name and desc:
                    if Categories.validate_input(name=name, desc=desc):
                        response = jsonify({
                            "message": "{} contains invalid characters".format(
                                Categories.validate_input(name=name, desc=desc)),
                            "status": "error"})
                        response.status_code = 400
                        return response
                    if not category_check:
                        category.update(name, desc, _id)
                    else:
                        response = jsonify({
                            "message": "Category already exist",
                            "status": "error"
                        })

                        response.status_code = 401
                        return response

                    obj = {
                        "id": category.id,
                        "name": category.name.title(),
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

    @staticmethod
    def delete(user_id, _id):
        """Handles deleting an existing category [ENDPOINT] DELETE /category/<id>"""

        category = Categories.query.filter_by(id=_id).filter_by(user_id=user_id).first()
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


@recipe_namespace.route('', methods=['GET', 'POST'])
class UserRecipe(Resource):
    method_decorators = [token_required]

    @api.doc(parser=recipe_get_parser)
    def get(self, user_id, category_id, _id=None):
        """Gets all Recipes[ENDPOINT] GET /category/<int:category_id>/recipes """
        args = recipe_get_parser.parse_args()
        q = request.values.get('q', '').strip().lower()
        page = args['page']
        limit = args['limit']

        if not Categories.get_single(category_id):
            response = jsonify({
                "message": "Category does not exist",
                "status": "error"
            })
            response.status_code = 401
            return response

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

        if page:
            usrrecipes = Categories.get_all(user_id).count()
            pages = int(usrrecipes / limit)
            if page > pages:
                return {
                           "message": "Page not found"
                       }, 404
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
                        "name": recipe.name.title(),
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

            if not Categories.query.filter_by(id=category_id).filter_by(user_id=user_id).first():
                response = jsonify({
                    "message": "Category does not exist",
                    "status": "error"
                })
                response.status_code = 401
                return response
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
                    "name": rec.name.title(),
                    "time": rec.time,
                    "ingredients": rec.ingredients,
                    "direction": rec.direction,
                    "category_id": rec.category_id,
                    "date_created": rec.date_created,
                    "date_modified": rec.date_modified,
                }
                _recipes2.append(obj)

            response = jsonify({'Next Page': _urecipes.next_num,
                                'Prev Page': _urecipes.prev_num,
                                'Has next': _urecipes.has_next,
                                'Has previous': _urecipes.has_prev}, _recipes2)
            response.status_code = 200
            return response

    @api.expect(recipe_parser)
    def post(self, user_id, category_id):
        """Handles adding a new recipe [ENDPOINT] POST /categories/<category_id>/recipe"""
        post_data = recipe_parser.parse_args()

        recipe = Recipes.query.filter_by(name=post_data['name'].strip().lower()).\
            filter_by(category_id=category_id).first()
        if not recipe:

            if post_data:
                name = post_data['name'].strip().lower()
                time = post_data['time'].strip().lower()
                ingredients = post_data['ingredients'].strip().lower()
                direction = post_data['direction'].strip().lower()

                if name and time and ingredients and direction:
                    if Categories.validate_input(name=name, time=time,
                                                 ingredients=ingredients, direction=direction):
                        response = jsonify({
                            "message": "{} contains invalid characters".format(
                                Categories.validate_input(name=name, time=time,
                                                          ingredients=ingredients, direction=direction)),
                            "status": "error"})
                        response.status_code = 400
                        return response
                    recipe = Recipes(name=name, time=time,
                                     ingredients=ingredients, direction=direction,
                                     category_id=category_id)
                    recipe.save()
                    obj = {
                        "id": recipe.id,
                        "name": recipe.name.title(),
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
        response = jsonify({
            "message": "Recipe already exists",
            "status": "error"
        })
        response.status_code = 401
        return response


recipe_parser = api.parser()

recipe_parser.add_argument('name', type=str, help='Recipe name', location='form', required=True)
recipe_parser.add_argument('time', type=str, help='Expected time', location='form', required=True)
recipe_parser.add_argument('ingredients', type=str, help='Ingredients', location='form', required=True)
recipe_parser.add_argument('direction', type=str, help='Directions', location='form', required=True)


@recipe_namespace.route('/<int:_id>', methods=['GET', 'PUT', 'DELETE'])
class UserRecipes(Resource):
    method_decorators = [token_required]

    @staticmethod
    def get(user_id, category_id, _id=None):
        """Gets a single recipe by id [ENDPOINT] GET /category/<int:category_id>/recipes/<int:_id> """
        if not Categories.query.filter_by(id=category_id).filter_by(user_id=user_id).first():
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
                "name": recipe.name.title(),
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
        if not Categories.query.filter_by(id=category_id).filter_by(user_id=user_id).first():
            response = jsonify({
                "message": "Category does not exist",
                "status": "error"
            })
            response.status_code = 401
            return response

        recipe = Recipes.get_single(_id, category_id)
        if recipe:
            post_data = recipe_parser.parse_args()

            if post_data:
                name = post_data['name'].strip().lower()
                time = post_data['time'].strip().lower()
                ingredients = post_data['ingredients'].strip().lower()
                direction = post_data['direction'].strip().lower()

                recipe_check = Recipes.query.filter_by(name=post_data['name'].strip().lower()). \
                    filter_by(category_id=category_id).first()

                if name and time and ingredients and ingredients:
                    if Categories.validate_input(name=name, time=time,
                                                 ingredients=ingredients, direction=direction):
                        response = jsonify({
                            "message": "{} contains invalid characters".format(
                                Categories.validate_input(name=name, time=time,
                                                          ingredients=ingredients, direction=direction)),
                            "status": "error"})
                        response.status_code = 400
                        return response
                    if not recipe_check:
                        recipe = Recipes.update(name=name, time=time, ingredients=ingredients,
                                                direction=direction, _id=_id)
                    else:
                        response = jsonify({
                            "message": "Recipe already exists",
                            "status": "error"
                        })
                        response.status_code = 401
                        return response

                    obj = {
                        "id": recipe.id,
                        "name": recipe.name.title(),
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

    @staticmethod
    def delete(user_id, category_id, _id):
        """Deletes a single recipe by id [ENDPOINT] DELETE /category/<int:category_id>/recipes/<int:_id> """
        if not Categories.query.filter_by(id=category_id).filter_by(user_id=user_id).first():
            response = jsonify({
                "message": "Category does not exist",
                "status": "error"
            })
            response.status_code = 401
            return response

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
