import os
import re
import uuid
from datetime import datetime

from flask_httpauth import HTTPTokenAuth
from itsdangerous import Serializer
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename

from app.ErrorCode import ErrorCode
from app.Code import ManageOrder
from . import api
from .view_func import *

from flask import jsonify, request, g
from app import db
from app.models import User, Medal, User_Medal, Book, Return, Borrow, Comment, Book_Tag, Tag, User_log
from app.config import Config

auth = HTTPTokenAuth(scheme='JWT')





@api.route('/testing', methods=['GET', 'POST'])
@auth.login_required
def testing():
    date = User.query.all()
    ret = [i.__repr__() for i in date]
    ret.append(g.user.sid)
    return make_json(ret)


@auth.verify_token
def verify_token(token):
    # Config.SECRET_KEY:内部的私钥，这里写在配置信息里
    s = Serializer(Config.SECRET_KEY)

    user = User.verify_auth_token(token)
    if not user:
        return False
    # 校验通过返回True
    g.user = user
    return True


@auth.error_handler
def error_handler_401():
    return make_json(date={}, code=401, msg="invalid token")


# @csrf.exempt
@api.route('/user/login', methods=['POST'])
def login():
    '''
    接受参数并校验参数，返回token
    :return:
    '''
    form = request.get_json()
    sid = form.get('sid')
    password = form.get('password')
    if sid is None or password is None:
        return make_json({}, code=ErrorCode.INVALID_KEY, msg='缺少参数')
    guest = User.query.filter_by(sid=sid).first()
    # 生成token
    if guest is None:
        return make_json({}, code=ErrorCode.LOGIN_FAIL, msg='error sid')
    elif guest.check_pwd(password):
        z_token = User.create_token(guest.id)
        date = {"token": z_token, "id": guest.id}
        add_user_log(guest.sid, ManageOrder.USER_LOGIN_OP)
        return make_json(date)
    else:
        return make_json({}, code=ErrorCode.LOGIN_FAIL, msg='error password')


@api.route('/user/register', methods=['POST'])
def register():
    register_date, is_checked = check_register_date(request.get_json())
    if is_checked:  # 验证注册参数规范性
        if has_user_sid(register_date.get("sid")):  # 学号是否存在判断
            return make_json({}, ErrorCode.REGISTER_FAIL_EXIST_SID, "学号已存在")
        try:
            add_user_to_db(register_date)  # 信息写入数据库
        except ValueError as e:
            print("Error:", e.args)
            return make_json({}, ErrorCode.INVALID_KEY, "注册参数存在错误")
        return make_json({}, 0, "OK")  # 注册成功

    else:
        return register_date, ErrorCode.INVALID_KEY


@api.route("/user/<int:id>", methods=['GET', 'POST'])
@auth.login_required
def user_date_get(id):
    if request.method == 'GET':
        if id != g.user.id:
            return make_json({}, 30001, "无法查询其他用户信息"), 401
        user_date = User.query.filter_by(id=id).first()
        if user_date is not None:
            ret = {"id": user_date.id,
                   "sid": user_date.sid,
                   "face": user_date.face if user_date.face is not None else Config.DEFAULT_USER_FACE_GET,
                   "institute": user_date.institute if user_date.institute is not None else "",
                   "username": user_date.username,
                   "realname": user_date.realname,
                   "sex": "保密" if user_date.sex == 0 else (
                       "男" if user_date.sex == 1 else "女" if user_date.sex == 2 else "未知"),
                   "birthday": user_date.birthday if user_date.birthday is not None else "",
                   "email": user_date.email if user_date.email is not None else "",
                   "phone": user_date.phone if user_date.phone is not None else "",
                   "left_borrow": user_date.left_borrow,
                   "total_borrowed": user_date.total_borrowed,
                   "overtime_borrowed": user_date.overtime_borrowed, }

        else:
            return make_json({}, 404, "用户不存在"), 404

        return make_json(ret)

    else:
        if id != g.user.id:
            return make_json({}, 30001, "无法查询其他用户信息"), 401
        try:
            face = request.files['face']
        except KeyError:
            face = None
        form = request.get_json()

        changed_date, is_checked = check_changed_date(form if form is not None else dict(), face)
        if is_checked:  # 验证注册参数规范性
            try:
                user_change_user_to_db(id,changed_date,face)  # 修改信息写入数据库

            except ValueError as e:
                print("Error:", e.args)
                db.session.rollback()
                return make_json({}, ErrorCode.INVALID_KEY, "修改参数存在错误"), ErrorCode.INVALID_KEY
            return make_json({}, 0, "OK")  # 注册成功

        else:
            return changed_date, ErrorCode.INVALID_KEY

        return make_json({})


@api.route("/user/<int:id>/medal", methods=['GET'])
@auth.login_required
def show_medal(id: int):
    if id != g.user.id:
        return make_json({}, 30001, "无法查询其他用户信息"), 401

    medal_id = User_Medal.query.filter(User_Medal.uid == id).all()
    ret = {"id": id, "count": len(medal_id)}
    medal_list = []
    for medal_link in medal_id:
        medal = Medal.query.filter_by(id=medal_link.mid).first()
        temp_medal = {"medal_id": medal_link.mid, "medal_name": medal.name}
        medal_list.append(temp_medal)
    ret["medal_lsit"] = medal_list
    return make_json(ret)


@api.route("/user/<int:id>/account/password", methods=['POST'])
@auth.login_required
def change_pwd(id: int):
    if id != g.user.id:
        return make_json({}, 30001, "无法查询其他用户信息"), 401
    form = request.get_json()
    old_pwd = form.get("oldpassword")
    new_pwd = form.get("password")
    if not check_pwd_format(old_pwd) or not check_pwd_format(new_pwd):
        return make_json({}, ErrorCode.INVALID_KEY, "密码格式存在错误")

    user = User.query.filter_by(id=id).first()
    if not user.check_pwd(old_pwd):
        return make_json({}, ErrorCode.PASSWORD_WRONG, "密码错误")

    user.password = User.create_hash_pwd(new_pwd)
    db.session.commit()
    add_user_log(g.user.sid, ManageOrder.CHANGE_PWD)
    return make_json({})


@api.route("/user/<int:id>/logout", methods=['GET'])
@auth.login_required
def logout(id):
    add_user_log(g.user.sid, ManageOrder.LOGOUT)
    return make_json({})


@api.route("/book/<isbn>", methods=['GET'])
def get_book_isbn(isbn):
    if check_isbn_format(isbn):
        book = Book.query.filter_by(isbn=isbn).first()
        if book is not None:
            return make_json(get_book_data_detail(book))
    return make_json({}, ErrorCode.NOT_FOUND, "未查询到书籍记录"), ErrorCode.NOT_FOUND


@api.route("/book", methods=['GET', 'POST'])
def book_search():
    if request.method == 'GET':
        data = request.args
    else:
        data = request.get_json()

    format_data, is_check = check_book_date(data)
    if not is_check:
        return format_data, ErrorCode.INVALID_KEY

    search_data = search_books(format_data)
    ret = {"page": format_data['page'], "per_page": format_data['per_page']}
    books = []
    for book in search_data.items:
        book_temp = get_book_data_detail(book)
        books.append(book_temp)

    ret['books'] = books
    return make_json(ret)


@api.route("/user/<int:id>/book/<isbn>/return", methods=['GET'])
@auth.login_required
def return_book(id: int, isbn):
    if id != g.user.id:
        return make_json({}, 30001, "无法查询其他用户信息"), 401
    if return_book_with_id_and_isbn(id, isbn):
        add_user_log(g.user.sid, ManageOrder.RETURN_BOOK, isbn)
        medal_two_check(id)
        return make_json({})
    return make_json({}, ErrorCode.NOT_FOUND, "未查询到借书记录"), ErrorCode.NOT_FOUND


@api.route("/user/<int:id>/book/<isbn>/borrow", methods=['GET'])
@auth.login_required
def borrow_book(id: int, isbn):
    if id != g.user.id:
        return make_json({}, 30001, "无法查询其他用户信息"), 401
    stat,return_time = borrow_book_with_id_and_isbn(id, isbn)
    if stat == 0:
        add_user_log(g.user.sid, ManageOrder.BORROW_BOOK, isbn)
        return_time = datetime.strftime(return_time, "%Y-%m-%d %H:%M:%S")
        return make_json({"return_time":return_time})
    elif stat == 404:
        return make_json({}, ErrorCode.NOT_FOUND, "未查询到书籍记录"), ErrorCode.NOT_FOUND
    elif stat == 401:
        return make_json({}, ErrorCode.NOT_FOUND, "书已被借出"), ErrorCode.NOT_FOUND
    elif stat == 400:
        return make_json({}, ErrorCode.INVALID_KEY, "ISBN号格式错误"), ErrorCode.INVALID_KEY
    return make_json({}, 500, "未知错误"), 500


@api.route("/user/<int:id>/comment", methods=['POST'])
@auth.login_required
def comment_book(id: int):
    if id != g.user.id:
        return make_json({}, 30001, "无法查询其他用户信息"), 401
    form = request.get_json()
    isbn = form.get('isbn')
    comment = form.get('comment')
    stat = comment_in_book(id, isbn, comment)
    if stat == 0:
        add_user_log(g.user.sid, ManageOrder.ADD_COMMENT, isbn)
        return make_json({})
    elif stat == 404:
        return make_json({}, ErrorCode.NOT_FOUND, "未查询到书籍记录"), ErrorCode.NOT_FOUND
    elif stat == 401:
        return make_json({}, ErrorCode.INVALID_KEY, "评论内容参数错误"), ErrorCode.INVALID_KEY
    return make_json({}, 500, "未知错误"), 500


@api.route("/user/<int:id>/comment/<int:comment_id>/delete", methods=['GET'])
@auth.login_required
def delete_comment(id: int, comment_id: int):
    if id != g.user.id:
        return make_json({}, 30001, "无法查询其他用户信息"), 401
    stat, isbn = delete_comment_by_id(comment_id)
    if stat is True:
        add_user_log(g.user.sid, ManageOrder.DELETE_COMMENT, isbn)
        return make_json({})
    else:
        return make_json({}, ErrorCode.NOT_FOUND, "未查询到评论记录"), ErrorCode.NOT_FOUND


@api.route("/comment/<int:comment_id>", methods=['GET'])
@auth.login_required
def get_comment_id(comment_id: int):
    comment = Comment.query.get(comment_id)
    if comment is None:
        return make_json({}, ErrorCode.NOT_FOUND, "未查询到评论记录"), ErrorCode.NOT_FOUND
    else:

        return make_json(get_comment_id_detail(comment))


@api.route("/comments", methods=['GET', 'POST'])
def get_comments():
    if request.method == "GET":
        data = request.args
    else:
        data = request.get_json()

    format_data, is_check = check_comment_search_date(data)
    if not is_check:
        return format_data, ErrorCode.INVALID_KEY
    else:
        search_data = search_comments(format_data)
        ret = {"page": format_data['page'], "per_page": format_data['per_page']}
        comments = []
        for comment in search_data.items:
            comment_temp = get_comment_id_detail(comment)
            comments.append(comment_temp)

        ret['comments'] = comments
    return make_json(ret)


@api.route("/user/<int:id>/book", methods=['GET', 'POST'])
@auth.login_required
def record_search(id: int):
    # if id != g.user.id:
    #     return make_json({}, 30001, "无法查询其他用户信息"), 401
    if request.method == 'GET':
        data = request.args
    else:
        data = request.get_json()

    format_data, is_check = check_record_date(data)
    if not is_check:
        return format_data, ErrorCode.INVALID_KEY
    else:
        user_record = user_record_by_id(id, format_data['isreturned'], format_data['page'], format_data['per_page'])
        search_data = search_record(format_data, user_record)
        ret = {"page": format_data['page'], "per_page": format_data['per_page']}

        ret['books'] = search_data
    return make_json(ret)


@api.route("/user/<int:id>/recommend", methods=['GET'])
def recommend_book(id: int):
    page = request.args.get("page",1,int)
    per_page = request.args.get("per_page",10,int)
    books = recommend_book_to_user(id,page,per_page)
    ret = []
    for book in books:
        temp_book = get_book_data_detail(book)
        ret.append(temp_book)
    return make_json(ret)


@api.route("/tag/<int:id>", methods=['GET'])
# @auth.login_required
def tag_get_id(id: int):
    tag = Tag.query.get(id)
    if tag is not None:
        ret = get_tag_detail(tag)
        return make_json(ret)
    else:
        return make_json({}, ErrorCode.NOT_FOUND, "标签不存在"), ErrorCode.NOT_FOUND


@api.route("/tag", methods=['GET'])
# @auth.login_required
def tags_get():
    tags = Tag.query.all()
    ret = []
    for tag in tags:
        ret.append(get_tag_detail(tag))
    return make_json(ret)
