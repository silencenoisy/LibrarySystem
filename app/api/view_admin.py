import os
import re
import uuid
from datetime import datetime

from flask_httpauth import HTTPTokenAuth
from itsdangerous import Serializer

from app.api.view_func import *
from . import api

from flask import request, g
from app import db
from app.models import User, Admin, Return, Book, Admin, Book_Tag, Borrow, User_Medal, Comment, Tag, User_log, Admin_log
from app.config import Config

auth2 = HTTPTokenAuth(scheme='JWT')





@api.route('/admin/testing', methods=['GET', 'POST'])
@auth2.login_required
def admin_testing():
    date = User.query.all()
    ret = [i.__repr__() for i in date]
    ret.append(g.admin.username)
    return make_json(ret)


@api.route('/admin/login', methods=['POST'])
def admin_login():
    '''
    接受参数并校验参数，返回token
    :return:
    '''
    form = request.get_json()
    username = form.get('username')
    password = form.get('password')
    if username is None or password is None:
        return make_json({}, code=ErrorCode.INVALID_KEY, msg='缺少参数'), ErrorCode.INVALID_KEY
    guest = Admin.query.filter_by(username=username).first()
    # 生成token
    if not guest:
        return make_json({},code=ErrorCode.LOGIN_FAIL,msg="username not exist"),ErrorCode.LOGIN_FAIL
    if guest.check_pwd(password):
        z_token = Admin.create_token(guest.id)
        date = {"token": z_token, "id": guest.id, "power": guest.power}
        add_admin_log(guest.username, ManageOrder.ADMIN_LOGIN_OP)
        db.session.commit()
        return make_json(date)

    else:
        return make_json({},code=ErrorCode.LOGIN_FAIL, msg='error password'), ErrorCode.LOGIN_FAIL


@api.route('/admin/<int:id>/logout', methods=['GET'])
@auth2.login_required
def login_out(id):
    add_admin_log(g.admin.username, ManageOrder.ADMIN_LOGOUT_OP)
    db.session.commit()
    return make_json({})


@auth2.verify_token
def verify_token(token):
    # Config.SECRET_KEY:内部的私钥，这里写在配置信息里
    s = Serializer(Config.SECRET_KEY_ADMIN)

    admin = Admin.verify_auth_token(token)
    if not admin:
        return False
    # 校验通过返回True
    g.admin = admin
    return True


@auth2.error_handler
def error_handler_401():
    return make_json({},code=401, msg="invalid token")


@api.route('/book/rank', methods=['GET', 'POST'])
def book_rank():
    if request.method == "GET":
        data = request.args
    else:
        data = request.get_json()
    data, is_checked = check_book_rank(data)
    if not is_checked:
        return data, ErrorCode.INVALID_KEY
    ret = borrow_rank(data)

    return make_json(ret)


@api.route('/book/<ISBN>', methods=['POST'])
@auth2.login_required
def modify_book(ISBN):
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.LOGIN_FAIL

    book = Book.query.filter_by(isbn=ISBN).first()
    if book is None:
        return make_json({},code=ErrorCode.NOT_FOUND, msg='book not find'), ErrorCode.NOT_FOUND
    try:
        cover_image = request.files['cover_image']
    except KeyError:
        cover_image = None
    form = request.get_json()
    data, is_checked = check_change_book_data(form if form is not None else dict(),cover_image)

    if not is_checked:
        return data, ErrorCode.INVALID_KEY

    change_book_data(book, data,cover_image)
    add_admin_log(g.admin.username, ManageOrder.ADMIN_MODIFY_BOOK_OP,ISBN)
    db.session.commit()
    return make_json({})


@api.route('/book/addition', methods=['POST'])
@auth2.login_required
def add_book():
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.LOGIN_FAIL
    isbn = request.get_json().get("isbn")
    if isbn is None or not check_isbn_format(isbn):
        return make_json({}, ErrorCode.INVALID_KEY, "isbn号格式错误"), ErrorCode.INVALID_KEY

    book = Book.query.filter_by(isbn=isbn).first()
    if book is not None:
        return make_json({},code=ErrorCode.INVALID_KEY,
                         msg='book has existed'), ErrorCode.INVALID_KEY
    data = request.get_json()
    try:
        cover_image = request.files['cover_image']
    except KeyError:
        cover_image = None
    data, is_checked = check_add_book_data(data,cover_image)
    if not is_checked:
        return data, ErrorCode.INVALID_KEY

    if not add_one_book(isbn, data,cover_image):
        return make_json({}, ErrorCode.SQL_ERROR, "标签添加失败")
    add_admin_log(g.admin.username, ManageOrder.ADMIN_ADD_BOOK_OP,isbn)
    db.session.commit()
    return make_json({})


@api.route('/book/<ISBN>/delete', methods=['GET'])
@auth2.login_required
def delete_book(ISBN):
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.ADMIN_NULL_POWER

    book = Book.query.filter_by(isbn=ISBN).first()
    if book is None:
        return make_json({},code=ErrorCode.NOT_FOUND, msg='book not find'), ErrorCode.NOT_FOUND

    tag_now_list = Book_Tag.query.filter_by(bid=book.id).all()

    for tag in tag_now_list:
        db.session.delete(tag)

    borrow_record = Borrow.query.filter_by(bid=book.id).first()
    if borrow_record is not None:
        db.session.delete(borrow_record)

    return_record = Return.query.filter_by(bid=book.id).first()
    if return_record is not None:
        db.session.delete(return_record)

    add_admin_log(g.admin.username, ManageOrder.ADMIN_DELETE_BOOK_OP, book.isbn)
    db.session.delete(book)
    db.session.commit()

    return make_json({})


@api.route('/admin/user/<int:id>/change', methods=['POST'])
@auth2.login_required
def modify_user(id):
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.ADMIN_NULL_POWER
    try:
        user_face = request.files['face']
    except KeyError:
        user_face = None
    changed_data, is_checked = check_modify_user_data(request.get_json(),user_face)
    if is_checked:  # 验证注册参数规范性
        try:
            change_user_to_db(id, changed_data,user_face)  # 修改信息写入数据库
            user = User.query.get(id)
            add_admin_log(g.admin.username, ManageOrder.ADMIN_MODIFY_USER_OP,user.sid if user is not None else "")
            db.session.commit()
        except ValueError as e:
            print("Error:", e.args)
            db.session.rollback()
            return make_json({}, ErrorCode.INVALID_KEY, "修改参数存在错误"), ErrorCode.INVALID_KEY
        return make_json({}, 0, "OK")  # 注册成功

    else:
        return changed_data, ErrorCode.INVALID_KEY

    return make_json({})


@api.route('/admin/user', methods=['POST'])
@auth2.login_required
def query_user():
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.ADMIN_NULL_POWER

    data = request.get_json()
    format_data, is_check = check_query_user_data(data)
    if not is_check:
        return format_data, ErrorCode.INVALID_KEY

    search_data = search_users(format_data)
    ret = {"page": format_data['page'], "per_page": format_data['per_page']}
    users = []
    print(print(search_data))
    try:
        datass = search_data.items
    except:
        datass = search_data

    for user in datass:
        user_temp = {
            "id": user.id,
            "sid": user.sid,
            "face": user.face if user.face is not None else Config.DEFAULT_USER_FACE_GET,
            "institute": user.institute if user.institute is not None else "",
            "username": user.username,
            "realname": user.realname,
            "sex": user.sex,
            "birthday": user.birthday if user.birthday is not None else "",
            "email": user.email if user.email is not None else "",
            "phone": user.phone if user.phone is not None else "",
            "left_borrow": user.left_borrow,
            "total_borrowed": user.total_borrowed,
            "overtime_borrowed": user.overtime_borrowed,
        }
        users.append(user_temp)
    ret['users'] = users
    return make_json(ret)


@api.route('/admin/user/<int:id>/delete', methods=['GET'])
@auth2.login_required
def delete_user(id):
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.ADMIN_NULL_POWER

    user = User.query.get(id)
    if user is None:
        return make_json({},code=ErrorCode.NOT_FOUND, msg='user not find'), ErrorCode.NOT_FOUND

    user_medal_list = User_Medal.query.filter_by(uid=id).all()
    for user_medal in user_medal_list:
        db.session.delete(user_medal)
    db.session.commit()

    borrows = Borrow.query.filter_by(uid=id).all()
    return_records = Return.query.filter_by(uid=id).all()
    for borrow in borrows:
        db.session.delete(borrow)
    for return_record in return_records:
        db.session.delete(return_record)
    add_admin_log(g.admin.username, ManageOrder.ADMIN_DELETE_USER_OP,user.sid )
    db.session.delete(user)

    db.session.commit()
    return make_json({})


@api.route('/admin/user/addition', methods=['POST'])
@auth2.login_required
def admin_add_user():
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.LOGIN_FAIL

    user_data, is_checked = check_add_user_data(request.get_json())
    if is_checked:  # 验证注册参数规范性
        if has_user_sid(user_data.get("sid")):  # 学号是否存在判断
            return make_json({}, ErrorCode.REGISTER_FAIL_EXIST_SID, "学号已存在"), ErrorCode.INVALID_KEY
        try:
            add_user_to_db(user_data)  # 信息写入数据库
            add_admin_log(g.admin.username, ManageOrder.ADMIN_ADD_USER_OP,user_data.get("sid"))
            db.session.commit()
        except ValueError as e:
            print("Error:", e.args)
            return make_json({}, ErrorCode.INVALID_KEY, "注册参数存在错误"), ErrorCode.INVALID_KEY
        return make_json({}, 0, "OK")  # 注册成功

    return user_data, ErrorCode.INVALID_KEY


@api.route('/admin/comment/<int:id>/delete', methods=['GET'])
@auth2.login_required
def admin_delete_comment(id):
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.ADMIN_NULL_POWER

    com = Comment.query.get(id)
    add_admin_log(g.admin.username, ManageOrder.ADMIN_DELETE_COMMENT_OP, com.comment)
    db.session.delete(com)
    db.session.commit()
    return make_json({})


@api.route('/comment/<int:id>/change', methods=['POST'])
@auth2.login_required
def modify_comment(id):
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.ADMIN_NULL_POWER

    com = Comment.query.get(id)
    if com is None:
        return make_json({},code=ErrorCode.NOT_FOUND, msg='comment not find'), ErrorCode.NOT_FOUND
    new_comment = request.get_json().get("comment")
    if new_comment is None or not check_comment_format(new_comment):
        return make_json({})
    com.comment = new_comment
    db.session.commit()
    add_admin_log(g.admin.username, ManageOrder.ADMIN_MODIFY_COMMENT_OP,com.comment)
    db.session.commit()
    return make_json({})


@api.route('/admin/tag/<int:id>', methods=['POST'])
@auth2.login_required
def tag_change(id):
    tag = Tag.query.get(id)
    if tag is None:
        return make_json({}, ErrorCode.NOT_FOUND, "标签不存在"), ErrorCode.NOT_FOUND

    name = request.get_json().get("name")
    if Tag.query.filter(Tag.name == name).first():
        return make_json({}, ErrorCode.INVALID_KEY, "标签名已存在"), ErrorCode.INVALID_KEY

    tag.name = name
    db.session.commit()
    add_admin_log(g.admin.username, ManageOrder.ADMIN_MODIFY_TAG_OP,tag.name)
    db.session.commit()
    return make_json({})


@api.route('/tag/addition', methods=['POST'])
@auth2.login_required
def tag_addition():
    name = request.get_json().get("name")
    if Tag.query.filter(Tag.name == name).first():
        return make_json({}, ErrorCode.INVALID_KEY, "标签名已存在"), ErrorCode.INVALID_KEY
    if name is None or not check_tag_format(name):
        return make_json({}, ErrorCode.INVALID_KEY, "标签格式错误"), ErrorCode.INVALID_KEY
    tag = Tag(name=name)
    db.session.add(tag)
    db.session.commit()
    add_admin_log(g.admin.username, ManageOrder.ADMIN_ADD_TAG_OP,tag.name)
    db.session.commit()
    return make_json({})


@api.route('/tag/<int:id>/delete', methods=['GET'])
@auth2.login_required
def tag_delete(id):
    tag = Tag.query.get(id)
    if tag is None:
        return make_json({}, ErrorCode.NOT_FOUND, "标签不存在"), ErrorCode.NOT_FOUND

    book_tag_list = Book_Tag.query.filter(Book_Tag.tid == tag.id).all()
    for item in book_tag_list:
        db.session.delete(item)
    add_admin_log(g.admin.username, ManageOrder.ADMIN_DELETE_TAG_OP, tag.name)
    db.session.delete(tag)
    db.session.commit()
    return make_json({})


@api.route('/log/user', methods=['GET', "POST"])
@auth2.login_required
def query_user_log():
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.ADMIN_NULL_POWER

    if request.method == 'GET':
        data = request.args
    else:
        data = request.get_json()

    format_data, is_check = check_user_log_data(data)

    if not is_check:
        return format_data, ErrorCode.INVALID_KEY

    search_data = search_user_log(format_data)
    ret = {"page": format_data['page'], "per_page": format_data['per_page']}
    user_logs = []
    for user_log in search_data.items:
        user_log_temp = user_log_detail(user_log)
        user_logs.append(user_log_temp)
    ret['user_logs'] = user_logs
    return make_json(ret)


@api.route('/log/admin', methods=['GET', "POST"])
@auth2.login_required
def query_admin_log():
    if g.admin.power == 0:
        return make_json({},code=ErrorCode.ADMIN_NULL_POWER, msg='admin no enough power'), ErrorCode.ADMIN_NULL_POWER

    if request.method == 'GET':
        data = request.args
    else:
        data = request.get_json()

    format_data, is_check = check_admin_log_data(data)

    if not is_check:
        return format_data, ErrorCode.INVALID_KEY

    search_data = search_admin_log(format_data)
    ret = {"page": format_data['page'], "per_page": format_data['per_page']}
    admin_logs = []
    for admin_log in search_data.items:
        admin_log_temp = admin_log_detail(admin_log)
        admin_logs.append(admin_log_temp)
    ret['admin_logs'] = admin_logs
    return make_json(ret)
