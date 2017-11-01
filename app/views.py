from functools import wraps

from flask import request, jsonify, abort, json

from app import api, Resource
from app.models import Users, Categories


def token_required(f):
    @wraps(f)
    def validate_user(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        access_token = auth_header.split(" ")[1] if auth_header else None
        if access_token:
            user_id = Users.decode_token(access_token)
        if isinstance(user_id, str):
            return user_id

        return f(user_id, *args, **kwargs)

    return validate_user


@api.route('/auth/register')
class UserRegistration(Resource):
    def post(self):
        """Handles POST request for auth/register"""
        post_data = json.loads(request.data)
        # check if user already exists
        user = Users.query.filter_by(email=post_data['email']).first()

        if not user:
            # There is no user, try to register them
            try:

                email = post_data['email']
                username = post_data['username']
                password = post_data['password']

                user = Users(email=email, username=username, password=password)
                user.save()

                response = jsonify({
                    "message": "You registered successfully. Please log in.",
                    "status": "success"
                })
                response.status_code = 201
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
            response.status_code = 202

            return response


@api.route('/auth/login')
class UserLogin(Resource):
    def post(self):
        """Handles POST request for /auth/login"""
        try:
            post_data = json.loads(request.data)
            # check if user exists, email is unique to each user
            user = Users.query.filter_by(email=post_data['email']).first()

            if user and user.password_is_valid(post_data['password']):
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


@api.route('/categories')
@api.route('/categories/<int:_id>')
class UserCategories(Resource):
    method_decorators = [token_required]

    def get(self, user_id, _id=None):
        if not _id:

            cat = Categories.get_all(user_id).all()
            if cat:
                categories = []
                for category in cat:
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
            response = jsonify({
                "message": "No categories available at the moment",
                "status": "error"
            })
            response.status_code = 401
            return response

    def post(self, user_id):
        post_data = json.loads(request.data)

        if post_data:
            name = post_data['name']
            desc = post_data['desc']

            if name and desc:
                category = Categories(name=name, desc=desc, user_id=user_id)
                category.save()

                response = jsonify({
                    "message": "Category added successfully",
                    "status": "success"
                })
                response.status_code = 201
                return response
        response = jsonify({
            "message": "Name or description cannot be empty",
            "status": "error"
        })
        response.status_code = 400
        return response

    def put(self, user_id, _id):

        category = Categories.get_single(_id)

        if category:
            post_data = json.loads(request.data)
            if post_data:
                name = post_data['name']
                desc = post_data['desc']
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
                response.status_code = 201
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
        response.status_code = 200
        return response
