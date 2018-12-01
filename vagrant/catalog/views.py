import json
import os
import random
import string

import httplib2
import requests
from flask import (Flask, abort, flash, g, jsonify, make_response,
                   render_template, request)
from flask import session as login_session
from flask import url_for
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import FlowExchangeError, flow_from_clientsecrets
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, joinedload

from databasemodels import Base, Category, Item, User


CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

auth = HTTPBasicAuth()

g_app = Flask(__name__)
g_app.secret_key = os.urandom(24)

# Connect to Database and create database session
g_engine = create_engine('sqlite:///itemcatalog.db',
                         connect_args={'check_same_thread': False})
Base.metadata.bind = g_engine

DBSession = sessionmaker(bind=g_engine)
g_session = DBSession()

global g_authenticated
g_authenticated = False

g_categories = g_session.query(Category).all()


@auth.verify_password
def verify_password(username_or_token, password):
    if 'username' not in login_session:
        return False
    else:
        return True


def refreshState():
    global login_session
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state


@g_app.route('/', methods=['GET'])
def home():
    items = g_session.query(Item).order_by(Item.lastupdated.desc()).all()
    global g_authenticated
    if 'username' not in login_session:
        g_authenticated = False
    else:
        g_authenticated = True

    refreshState()
    return render_template('index.html',
                           STATE=login_session['state'],
                           categories=g_categories,
                           items=items,
                           authenticated=g_authenticated,
                           itemsHeading="Latest Items")


@g_app.route('/oauth/google', methods=['POST'])
def gconnect():
    # global login_session
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Unauthorized!!!'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    oauth_code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(oauth_code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade auth code'), 401)
        response.headers['Content-type'] = 'application/json'

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    http_obj = httplib2.Http()
    result = json.loads(http_obj.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user = g_session.query(User).filter_by(
        email=login_session['email']).first()
    if not user:
        user = User(username=login_session['username'],
                    picture=login_session['picture'],
                    email=login_session['email'])
    g_session.add(user)
    g_session.commit()
    g_session.refresh(user)

    login_session['user_id'] = user.id

    global g_authenticated
    g_authenticated = True

    return json.dumps({'name': login_session['username']})


@g_app.route('/gdisconnect')
def gdisconnect():
    # global login_session
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(
        login_session['access_token'])

    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['google_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        global g_authenticated
        g_authenticated = False
        return json.dumps({'message': 'Successfully logged out'})
    else:
        return json.dumps({'message': 'Could not log out successfully'})


@g_app.route('/item/new/', methods=['GET', 'POST'])
@auth.login_required
def newCategoryItem():
    if request.method == 'POST':
        if request.form['state'] != login_session['state']:
            response = make_response(json.dumps('Unauthorized!!!'), 401)
            response.headers['Content-type'] = 'application/json'
            return response

        newItem = Item(title=request.form['name'],
                       desc=request.form['desc'],
                       cat_id=request.form['category'],
                       user_id=login_session['user_id'])
        g_session.add(newItem)
        g_session.commit()
        result = "Item added successfully"
        return render_template('additem.html',
                               categories=g_categories,
                               result=result,
                               authenticated=g_authenticated)
    else:
        refreshState()
        return render_template('additem.html',
                               STATE=login_session['state'],
                               categories=g_categories,
                               authenticated=g_authenticated)


@g_app.route('/catalog/<cat_name>/items', methods=['GET'])
def getAllCategoryItems(cat_name):
    category = list(cat for cat in g_categories if cat.name == cat_name)
    items = g_session.query(Item).filter_by(cat_id=category[0].id)

    refreshState()
    return render_template('index.html',
                           STATE=login_session['state'],
                           categories=g_categories,
                           items=items,
                           authenticated=g_authenticated,
                           itemsHeading=cat_name + " Items")


@g_app.route('/catalog/<cat_name>/<item_title>', methods=['GET'])
def getItemDesc(cat_name, item_title):
    item = g_session.query(Item).filter_by(title=item_title)
    refreshState()

    isCreator = False
    if g_authenticated is True:
        if login_session['user_id'] == item[0].user_id:
            isCreator = True

    return render_template('item_page.html',
                           STATE=login_session['state'],
                           item_title=item_title,
                           desc=item[0].desc,
                           authenticated=g_authenticated,
                           isCreator=isCreator)


@g_app.route('/catalog/<item_title>/edit', methods=['GET', 'POST'])
@auth.login_required
def editItem(item_title):
    if request.method == 'POST':
        if request.form['state'] != login_session['state']:
            response = make_response(json.dumps('Unauthorized!!!'), 401)
            response.headers['Content-type'] = 'application/json'
            return response

        item = g_session.query(Item).filter_by(id=request.form['currentId'])

        if item[0].user_id != login_session['user_id']:
            response = make_response(json.dumps('Unauthorized!!!'), 401)
            response.headers['Content-type'] = 'application/json'
            return response

        item[0].title = request.form['name']
        item[0].desc = request.form['desc']
        g_session.commit()
        result = "Item modified successfully"

        return render_template('item_page.html',
                               result=result,
                               STATE=login_session['state'],
                               item_title=item[0].title,
                               desc=item[0].desc,
                               authenticated=g_authenticated)
    else:
        refreshState()
        item = g_session.query(Item).filter_by(title=item_title)

        if item[0].user_id != login_session['user_id']:
            response = make_response(json.dumps('Unauthorized!!!'), 401)
            response.headers['Content-type'] = 'application/json'
            return response

        return render_template('edititem.html',
                               currentTitle=item_title,
                               currentId=item[0].id,
                               STATE=login_session['state'],
                               desc=item[0].desc,
                               categories=g_categories,
                               authenticated=g_authenticated)


@g_app.route('/catalog/<item_title>/delete', methods=['GET', 'POST'])
@auth.login_required
def deleteItem(item_title):
    if request.method == 'POST':
        pageData = json.loads(request.data)
        if pageData["state"] != login_session['state']:
            response = make_response(json.dumps('Unauthorized!!!'), 401)
            response.headers['Content-type'] = 'application/json'
            return response

        item = g_session.query(Item).filter_by(id=pageData["id"])

        if item[0].user_id != login_session['user_id']:
            response = make_response(json.dumps('Unauthorized!!!'), 401)
            response.headers['Content-type'] = 'application/json'
            return response

        g_session.delete(item[0])
        g_session.commit()

        return json.dumps({'message': 'Item deleted successfully'})
    else:
        refreshState()
        item = g_session.query(Item).filter_by(title=item_title)

        if item[0].user_id != login_session['user_id']:
            response = make_response(json.dumps('Unauthorized!!!'), 401)
            response.headers['Content-type'] = 'application/json'
            return response

        return render_template('deleteitem.html',
                               item_title=item_title,
                               itemId=item[0].id,
                               STATE=login_session['state'],
                               desc=item[0].desc,
                               categories=g_categories,
                               authenticated=g_authenticated)


@g_app.route('/catalog.json')
def getCatalog():
    categories = DBSession().query(Category).options(
                                joinedload(Category.items)).all()
    return jsonify(dict(
                    Category=[dict(
                            category.serialize,
                            Items=[i.serialize for i in category.items])
                            for category in categories]))


if __name__ == '__main__':
    g_app.debug = True
    g_app.run(host='0.0.0.0', port=5000)
