"""
This module holds all views controls for
ecomap project.
"""
# import sys

from flask import render_template, request, jsonify
from flask_login import login_user, logout_user

import ecomap.db.user as usr

from ecomap.app import app


@app.route("/")
def index():
    return render_template("base.html")


@app.route("/api/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        user = usr.User.get(username=data['email'])
        if user and user.verify_password(data['password']):
            login_user(user, force=True)
            return jsonify(id=user.userid, name=user.first_name,
                           surname=user.last_name, role='???', iat="???",
                           token=user.get_auth_token(), email=user.email)
    return jsonify(error="Couldn't login with your credenntials!!!", logined=0)


@app.route("/api/logout", methods=["GET", "POST"])
def logout():
    result = logout_user()
    return jsonify(result=result)


@app.route("/api/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if not usr.User.get(data['email']):
            usr.User.register(data['firstName'], data['lastName'],
                              data['email'], data['password'])
            status = 'added %s %s' % (data['firstName'], data['lastName'])
        else:
            status = 'user with this email already exists'
        return jsonify({'status': status})

if __name__ == "__main__":
    app.run()
    # usr.login_manager.init_app(app)

    # user = usr.User.get(username="admin")
    # print user
    # login_user(user, remember=True)
