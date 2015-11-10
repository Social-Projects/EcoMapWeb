# coding=utf-8
"""
This module holds all views controls for
ecomap project.
"""
# import sys
import json
import imghdr
import os
import time

from flask import render_template, request, jsonify, Response, g
from flask_login import login_user, logout_user, login_required, current_user
from flask.ext.wtf import Form
from flask_wtf import Form

from wtforms import FileField, SubmitField, ValidationError

import ecomap.user as usr

from ecomap.app import app, logger
from ecomap.db import util as db


class UploadForm(Form):
    image_file = FileField('Image file')
    submit = SubmitField('Submit')

    def validate_image_file(self, field):  # if name starts with validate_ + <fieldname>
                                            # flask wtf defines function as a standard validation
        if field.data.filename[-4:].lower() != '.jpg':
            raise ValidationError('Invalid file extension')  # exception from flask wtf
        if imghdr.what(field.data) != 'jpeg':
            x = imghdr.what(field.data)
            raise ValidationError('Invalid image format %s' %x)


@app.route('/api/test_photo', methods=['GET', 'POST'])
def test_photo():
    image = None
    form = UploadForm()
    if form.validate_on_submit():
        image = '/image_profile' + form.image_file.data.filename  # image path with custom name
        form.image_file.data.save('/home/padalko/ss_projects/Lv-164.UI/ecomap/www/media/image.', image)  # save method of data.
        #  app.static_folder - default flask config
    return render_template('photo_test.html', form=form, image=image)


# @app.before_request
# def load_users():
#     if current_user.is_authenticated:
#         g.user = current_user.first_name
#     else:
#         anon = usr.Anonymous()
#         g.user = anon.username
#

def make_json(sql_list):
    """
    MOVE THIS SOMEWHERE AND RENAME
    PARSES DB TUPLE INTO JSON
    :param sql_list:
    :return:
    """
    dct = {}
    for (resource_id, resource, method, perm, role_id, role) in sql_list:
        if resource not in dct:
            dct[resource] = {}
            dct[resource] = {'resource_id': int(resource_id)}
        if method not in dct[resource]:
            dct[resource][method] = {}
        if role not in dct[resource][method]:
            dct[resource][method][role] = {}
            dct[resource][method][role].update({'role_id': int(role_id),
                                                'perm': perm})
    return dct



@app.route("/api/admin")
def admin():
    return render_template("admin.html")


@app.route("/", methods=['GET'])
def index():
    """Controller starts main application page.

    return: renders html template.
    """
    return render_template("index.html")


@app.route("/api/login", methods=["POST"])
def login():
    """Login processes handler.
    Log user in or shows error messages.

    return:
        - if log in succeed:
            json with user data from db.
            Status 200 - OK
        - if user with entered email isn't exists
            or password was invalid:
            json with error message
            {'error':'message'}
            Status 401 - Unauthorized
        - if login data has invalid format:
            Status 400 - Bad Request

    """
    if request.method == "POST" and request.get_json():
        data = request.get_json()
        try:
            user = usr.get_user_by_email(data['email'])
        except KeyError:
            return jsonify(error="Bad Request", logined=0), 400
        if user and user.verify_password(data['password']):
            login_user(user, remember=True)
            return jsonify(id=user.uid,
                           name=user.first_name,
                           surname=user.last_name,
                           role='???', iat="???",
                           token=user.get_auth_token(),
                           email=user.email)
        if not user:
            return jsonify(error="There is no user with given email.",
                           logined=0), 401
        if not user.verify_password(data['password']):
            return jsonify(error="Invalid password, try again.",
                           logined=0), 401


@app.route("/api/change_password", methods=["GET"])
def change_password():
    """handler for change password
    return:
        - if succeed:
            Status 200 - OK
        - if password was invalid:
            json with error message
            {'error':'message'}
            Status 401 - Unauthorized
        - if data has invalid format:
            Status 400 - Bad Request

    """
    logger.warning('CURRENT')
    logger.warning(current_user)
    if current_user.is_authenticated:
        user = current_user
        logger.warning('AUTHEND')
        logger.warning(current_user._get_current_object())
        logger.warning(dir(current_user))
        return jsonify(authentificated=(user.uid +
                                             " " + user.first_name),
                        dir = dir(user),
                       uid = user.uid,
                       fn = user.first_name,
                       ln = user.last_name,
                       pas = user.password,
                       mail = user.email,
                       cu = current_user.__dict__
                       )
    if not current_user.is_authenticated:
        user = usr.Anonymous()
        logger.warning('NOT AUTH')
        logger.warning(user.username)
        return jsonify(error="you are not logged in - you are anon.",
                           logined=0,
                       cu = current_user.__dict__), 401
        # if not user.verify_password(data['password']):
        #     return jsonify(error="Invalid password, try again.",
        #                    logined=0), 401


@app.route("/api/logout", methods=["POST", 'GET'])
@login_required
def logout():
    """Method for user's log out.

    return:
        - if logging out was successful:
            json {result:True}
        - in case of problems:
            json {result:False}
    """
    result = logout_user()
    return jsonify(result=result)


@app.route("/api/register", methods=["POST"])
def register():
    """Method for registration new user in db.
    Method checks if user is not exists and handle
    registration processes.

    return:
        - if one of the field is incorrect or empty:
            json {'error':'Unauthorized'}
            Status 401 - Unauthorized
        - if user already exists
            Status 400 - Bad Request
            json {'status': 'user with this email already exists'}
        - if registration was successful:
            json {'status': added user <username>}
            Status 200 - OK
    """
    if request.method == 'POST' and request.get_json():
        data = request.get_json()
        arguments = ['firstName', 'lastName', 'email',
                     'password', 'pass_confirm']
        # TODO separate user func
        try:
            if [v for k, v in request.get_json().iteritems() if
                    not v or k not in arguments]:
                return jsonify(error="Unauthorized,"
                                     " some fields are empty"), 401
            first_name = data['firstName']
            last_name = data['lastName']
            email = data['email']
            password = data['password']
        except KeyError:
            return jsonify(error="Unauthorized, missing fields"), 401
        if not usr.get_user_by_email(email):
            usr.register(first_name, last_name, email, password)
            status = 'added %s %s' % (first_name, last_name)
        else:
            status = 'user with this email already exists'
            return jsonify({'status': status}), 400
        return jsonify({'status': status})


@app.route("/api/email_exist", methods=['POST'])
def email_exist():
    if request.method == "POST" and request.get_json():
        data = request.get_json()
        # return jsonify(email=data)
        user = usr.get_user_by_email(data['email'])
        if user:
            return jsonify(), 200
        else:
            return jsonify(), 401


# API ECOMAP-007 MOCK-Routes
@app.route("/api/problems", methods=['GET'])
def get_problems():
    """
    Get all moderated problems in
     brief (id, title, coordinates, type and status);
    return: list of jsons
    """
    data = [
        {
            'id': 1,
            'title': 'xxxx',
            'Title': "Xxxxxxx",
            'Latitude': 45.350166,
            'Longtitude': 29.001091,
            'ProblemTypes_Id': 4,
            'Status': 1,
            'Date': '2014-02-18T07:15:51.000Z'
        },
    ]
    return Response(json.dumps(data), mimetype='application/json')


@app.route("/api/problems/<int:id>", methods=['GET'])
def get_problems_by_id(id):
    """
    get detailed problem description
    (all information from tables 'Problems', 'Activities', 'Photos')
    by it's id;
    """

    data = [
        [
            {
                "Id": 5,
                "Title": "Загрязнение Днепра",
                "Content": "В городе Берислав нет "
                           "очистных сооружений.",
                "Proposal": "",
                "Severity": 3,
                "Moderation": 1,
                "Votes": 13,
                "Latitude": 46.8326,
                "Longtitude": 33.416462,
                "Status": 0,
                "ProblemTypes_Id": 4
            }
        ],
        [],
        [
            {
                "Id": 5,
                "Content": "{\"Content\":\"Проблему "
                           "додано анонімно\",\"userName\""
                           ":\"(Анонім)\"}",
                "Date": "2014-02-27T15:24:53.000Z",
                "ActivityTypes_Id": 1,
                "Users_Id": 2,
                "Problems_Id": 5
            }
        ]
    ] if id == 1 else {'data': 'select ID=1'}
    return Response(json.dumps(data), mimetype='application/json')


@app.route("/api/users/<int:idUser>", methods=['GET'])
def get_user_by_id(idUser):
    """
    get user's name and surname by id;
    :return
        - JSON with user's name and surname or
            empty JSON if there is no
            user with selected id
    """

    data = dict(json=[
        {
            "Name": "admin",
            "Surname": None
        }
    ], length=1) if idUser == 1 else {}

    return jsonify(data)


@app.route("/api/usersProblem/<int:id>", methods=['GET'])
def get_users_problems(id):
    """
    Get all user's problems in brief
    (id, title, coordinates, type and status) by user's id;
    :return
        - returns array of user's problems and empty array
        if there is no user with such id
    """

    data = [
        dict(Id=190,
             Title="назва3333",
             Latitude=51.419765,
             Longtitude=29.520264,
             ProblemTypes_Id=1,
             Status=0,
             Date="2015-02-24T14:27:22.000Z")
    ] if id == 1 else []

    return Response(json.dumps(data), mimetype='application/json')


@app.route("/api/activities/<int:idUser>", methods=['GET'])
def get_user_activities(idUser):
    """
    get all user's activity
    (id, type, description and id of related problem);
    :return: json
    """
    data = dict(
        id=1,
        type='activitytype',
        description='description',
        problem_id=2
    ) if idUser == 1 else {}
    return jsonify(data)


@app.route("/api/problempost", methods=['POST'])
def post_problem():
    """
    post new detailed environment problem to the server
    Request Content-Type: multipart/form-data;

    Request parameters:
    title	optional
    content	optional
    proposal	optional
    latitude	optional
    longitude	optional
    type	1-6, required
    userId	optional
    userName	optional
    userSurname	optional

       :return: json Content-type: application/json;charset=UTF-8
    """
    if request.method == 'POST' and request.form:
        input_data = request.form
        # logger.warning(input_data)
        # logger.warning(request.content_type)
        try:
            input_data['type']
        except KeyError:
            logger.warning('no required parameter')
            return jsonify(err="ER_BAD_NULL_ERROR"), 500
        try:
            int(input_data['userId'])
        except ValueError:
            logger.warning('user id not a int')
            return jsonify(Response='500 Internal Server Error'), 500
        except KeyError:
            pass
        output = {
            "json": {
                'test': input_data['type'],
                "fieldCount": 0,
                "affectedRows": 1,
                "insertId": 191,
                "serverStatus": 2,
                "warningCount": 0,
                "message": "\u0000",
                "protocol41": True,
                "changedRows": 0
            }
        }
        return jsonify(output)


@app.route("/api/resources", methods=['GET', 'POST', 'PUT', 'DELETE'])
def get_resource():
    """NEW!
    get list of site resources needed for administration.
    and server permission control.
    action PUT:
    'resourse_name' = changes to name of the resource.
    'resourse_id' = key to search name of the resource in db.
    action DELETE:
    'resource_name' = that has to be Deleted.
    'resource_id' = key to search name of resource in db to delete.

       :return:
            - list of jsons
            - if no resource in DB
                return empty json
    """

    if request.method == "POST" and request.get_json():
        data = request.get_json()
        try:
            db.add_resource(data['resource_name'])
        except KeyError:
            return jsonify(error="Bad Request[key_error]"), 400
        return jsonify(added_resource=data['resource_name'])

    # edit resource by id
    if request.method == "PUT" and request.get_json():
        edit_data = request.get_json()
        try:
            db.edit_resource_by_id(edit_data['resource_name'],
                             edit_data['resource_id'])
        except KeyError:
            return jsonify(error="Bad Request[key_error]"), 400
        return jsonify(status="success", edited=edit_data['resource_name'])

    # #edit resource by value
    # if request.method == "PUT" and request.get_json():
    #     edit_data = request.get_json()
    #     try:
    #         db.edit_resource_value(edit_data['old_resource_value'],
    #                                edit_data['new_resource_value'])
    #     except KeyError:
    #         return jsonify(error="Bad Request[key_error]"), 400
    #     return jsonify(status="success",
    #                    edited=edit_data['new_resource_value'])

    # # delete by id
    # if request.method == "DELETE" and request.get_json():
    #     del_data = request.get_json()
    #     try:
    #         db.delete_resource_by_id(del_data['resource_name'],
    #                                  del_data['resource_id'])
    #     except KeyError:
    #         return jsonify(error="Bad Request[key_error]"), 400
    #     return jsonify(status="success",
    #                    deleted_resource=del_data['resource_name'])

    if request.method == "DELETE" and request.get_json():
        del_data = request.get_json()
        try:
            db.delete_resource(del_data['resource_name'])
        except KeyError:
            return jsonify(error="Bad Request[key_error]"), 400
        return jsonify(status="success",
                       deleted_resource=del_data['resource_name'])

    parsed_data = db.get_all_resources()
    return Response(json.dumps(parsed_data), mimetype='application/json')


@app.route("/api/roles", methods=['GET', 'POST', 'PUT', 'DELETE'])
def roles():
    """NEW!
    get list of roles for server permission control.
    action GET:
    'role_name' = name of role in db.
    action POST:
    'role_name' = name of the role.
    action PUT:
    'role_name' = changes to name of the role
    'role_id' = key to search name of the role in db
    action DELETE:
    'role_name' = that has to be Deleted
    'role_id' = key to search name of resource in db to delete
       :return:
            - list of jsons(dicts)
            - if no resource in DB
                return empty dict
    """

    if request.method == "POST" and request.get_json():
        data = request.get_json()
        try:
            db.add_role(data['role_name'])
        except KeyError:
            return jsonify(error="Bad Request[key_error]"), 400
        return jsonify(added_resource=data['role_name'])

    # edit role by id
    if request.method == "PUT" and request.get_json():
        edit_data = request.get_json()
        try:
            db.edit_role_by_id(edit_data['role_name'], edit_data['role_id'])
        except KeyError:
            return jsonify(error="Bad Request[key_error]"), 400
        return jsonify(status="success", edited=edit_data['role_name'])

    # # edit role by value
    # if request.method == "PUT" and request.get_json():
    #     edit_data = request.get_json()
    #     try:
    #         db.edit_role_value(edit_data['old_role_value'],
    #                            edit_data['new_role_value'])
    #     except KeyError:
    #         return jsonify(error="Bad Request[key_error]"), 400
    #     return jsonify(status="success", edited=edit_data['new_role_value'])

    # delete role by id
    # if request.method == "DELETE" and request.get_json():
    #     del_data = request.get_json()
    #     try:
    #         db.delete_role_by_id(del_data['role_name'], del_data['role_id'])
    #     except KeyError:
    #         return jsonify(error="Bad Request[key_error]"), 400
    #     return jsonify(status="success",
    #                    deleted_resource=del_data['role_name'])

    if request.method == "DELETE" and request.get_json():
        data = request.get_json()
        try:
            db.delete_role(data['role_name'])
        except KeyError:
            return jsonify(error="Bad Request[key_error]"), 400
        return jsonify(status="success",
                       deleted_resource=data['role_name'])

    parsed_data = db.get_roles()
    logger.warning(parsed_data)
    return Response(json.dumps(parsed_data), mimetype='application/json')


@app.route("/api/permissions", methods=['GET', 'PUT', 'POST'])
def permissions():
    """NEW!
    get and add actions of
    server permission control.

       :return:
            - list of lists with permission data
                [id,action,modifier,resource)
            - if no resource in DB
                return empty json
    """

    if request.method == "POST" and request.get_json():
        data = request.get_json()
        try:
            db.add_permission(data['resource_name'])
        except KeyError:
            return jsonify(error="Bad Request[key_error]"), 400
        return jsonify(added_permission_for=data['resource_name'])

    if request.method == "PUT" and request.get_json():
        edit_data = request.get_json()
        try:
            db.update_role_permission(edit_data['resource_name'],
                                      edit_data['action'],
                                      edit_data['modifier'],
                                      edit_data['role_name'])
        except KeyError:
            return jsonify(error="Bad Request[key_error]"), 400
        return jsonify(status="success", edited=edit_data['role_name'])

    parsed_data = db.get_permissions()
    return Response(json.dumps(parsed_data), mimetype='application/json')


@app.route("/api/get_all_permissions", methods=['GET', 'POST'])
def get_all():
    """NEW!
        SHOW TABLE
        makes join
       :return:
            - list of jsons
            - if no resource in DB
                return empty json
    """
    parsed_data = db.select_all()
    res = make_json(parsed_data)
    return jsonify(res)


if __name__ == "__main__":
    app.run()

    app.logger = logger
    # usr.login_manager.init_app(app)

    # user = usr.User.get(username="admin")
    # print user
    # login_user(user, remember=True)
