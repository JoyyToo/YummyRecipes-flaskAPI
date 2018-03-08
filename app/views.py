from functools import wraps
from flask import request, jsonify, url_for
import re
import humanize
from itsdangerous import URLSafeTimedSerializer
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from app import api, Resource, app
from app.models import Users, Categories, Recipes, Blacklist

mail = Mail(app)

recipients = []
sender = 'Admin'

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

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
            return {
                       "message": "Unauthorized, Please login or register",
                       "status": "error"
                   }, 403

        token_auth = Users.decode_token(access_token)

        if token_auth in ["expired", "invalid"]:
            if token_auth == "expired":
                return {"message": "Expired token. Please login to get a new token"}, 403
            else:
                return {"message": "Invalid token. Please register or login"}, 403

        if access_token:
            user_id = Users.decode_token(access_token)
            if user_id:
                if isinstance(user_id, int):
                    blacklisted = Blacklist.query.filter_by(revoked_token=str(access_token)).first()

                    if blacklisted:
                        response = jsonify({
                            "message": "Session not available, Please login",
                            "status": "error"
                        })
                        response.status_code = 401
                        return response
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

                if len(email) > 40 or len(username) > 40:
                    response = jsonify({
                        "Message": "Please make the length of the email or username less than 40 characters",
                        "Status": "error"
                    })
                    response.status_code = 400
                    return response

                regex = r"(^[a-zA-Z0-9_.]+@[a-zA-Z0-9-]+\.[a-z]+$)"
                if username and password:
                    if re.match(regex, email):

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

                        response = jsonify({
                            "message": "You registered successfully. Please log in.",
                            "status": "success"
                        })
                        response.status_code = 201
                        return response
                    else:

                        response = jsonify({
                            "message": "Please enter a valid email address",
                            "status": "error"
                        })

                        response.status_code = 400
                        return response
                response = jsonify({
                    "message": "Please fill all fields",
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
                if access_token:
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
    def post(user_id):
        """Handles POST request for /auth/logout"""
        auth_header = request.headers.get('Authorization', '')
        access_token = auth_header.split(" ")[1]

        revoked_token = Blacklist(revoked_token=access_token)
        revoked_token.save()

        response = jsonify({
            "message": "You logged out successfully.",
            "status": "success"
        })
        response.status_code = 200
        return response


def email_notification(subject, recipients, _link):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = "Use the token to reset password in the app: {}".format(_link)
    with app.app_context():
        mail.send(msg)
    return "\n\nEmail sent successfully\n\n"


reset_parser = api.parser()
reset_parser.add_argument('email', type=str, help='Email', location='form', required=True)


@auth_namespace.route('/reset-password')
class ResetPasswordView(Resource):

    @api.expect(reset_parser)
    def post(self):
        """Handles POST request for /auth/reset-password"""
        data = reset_parser.parse_args()
        email = data['email']

        regex = r"(^[a-zA-Z0-9_.]+@[a-zA-Z0-9-]+\.[a-z]+$)"
        if re.match(regex, email) and email.strip(' '):
            user = Users.query.filter_by(email=email).first()
            if user:
                token = s.dumps(email, salt='password-reset')
                recipients.append(email)
                _link = 'http://localhost:3000/newpassword/' + token

                email_notification('Reset password', recipients, _link)

                response = jsonify({
                    'message': 'A reset link has been sent to : {} <br/>'.format(email),
                    'status': 'success'
                })
                response.status_code = 200
                return response
            else:
                response = jsonify({
                    'message': "User email does not exist.",
                    'status': 'error'
                })
                response.status_code = 404
                return response

        else:
            response = jsonify({
                'message': "Email Invalid. Do not include special characters.",
                'status': 'error'
            })
            response.status_code = 400
            return response


new_parser = api.parser()
new_parser.add_argument('newpassword', type=str, help='New password', location='form')


@auth_namespace.route('/new-password/<token>')
class NewPasswordView(Resource):

    @api.expect(new_parser)
    def post(self, token):
        """Handles POST request for /auth/new-password/<token>"""
        data = new_parser.parse_args()
        password = data['newpassword']

        try:
            email = s.loads(token, salt='password-reset', max_age=60 * 10)  # 24hrs
            user = Users.query.filter_by(email=email).first()

            if user:
                if len(password) < 6:
                    response = jsonify({
                        "message": "Password must be more than 6 characters.",
                        "status": "error"})
                    response.status_code = 400
                    return response
                user.password = Bcrypt().generate_password_hash(password).decode()
                user.save()
                response = jsonify({
                    "message": "Password for {} has been reset. You can now login".format(email, password),
                    "status": "success"
                })
                response.status_code = 200
                return response

            response = jsonify({
                "message": "Invalid user",
                "status": "error"
            })
            response.status_code = 200
            return response
        except Exception as e:
            return 'You are not allowed to do this operation'


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
    def get(self, user_id):
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
            categories = Categories.query. \
                filter(Categories.name.like('%' + q + '%')).paginate(page, limit)
            user_categories = []
            for x in categories.items:
                if x.user_id == user_id:
                    user_categories.append(x)
            if user_categories:
                categories = []
                for category in user_categories:
                    obj = {
                        "id": category.id,
                        "name": category.name.title(),
                        "desc": category.desc,
                        "date_created": humanize.naturaldate(category.date_created),
                        "date_modified": humanize.naturaldate(category.date_modified),
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
                response.status_code = 404
                return response

        try:
            recipe_category = Categories.query.filter_by(user_id=user_id).paginate(page, limit, error_out=True)
        except Exception as e:
            response = jsonify({
                "message": str(e),
                "status": "error"
            })
            response.status_code = 400
            return response

        if recipe_category:
            recipecategories = []
            for category in recipe_category.items:
                obj = {
                    "id": category.id,
                    "name": category.name.title(),
                    "desc": category.desc,
                    "date_created": humanize.naturaldate(category.date_created),
                    "date_modified": humanize.naturaldate(category.date_modified),
                    "user_id": category.user_id
                }
                recipecategories.append(obj)
            response = jsonify({'Next Page': recipe_category.next_num,
                                'Prev Page': recipe_category.prev_num,
                                'Has next': recipe_category.has_next,
                                'total items': recipe_category.total,
                                'current page': recipe_category.page,
                                'total pages': recipe_category.pages,
                                'Has previous': recipe_category.has_prev}, recipecategories
                               )
            response.status_code = 200

            if not recipecategories:
                response = jsonify({
                    "message": "No categories available at the moment",
                    "status": "error"
                })
                response.status_code = 401

            return response

    @api.expect(category_parser)
    def post(self, user_id):
        """Handles adding a new category [ENDPOINT] POST /category"""
        post_data = category_parser.parse_args()

        category = Categories.query.filter_by(name=post_data['name'].strip().lower()).filter_by(user_id=user_id).first()
        if not category:

            if post_data:
                name = post_data['name'].strip().lower()
                desc = post_data['desc'].strip().lower()

                if len(name) > 30:
                    response = jsonify({
                        "Message": "Please make the length of the name less than 30 characters",
                        "Status": "error"
                    })
                    response.status_code = 400
                    return response

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
                        "date_created": humanize.naturaldate(category.date_created),
                        "date_modified": humanize.naturaldate(category.date_modified),
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
                    "": humanize.naturaldate(category.date_created),
                    "date_modified": humanize.naturaldate(category.date_modified),
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
            response.status_code = 404
            return response

    @api.expect(category_parser)
    def put(self, user_id, _id):
        """Handles adding updating an existing category [ENDPOINT] PUT /category/<id>"""

        category = Categories.query.filter_by(id=_id).first()

        if category:
            post_data = category_parser.parse_args()
            if post_data:
                name = post_data['name'].strip().lower()
                desc = post_data['desc'].strip().lower()

                if len(name) > 30:
                    response = jsonify({
                        "Message": "Please make the length of the name less than 30 characters",
                        "Status": "error"
                    })
                    response.status_code = 400
                    return response

                if name and desc:
                    if Categories.validate_input(name=name, desc=desc):
                        response = jsonify({
                            "message": "{} contains invalid characters".format(
                                Categories.validate_input(name=name, desc=desc)),
                            "status": "error"})
                        response.status_code = 400
                        return response
                    check_category = Categories.query.filter_by(user_id=user_id, name=name.strip().lower()).first()
                    if check_category:

                        response = jsonify({
                            "message": "Category already exists",
                            "status": "error",
                        })
                        response.status_code = 400
                        if check_category.id != _id:
                            return response

                    category.update(name, desc, _id)

                    obj = {
                        "id": category.id,
                        "name": category.name.title(),
                        "desc": category.desc,
                        "date_created": humanize.naturaldate(category.date_created),
                        "date_modified": humanize.naturaldate(category.date_modified),
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

        response.status_code = 404
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
        response.status_code = 404
        return response


recipe_parser = api.parser()
recipe_get_parser = api.parser()
recipe_get_parser.add_argument('q', type=str, help='Search')
recipe_get_parser.add_argument('page', type=int, help='Page number, default=1')
recipe_get_parser.add_argument('limit', type=int, help='Limit per page, default=5')
recipe_parser.add_argument('name', type=str, help='Recipe name', location='form', required=True)
recipe_parser.add_argument('time', type=str, help='Expected time', location='form', required=True)
recipe_parser.add_argument('ingredients', type=str, help='Ingredients', location='form', required=True)
recipe_parser.add_argument('procedure', type=str, help='Procedures', location='form', required=True)


@recipe_namespace.route('', methods=['GET', 'POST'])
class UserRecipe(Resource):
    method_decorators = [token_required]

    @api.doc(parser=recipe_get_parser)
    def get(self, user_id, category_id):
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
            response.status_code = 404
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

            recipes = Recipes.query. \
                filter(Recipes.name.like('%' + q + '%')).paginate(page, limit)
            user_recipes = []
            for x in recipes.items:
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
                        "procedure": recipe.procedure,
                        "category_id": recipe.category_id,
                        "date_created": humanize.naturaldate(recipe.date_created),
                        "date_modified": humanize.naturaldate(recipe.date_modified),
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
                response.status_code = 404
                return response
        try:
            category_recipes = Recipes.query.filter_by(category_id=category_id).paginate(page, limit, error_out=True)
        except Exception as e:
            response = jsonify({
                "message": str(e).split(".")[0] + '.',
                "status": "error"
            })
            response.status_code = 401
            return response

        if category_recipes:

            if not Categories.query.filter_by(id=category_id).filter_by(user_id=user_id).first():
                response = jsonify({
                    "message": "Category does not exist",
                    "status": "error"
                })
                response.status_code = 404
                return response
            recipe = Recipes.get_all(category_id)
            if not recipe:
                response = jsonify({
                    "message": "Recipe not available at the moment. You can add some.",
                    "status": "error"
                })
                response.status_code = 404
                return response
            categoryrecipes = []
            for rec in category_recipes.items:
                obj = {
                    "id": rec.id,
                    "name": rec.name.title(),
                    "time": rec.time,
                    "ingredients": rec.ingredients,
                    "procedure": rec.procedure,
                    "category_id": rec.category_id,
                    "date_created": humanize.naturaldate(rec.date_created),
                    "date_modified": humanize.naturaldate(rec.date_modified),
                }
                categoryrecipes.append(obj)

            response = jsonify({'Next Page': category_recipes.next_num,
                                'Prev Page': category_recipes.prev_num,
                                'Has next': category_recipes.has_next,
                                'total items': category_recipes.total,
                                'current page': category_recipes.page,
                                'total pages': category_recipes.pages,
                                'Has previous': category_recipes.has_prev}, categoryrecipes)
            response.status_code = 200
            return response

    @api.expect(recipe_parser)
    def post(self, user_id, category_id):
        """Handles adding a new recipe [ENDPOINT] POST /categories/<category_id>/recipe"""
        post_data = recipe_parser.parse_args()

        if not Categories.query.filter_by(id=category_id).filter_by(user_id=user_id).first():
            response = jsonify({
                "message": "Category does not exist",
                "status": "error"
            })
            response.status_code = 404
            return response

        recipe = Recipes.query.filter_by(name=post_data['name'].strip().lower()). \
            filter_by(category_id=category_id).first()
        if not recipe:

            if post_data:
                name = post_data['name'].strip().lower()
                time = post_data['time'].strip().lower()
                ingredients = post_data['ingredients'].strip().lower()
                procedure = post_data['procedure'].strip().lower()

                if len(name) >= 30 or len(time) >= 30:
                    response = jsonify({
                        "Message": "Please make the name or time shorter than 30 characters",
                        "Status": "error"
                    })
                    response.status_code = 400
                    return response

                if name and time and ingredients and procedure:
                    if Categories.validate_input(name=name, time=time,
                                                 ingredients=ingredients, procedure=procedure):
                        response = jsonify({
                            "message": "{} contains invalid characters".format(
                                Categories.validate_input(name=name, time=time,
                                                          ingredients=ingredients, procedure=procedure)),
                            "status": "error"})
                        response.status_code = 400
                        return response
                    recipe = Recipes(name=name, time=time,
                                     ingredients=ingredients, procedure=procedure,
                                     category_id=category_id, user_id=user_id)
                    recipe.save()
                    obj = {
                        "id": recipe.id,
                        "name": recipe.name.title(),
                        "time": recipe.time,
                        "ingredients": recipe.ingredients,
                        "procedure": recipe.procedure,
                        "category_id": recipe.category_id,
                        "date_created": humanize.naturaldate(recipe.date_created),
                        "date_modified": humanize.naturaldate(recipe.date_modified),

                    }
                    response = jsonify({
                        "message": "Recipe added successfully",
                        "status": "success",
                        "recipe": obj
                    })

                    response.status_code = 201
                    return response
            response = jsonify({
                "message": "Name or time or ingredients or procedure cannot be empty",
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
recipe_parser.add_argument('procedure', type=str, help='procedures', location='form', required=True)


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
            response.status_code = 404
            return response

        if _id:
            recipe = Recipes.get_single(_id, category_id)
            if not recipe:
                response = jsonify({
                    "message": "Recipe not available at the moment. You can add some",
                    "status": "error"
                })
                response.status_code = 404
                return response

            obj = {
                "id": recipe.id,
                "name": recipe.name.title(),
                "time": recipe.time,
                "ingredients": recipe.ingredients,
                "procedure": recipe.procedure,
                "category_id": recipe.category_id,
                "date_created": humanize.naturaldate(recipe.date_created),
                "date_modified": humanize.naturaldate(recipe.date_modified),
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
            response.status_code = 404
            return response

        recipe = Recipes.get_single(_id, category_id)

        if recipe:
            post_data = recipe_parser.parse_args()

            if post_data:
                name = post_data['name'].strip().lower()
                time = post_data['time'].strip().lower()
                ingredients = post_data['ingredients'].strip().lower()
                procedure = post_data['procedure'].strip().lower()

                if len(name) > 30 or len(time) > 30:
                    response = jsonify({
                        "Message": "Please make the length of the name or time shorter than 30 characters",
                        "Status": "error"
                    })
                    response.status_code = 400
                    return response

                if name and time and ingredients and procedure:
                    if Categories.validate_input(name=name, time=time,
                                                 ingredients=ingredients, procedure=procedure):
                        response = jsonify({
                            "message": "{} contains invalid characters".format(
                                Categories.validate_input(name=name, time=time,
                                                          ingredients=ingredients, procedure=procedure)),
                            "status": "error"})
                        response.status_code = 400
                        return response

                    recipe_check = Recipes.query.filter_by(user_id=user_id, category_id=category_id,
                                                           name=name.strip().lower()).first()

                    if recipe_check:

                        response = jsonify({
                            "message": "Recipe already exists",
                            "status": "error"
                        })
                        response.status_code = 400

                        if recipe_check.id != _id:
                            return response
                    recipe.update(name, time, ingredients, procedure, _id)

                    obj = {
                        "id": recipe.id,
                        "name": recipe.name.title(),
                        "time": recipe.time,
                        "ingredients": recipe.ingredients,
                        "procedure": recipe.procedure,
                        "category_id": recipe.category_id,
                        "date_created": humanize.naturaldate(recipe.date_created),
                        "date_modified": humanize.naturaldate(recipe.date_modified),
                    }
                    response = jsonify({
                        "message": "Recipe updated successfully",
                        "status": "success",
                        "recipe": obj
                    })
                    response.status_code = 200
                    return response
                response = jsonify({
                    "message": "Name or time or ingredients or procedure cannot be empty",
                    "status": "error"
                })
                response.status_code = 400
                return response
        response = jsonify({
            "message": "Recipe not found",
            "status": "error"
        })
        response.status_code = 404
        return response

    @staticmethod
    def delete(user_id, category_id, _id):
        """Deletes a single recipe by id [ENDPOINT] DELETE /category/<int:category_id>/recipes/<int:_id> """
        if not Categories.query.filter_by(id=category_id).filter_by(user_id=user_id).first():
            response = jsonify({
                "message": "Category does not exist",
                "status": "error"
            })
            response.status_code = 404
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
        response.status_code = 404
        return response
