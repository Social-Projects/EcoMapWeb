"""Module contains routes, used for admin page."""
import json

from flask import request, jsonify, Response, session
from flask_login import login_required

from ecomap import validator
from ecomap.app import app, logger
from ecomap.db import util as db
from ecomap.permission import permission_control


@app.route("/api/resources", methods=['POST'])
@login_required
def resource_post():
    """Function which edits resource name.
    :return: If there is already resource with this name:
                 {'error': 'resource already exists'}, 400
             If request data is invalid:
                 {'status': False, 'error': [list of errors]}, 400
             If all ok:
                 {'added_resource': 'resource_name',
                  'resource_id': 'resource_id'}
    """
    data = request.get_json()

    valid = validator.resource_post(data)

    if valid['status']:
        if db.get_resource_id(data['resource_name']):
            return jsonify(error='Resource already exists'), 400

        db.add_resource(data['resource_name'])
        added_res_id = db.get_resource_id(data['resource_name'])
        response = jsonify(added_resource=data['resource_name'],
                           resource_id=added_res_id[0])
        session['access_control'] = permission_control.reload_dct()
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400
    return response


@app.route("/api/resources", methods=['PUT'])
@login_required
def resource_put():
    """Function which edits resource name.
    :return: If there is already resource with this name:
                 {'error': 'this name already exists'}, 400
             If request data is invalid:
                 {'status': False, 'error': [list of errors]}, 400
             If all ok:
                 {'status': 'success', 'edited': 'resource_name'}
    """
    data = request.get_json()
    valid = validator.resource_put(data)

    if valid['status']:
        if db.get_resource_id(data['resource_name']):
            return jsonify(error='this name already exists'), 400

        db.edit_resource_name(data['resource_name'],
                              data['resource_id'])
        response = jsonify(status='success',
                           edited=data['resource_name'])
        session['access_control'] = permission_control.reload_dct()
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400
    return response


@app.route("/api/resources", methods=['DELETE'])
@login_required
def resource_delete():
    """Function which deletes resource from database.
       Before delete checks if resource have any permissions.
    :return: If resource have permissions:
                 {'error': 'Cannot delete!'}, 400
             If request data is invalid:
                 {'status': False, 'error': [list of errors]}, 400
             If all ok:
                 {'status': 'success', 'deleted_resource': 'resource_id'}
    """
    data = request.get_json()
    valid = validator.resource_delete(data)

    if valid['status']:
        if not db.check_resource_deletion(data['resource_id']):
            db.delete_resource_by_id(data['resource_id'])
            response = jsonify(status='success',
                               deleted_resource=data['resource_id'])
            session['access_control'] = permission_control.reload_dct()
        else:
            response = jsonify(error='Cannot delete!'), 400
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400
    return response


@app.route("/api/resources", methods=['GET'])
@login_required
def resource_get():
    """Function which returns all resources from database.
       :return: {'resource_name': 'resource_id'}
    """
    query = db.get_all_resources()
    parsed_data = {}
    if query:
        parsed_data = {res[1]: res[0] for res in query}
    return jsonify(parsed_data)


@app.route("/api/roles", methods=['POST'])
@login_required
def role_post():
    """Function which adds new role into database.
    :return: If there is already role with this name:
                 {'error': 'role already exists'}, 400
             If request data is invalid:
                 {'status': False, 'error': [list of errors]}, 400
             If all ok:
                 {'added_role': 'role_name',
                  'added_role_id': 'role_id'}
    """
    data = request.get_json()
    valid = validator.role_post(data)

    if valid['status']:
        if db.get_role_id(data['role_name']):
            return jsonify(error='role already exists'), 400

        db.insert_role(data['role_name'])
        added_role_id = db.get_role_id(data['role_name'])

        response = jsonify(added_role=data['role_name'],
                           added_role_id=added_role_id[0])
        session['access_control'] = permission_control.reload_dct()
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400
    return response


@app.route("/api/roles", methods=['PUT'])
@login_required
def role_put():
    """Function which edits role name.
    :return: If there is already resource with this name:
                 {'error': 'this name already exists'}, 400
             If request data is invalid:
                 {'status': False, 'error': [list of errors]}, 400
             If all ok:
                 {'status': 'success', 'edited': 'resource_name'}
    """
    data = request.get_json()
    valid = validator.role_put(data)

    if valid['status']:
        if db.get_role_id(data['role_name']):
            return jsonify(error='this name already exists'), 400

        db.edit_role(data['role_name'], data['role_id'])
        response = jsonify(status='success',
                           edited=data['role_name'])
        session['access_control'] = permission_control.reload_dct()
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400
    return response


@app.route("/api/roles", methods=['DELETE'])
@login_required
def role_delete():
    """Function which deletes role from database.
    :return: If role has permissions:
                 {'error': 'Cannot delete!'}
             If request data is invalid:
                 {'status': False, error: [list of errors]}, 400
             If all ok:
                 {'status': 'success', 'deleted_role': 'role_id'}
    """
    data = request.get_json()

    valid = validator.role_delete(data)

    if valid['status']:
        if not db.check_role_deletion(data['role_id']):
            db.delete_role_by_id(data['role_id'])
            response = jsonify(msg='success',
                                   deleted_role=data['role_id'])
            session['access_control'] = permission_control.reload_dct()
        else:
            response = jsonify(error='Cannot delete!')
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400
    return response


@app.route("/api/roles", methods=['GET'])
@login_required
def role_get():
    """Function which gets all roles from database.
       :return: {'role_name': 'role_id'}
    """
    query = db.get_all_roles()
    parsed_data = {}
    if query:
        parsed_data = {res[1]: res[0] for res in query}
    return jsonify(parsed_data)


@app.route("/api/permissions", methods=['POST'])
@login_required
def permission_post():
    """Function which adds new permission into database.
    :return: If request data is invalid:
                 {'status': False, 'error': [list of errors]}, 400
             If all ok:
                 {'added_permission': 'description',
                  'permission_id': 'permission_id'}
    """

    if request.method == 'POST' and request.get_json():
        data = request.get_json()
        valid = validator.permission_post(data)

        if valid['status']:
            db.insert_permission(data['resource_id'],
                                 data['action'],
                                 data['modifier'],
                                 data['description'])
            added_perm_id = db.get_permission_id(data['resource_id'],
                                                 data['action'],
                                                 data['modifier'])
            response = jsonify(added_permission_for=data['description'],
                               permission_id=added_perm_id[0])
            session['access_control'] = permission_control.reload_dct()
        else:
            response = Response(json.dumps(valid),
                                mimetype='application/json'), 400
        return response


@app.route("/api/permissions", methods=['PUT'])
@login_required
def permission_put():
    """Function which edits permission.
    :return: If request data is invalid:
                 {'status': False, 'error': [list of errors]}, 400
             If all ok:
                 {'status': 'success',
                  'edited_perm_id': 'permission_id'}
    """
    if request.method == 'PUT' and request.get_json():
        data = request.get_json()
        valid = validator.permission_put(data)

        if valid['status']:
            db.edit_permission(data['action'],
                               data['modifier'],
                               data['permission_id'],
                               data['description'])
            response = jsonify(status='success',
                               edited_perm_id=data['permission_id'])
            session['access_control'] = permission_control.reload_dct()
        else:
            response = Response(json.dumps(valid),
                                mimetype='application/json'), 400
        return response


@app.route("/api/permissions", methods=['DELETE'])
@login_required
def permission_delete():
    """Function which edits permission.
    :return: If permission is binded with any role:
                 {'error': 'Cannot delete!'}
             If request data is invalid:
                 {'status': False, 'error': [list of errors]}, 400
             If all ok:
                 {'status': 'success',
                  'edited_perm_id': 'permission_id'}
    """
    if request.method == 'DELETE' and request.get_json():
        data = request.get_json()
        valid = validator.permission_delete(data)

        if valid['status']:
            if not db.check_permission_deletion(data['permission_id']):
                db.delete_permission_by_id(data['permission_id'])
                response = jsonify(status='success',
                                   deleted_permission=data['permission_id'])
                session['access_control'] = permission_control.reload_dct()
            else:
                response = jsonify(error='Cannot delete!')
        else:
            response = Response(json.dumps(valid),
                                mimetype='application/json'), 400
        return response


@app.route("/api/permissions", methods=['GET'])
@login_required
def permission_get():
    """Function which gets all permissions.
    :return: {'permission_id': 'permission_id', 'action': 'action',
              'modifier': 'modifier', 'description': 'description'}
    """
    resource_id = request.args.get('resource_id')
    permission_tuple = db.get_all_permissions_by_resource(resource_id)
    parsed_json = {}
    if permission_tuple:
        for res in permission_tuple:
            parsed_json.update({'permission_id': res[0],
                                'action': res[1],
                                'modifier': res[2],
                                'description': res[3]})
    return Response(json.dumps(parsed_json), mimetype='application/json')


@app.route("/api/role_permissions", methods=['POST'])
@login_required
def role_permission_post():
    """Function which binds permission with role.
    :return: If request data is not valid:
                 {'status': False, 'error': [list of errors]}
             If all ok:
                 {'added_role_permission_for_role': 'role_id'}
    """
    data = request.get_json()
    valid = validator.role_permission_post(data)

    if valid['status']:
        db.add_role_permission(data['role_id'],
                               data['permission_id'])
        response = jsonify(added_role_permission_for_role=data['role_id'])
        session['access_control'] = permission_control.reload_dct()
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400
    return response


@app.route("/api/role_permissions", methods=['PUT'])
@login_required
def role_permission_put():
    """Function which sets list of permission to role. Before sets
       removes all permissions from role.
       :return: If request data is not invalid':
                    {'status': False, 'error': [list of errors]}
                If all ok:
                    {'msg': 'edited permission'}
    """
    data = request.get_json()
    logger.info('Role permission has been changed.')

    db.delete_permissions_by_role_id(data['role_id'])
    for perm_id in data['permission_id']:
        db.add_role_permission(data['role_id'], perm_id)
    response = jsonify(msg='edited permission')
    session['access_control'] = permission_control.reload_dct()
    return response


@app.route("/api/role_permissions", methods=['DELETE'])
@login_required
def role_permission_delete():
    """Function to delete permissions."""
    data = request.get_json()

    valid = validator.role_permission_delete(data)

    if valid['status']:
        if not db.check_role_deletion(data['role_id']):
            db.delete_role_by_id(data['role_id'])
            response = jsonify(status='success',
                               deleted_role=data['role_id'])
            session['access_control'] = permission_control.reload_dct()
        else:
            response = jsonify(error='Cannot delete!')
    else:
        response = Response(json.dumps(valid),
                            mimetype='application/json'), 400
    return response


@app.route("/api/role_permissions", methods=['GET'])
@login_required
def role_permission_get():
    """Function which gets all permissions from database and all actual
       permissions for current role.
       :return: {'actual': [list of actual permissions for role],
                 'all_permissions': [list of all permissions]}
    """
    role_id = request.args.get('role_id')
    permissions_of_role = db.get_role_permission(role_id)
    all_permissions = db.get_all_permissions()
    parsed_json = {}
    if all_permissions:
        parsed_json['all_permissions'] = []
        parsed_json['actual'] = []
        for res in all_permissions:
            parsed_json['all_permissions'].append({'resource_id': res[0],
                                                   'action': res[2],
                                                   'modifier': res[3],
                                                   'description': res[4]})

            parsed_json['actual'] = [({'permission_id': x[0], 'action': x[1],
                                       'modifier': x[2],
                                       'description': x[3]}) for x in
                                     permissions_of_role]

    return Response(json.dumps(parsed_json), mimetype='application/json')


@app.route("/api/all_permissions", methods=['GET'])
@login_required
def get_all_permissions():
    """Handler for sending all created permissions to frontend.

    :return: list of json
    """
    all_permissions = db.get_all_permissions()
    perms_list = []
    if all_permissions:
        for perm in all_permissions:
            perms_list.append({
                'permission_id': perm[0],
                'resource_name': perm[1],
                'action': perm[2],
                'modifier': perm[3],
                'description': perm[4]
            })
    return Response(json.dumps(perms_list), mimetype='application/json')


@app.route("/api/user_roles", methods=['GET', 'POST'])
@login_required
def get_all_users():
    """Function, used to get all users.
       :return: list of users with id, first name, last name, email and role
    """
    if request.method == 'POST' and request.get_json():
        data = request.get_json()

        valid = validator.user_role_put(data)

        if valid['status']:
            db.change_user_role(data['role_id'],
                                data['user_id'])
            response = jsonify(msg='success',
                               added_role=data['role_id'])
            session['access_control'] = permission_control.reload_dct()
        else:
            response = Response(json.dumps(valid),
                                mimetype='application/json'), 400
        return response
    users_tuple = db.get_all_users()
    parsed_json = []
    if users_tuple:
        for res in users_tuple:
            parsed_json.append({'user_id': res[0], 'first_name': res[1],
                                'last_name': res[2], 'email': res[3],
                                'role': res[4]})
    return Response(json.dumps(parsed_json), mimetype='application/json')


@app.route('/api/editResource/<int:page_id>', methods=['PUT'])
@login_required
def edit_page(page_id):
    """This method makes changes to given page(ex-resource).

        :returns confirmation.
    """
    if request.method == 'PUT' and request.get_json():
        data = request.get_json()
        result = False
        status_code = 404
        if db.get_page_by_id(data['id']):
            db.edit_page(page_id, data['title'], data['alias'],
                         data['description'], data['content'],
                         data['meta_keywords'], data['meta_description'],
                         data['is_enabled'])
            result = True
            status_code = 200
        return jsonify(result=result), status_code


@app.route('/api/addResource', methods=['POST'])
@login_required
def add_page():
    """This method adds new page to db."""
    result = None
    msg = None
    if request.method == 'POST' and request.get_json():
        data = request.get_json()
        if not db.get_page_by_alias(data['alias']):
            db.add_page(data['title'], data['alias'],
                        data['description'], data['content'],
                        data['meta_keywords'], data['meta_description'],
                        data['is_enabled'])
            if db.get_page_by_alias(data['alias']):
                result = True
                msg = 'Succesfully added!'
            else:
                result = False
                msg = "Couldn't add new page!"
        else:
            result = False
            msg = 'Page already exists!'
    return jsonify(result=result, msg=msg)


@app.route('/api/deleteResource/<page_id>', methods=['DELETE'])
@login_required
def delete_page(page_id):
    """This method deletes page by it's id."""
    msg = None
    result = None
    if request.method == 'DELETE':
        db.delete_page_by_id(page_id)
        if not db.get_page_by_id(page_id):
            result = True
            msg = 'Page was deleted successfully!'
        else:
            result = False
            msg = "Couldn't delete the page!"
    return jsonify(result=result, msg=msg)


@app.route("/api/user_page", methods=['GET'])
def pagination():
    """Returns a limit of users."""
    offset = request.args.get('offset')
    per_page = request.args.get('per_page')

    query = db.get_users_pagination(offset, per_page)
    count = db.count_users()
    parsed_json = []
    if query:
        for user_data in query:
            parsed_json.append({'id': user_data[0], 'first_name': user_data[1],
                                'last_name': user_data[2],
                                'email': user_data[3],
                                'role_name': user_data[4]})
    if count:
        parsed_json.append({'total_users': count[0]})

    return Response(json.dumps(parsed_json), mimetype='application/json')
