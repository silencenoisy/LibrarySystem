import os
import re
import uuid
from datetime import datetime

from sqlalchemy import or_, func
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename

from app.ErrorCode import ErrorCode
from app.Code import ManageOrder

from flask import jsonify
from app import db, train_data_matrix, re_users, re_items,items_kv,dataset
from app.models import User, Book, Return, Borrow, Comment, Book_Tag, Tag, User_log, Admin_log, User_Medal
from app.config import Config

import pandas as pd
import numpy as np
import random
from math import *


def is_int_number(date):
    try:
        int(date)
        return True
    except ValueError:
        pass
    return False


def len_is_between(date, min, max):
    if len(date) < min or len(date) > max:
        return False
    return True


def is_date_format(addtime):
    try:
        datetime.strptime(addtime, "%Y-%m-%d")
        return True
    except TypeError:
        pass
    except ValueError:
        pass
    return False


def is_datetime_format(addtime):
    try:
        datetime.strptime(addtime, "%Y-%m-%d %H:%M:%S")
        return True
    except TypeError:
        pass
    return False


def allow_pic(filename):
    if '.' in filename:
        if filename.rsplit('.', 1)[1] in Config.ALLOWED_EXTENSIONS:
            return True
    return False


def make_json(date, code: int = 0, msg="OK"):
    return jsonify({"code": code, "msg": msg, "data": date})


def check_sid_format(sid):
    if len(sid) != 9:
        return False
    if not is_int_number(sid):
        return False
    return True


def check_pwd_format(pwd):
    return len_is_between(pwd, 6, 20)


def check_username_format(username):
    return len_is_between(username, 1, 20)


def check_realname_format(realname):
    return len_is_between(realname, 1, 20)


def check_institute_format(institute):
    if institute is not None:
        if not len_is_between(institute, 1, 25):
            return False
    return True


def check_sex_format(sex):
    if sex < 0 or sex > 2:
        return False
    return True


def check_birthday_format(birthday):
    if birthday is None or is_date_format(birthday):
        return True
    return False


def check_email_format(email):
    p = re.compile(r"[^@]+@[^@]+\.[^@]+")
    if email is None or p.match(email):
        return True
    return False


def check_phone_format(phone):
    p = re.compile(r'^(13(7|8|9|6|5|4)|17(0|8|3|7)|18(2|3|6|7|9)|15(3|5|6|7|8|9))\d{8}$')
    if phone is None or p.match(phone):
        return True
    return False


def check_face_format(face):
    if face and allow_pic(face.filename):  # 文件不为空and文件格式正确
        return True
    return False


def check_isbn_format(isbn):
    if len_is_between(isbn, 0, 50):
        return True
    return False


def check_title_format(title):
    if len_is_between(title, 0, 50):
        return True
    return False


def check_author_format(author):
    if len_is_between(author, 0, 255):
        return True
    return False


def check_publication_format(publication):
    if len_is_between(publication, 0, 255):
        return True
    return False


def check_publish_time_format(publish_time):
    if is_date_format(publish_time):
        return True
    return False


def check_isborrowed_format(isborrowed):
    if isborrowed == 0 or isborrowed == 1:
        return True
    return False


def check_isreturned_format(isreturned):
    if isreturned == 0 or isreturned == 1:
        return True
    return False


def check_comment_format(comment):
    if len_is_between(comment, 0, 10240):
        return True
    return False


def check_tag_format(name):
    if len_is_between(name, 1, 20):
        return True
    return False


def check_uid_format(uid):
    if not is_int_number(uid):
        return False
    return True


def check_user_operation_format(operation):
    if operation < 0 or operation >= len(ManageOrder.USER_OP_TO_STRING):
        return False
    return True


def check_admin_operation_format(operation):
    if operation < 0 or operation >= len(ManageOrder.ADMIN_OP_TO_STRING):
        return False
    return True


def check_object_format(objects):
    return True


def check_time_format(time):
    if not is_datetime_format(time):
        return False
    return True


def save_user_image(face, count=0):
    if count > 1:
        return None, False
    if face is None:
        return None, False
    try:

        filename = secure_filename("user_face_%s" % (face.filename))
        path = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(path):
            face.save(path)
        return "/" + Config.XD_USER_DIR +"/"+ filename, True
    except Exception as e:
        print("Error:", e.args)
        return save_user_image(face, count + 1)


def to_date_type(birthday):
    return datetime.strptime(birthday, "%Y-%m-%d")


def check_register_date(dict):
    sid = dict.get("sid")
    pwd = dict.get("password")
    institute = dict.get("institute")
    username = dict.get("username")
    realname = dict.get("realname")
    birthday = dict.get("birthday")
    email = dict.get("email")
    phone = dict.get("phone")
    # sex = 0

    sex = dict.get("sex")
    if sex is None:
        sex = 0
    dict = ImmutableMultiDict(dict).to_dict()

    if sid is None:
        return make_json({}, 400, "缺少学号参数"), False
    if pwd is None:
        return make_json({}, 400, "缺少密码参数"), False
    if username is None:
        return make_json({}, 400, "缺少用户名参数"), False
    if realname is None:
        return make_json({}, 400, "缺少真实姓名参数"), False

    if not check_sid_format(sid):
        return make_json({}, 400, "学号格式错误"), False
    if not check_pwd_format(pwd):
        return make_json({}, 400, "密码格式错误"), False
    if not check_username_format(username):
        return make_json({}, 400, "用户名格式错误"), False
    if not check_institute_format(institute):
        return make_json({}, 400, "学院格式错误"), False
    if not check_sex_format(sex):
        return make_json({}, 400, "性别数字大小错误"), False
    else:
        dict['sex'] = sex
    if not check_birthday_format(birthday):
        return make_json({}, 400, "生日格式错误"), False
    else:
        if not dict.get("birthday") is None:
            dict['birthday'] = to_date_type(birthday)
    if not check_email_format(email):
        return make_json({}, 400, "邮箱格式错误"), False
    if not check_phone_format(phone):
        return make_json({}, 400, "电话格式错误"), False

    if dict.get("email") is None and dict.get("phone") is None:
        return make_json({}, 400, "电话和邮箱不能同时为空"), False

    return dict, True


def check_changed_date(dict, face):
    institute = dict.get("institute")
    username = dict.get("username")
    realname = dict.get("realname")
    birthday = dict.get("birthday")
    email = dict.get("email")
    phone = dict.get("phone")
    # sex = 0

    sex = dict.get("sex")
    if sex is None:
        sex = -1
    dict = ImmutableMultiDict(dict).to_dict()

    if username is not None and not check_username_format(username):
        return make_json({}, 400, "用户名格式错误"), False
    if institute is not None and not check_institute_format(institute):
        return make_json({}, 400, "学院格式错误"), False
    if sex != -1 and not check_sex_format(sex):
        return make_json({}, 400, "性别数字大小错误"), False
    elif sex == -1:
        dict['sex'] = None
    if birthday is not None and not check_birthday_format(birthday):
        return make_json({}, 400, "生日格式错误"), False
    else:
        if not dict.get("birthday") is None:
            dict['birthday'] = to_date_type(birthday)
    if email is not None and not check_email_format(email):
        return make_json({}, 400, "邮箱格式错误"), False
    if phone is not None and not check_phone_format(phone):
        return make_json({}, 400, "电话格式错误"), False

    if face is not None and not check_face_format(face):
        return make_json({}, 400, "头像出现未知错误"), False

    return dict, True


def has_user_sid(sid):
    if User.query.filter_by(sid=sid).first() is not None:
        return True
    return False


def add_user_to_db(register_date):
    try:
        user = User(sid=register_date["sid"], password=User.create_hash_pwd(register_date["password"])
                    , username=register_date["username"], realname=register_date["realname"],
                    institute=register_date.get("institute"), sex=register_date.get("sex"),
                    birthday=register_date.get("birthday"), email=register_date.get("email"),
                    phone=register_date.get("phone"), left_borrow=50)
        db.session.add(user)
        db.session.commit()
        return True
    except ValueError as e:
        print("Error:", e.args)
    return False


def user_change_user_to_db(id, changed_date: dict,face):
    user = User.query.filter_by(id=id).first()

    institute = changed_date.get("institute")
    username = changed_date.get("username")
    realname = changed_date.get("realname")
    birthday = changed_date.get("birthday")
    email = changed_date.get("email")
    phone = changed_date.get("phone")
    sex = changed_date.get("sex")

    face_path, is_save_success = save_user_image(changed_date.get("face"))
    if is_save_success:
        user.face = face_path
    if institute is not None:
        user.institute = institute
    if username is not None:
        user.username = username
    if realname is not None:
        user.realname = realname
    if birthday is not None:
        user.birthday = birthday
    if email is not None:
        user.email = email
    if phone is not None:
        user.phone = phone
    if sex is not None and sex != -1:
        user.sex = sex
    if face is not None:
        filename,is_save = save_user_image(face)
        if is_save:
            user.face = filename
    db.session.commit()

    return True


def check_book_date(data):
    isbn = data.get('isbn')
    title = data.get('title')
    author = data.get('author')
    publication = data.get('publication')
    publish_time = data.get('publish_time')
    isborrowed = data.get('isborrowed', type=int)
    per_page = data.get('per_page')
    page = data.get('page')
    if per_page is None:
        per_page = 20
    if page is None:
        page=1

    data = ImmutableMultiDict.to_dict(data)
    data['per_page'] = per_page
    data['page'] = page

    if isbn is not None and not check_isbn_format(isbn):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'ISBN号'格式错误"), False
    if title is not None and not check_title_format(title):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'标题'格式错误"), False
    if author is not None and not check_author_format(author):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'作者'格式错误"), False
    if publication is not None and not check_publication_format(publication):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'出版社'格式错误"), False
    if publish_time is not None and not check_publish_time_format(publish_time):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'出版日期'格式错误"), False
    if isborrowed is not None and not check_isborrowed_format(isborrowed):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'是否借出'格式错误"), False

    return data, True


def none_type_to_str(data):
    if data is None or len(data)==0:
        return None
    return data

def check_user_level_return(user,is_overtime):
    if user.total_borrowed<50:
        if is_overtime:
            user.overtime_borrowed+=1
            if user.overtime_borrowed==2:
                user.total_borrowed-=3
            if user.overtime_borrowed==5:
                user.total_borrowed-=1
            if user.overtime_borrowed==10:
                user.total_borrowed-=1
    else:

        if is_overtime:
            origin_standard = user.overtime_borrowe/user.total_borrowed
            origin_level = get_borrow_level(origin_standard)
            user.overtime_borrowed += 1
            standard = user.overtime_borrowe/user.total_borrowed
            level = get_borrow_level(standard)

            if origin_level!=level:
                if origin_level==1 and level == 2:
                    user.total_borrowed-=20
                elif origin_level==2 and level == 3:
                    user.total_borrowed-=20
                elif origin_level==3 and level == 4:
                    user.total_borrowed-=10





def return_book_with_id_and_isbn(id, isbn):
    if not check_isbn_format(isbn):
        return False
    book = Book.query.filter(Book.isbn == isbn).first()
    b_book = Borrow.query.filter(Borrow.uid == id, Borrow.bid == book.id).first()

    if b_book is not None:
        is_overtime = b_book.return_time < datetime.now()
        r_book = Return(bid=b_book.bid, uid=b_book.uid, borrow_time=b_book.addtime)
        book.isborrowed = 0
        user = User.query.filter(User.id == id).first()
        if user:
            check_user_level_return(user,is_overtime)

        db.session.add(r_book)
        db.session.delete(b_book)
        db.session.commit()
        # print(datetime.strftime(r_book.addtime,"%Y-%m-%d %H:%M:%S"))
        return True

    return False

def get_borrow_level(standard):
    if standard==0:
        return 1
    if standard<0.1:
        return 2
    if standard<0.2:
        return 3
    return 4

def update_user_level_borrow(user):
    if user.total_borrowed>=50:
        if user.total_borrowed==50:
            if user.overtime_borrowed==0:
                user.left_borrow+=45
            elif user.overtime_borrowed==1:
                user.left_borrow+=25
            elif user.overtime_borrowed<5:
                user.left_borrow+=28
            elif user.overtime_borrowed<10:
                user.left_borrow+=9
        elif user.total_borrowed>50:
            origin_total = user.total_borrowed-1
            origin_standard = user.overtime_borrowed/origin_total
            standard = user.overtime_borrowed/user.total_borrowed
            origin_level = get_borrow_level(origin_standard)
            level = get_borrow_level(standard)
            if level!=origin_level:
                if level==1 and origin_level==2:
                    user.total_borrowed+=20
                elif level==2 and origin_level==3:
                    user.total_borrowed+=20
                elif level==3 and origin_level==4:
                    user.total_borrowed+=10



def borrow_book_with_id_and_isbn(id, isbn):
    if not check_isbn_format(isbn):
        return 400, None
    book = Book.query.filter(Book.isbn == isbn).first()
    if book.isborrowed == 1:
        return 401, None
    if book is not None:
        b_user = User.query.filter_by(id=id).first()
        if b_user.left_borrow > 0:
            b_book = Borrow(bid=book.id, uid=id)
            book.isborrowed = 1
            db.session.add(b_book)
            b_user.total_borrowed += 1
            b_user.left_borrow -= 1
            update_user_level_borrow(b_user)
            db.session.commit()
            return 0, b_book.return_time
        return 401, None

    return 404, None


def search_books(data):
    isbn = none_type_to_str(data.get('isbn'))
    title = none_type_to_str(data.get('title'))
    author = none_type_to_str(data.get('author'))
    publication = none_type_to_str(data.get('publication'))
    publish_time = none_type_to_str(data.get('publish_time'))
    isborrowed = none_type_to_str(data.get('isborrowed'))

    books = Book.query.filter(
        Book.isbn.like("%{keyword}%".format(keyword=isbn)) if isbn is not None else True,
        Book.title.like("%{keyword}%".format(keyword=title)) if title is not None else True,
        Book.author.like("%{keyword}%".format(keyword=author)) if author is not None else True,
        Book.publication.like("%{keyword}%".format(keyword=publication)) if publication is not None else True,
        Book.publish_time.like("%{keyword}%".format(keyword=publish_time)) if publish_time is not None else True,
        Book.isborrowed == isborrowed if isborrowed is not None else True
    ).order_by(Book.id.desc())
    books = books.paginate(page=data.get('page'), per_page=data.get('per_page'), error_out=False)
    return books


def get_book_data_detail(book):
    if book is None:
        return None
    tags = Book_Tag.query.filter(Book_Tag.bid == book.id).all()
    tags_list = []
    for tag in tags:
        tag_temp = Tag.query.get(tag.tid)
        tags_list.append({"id": tag_temp.id, "name": tag_temp.name})
    book_temp = {
        "id": book.id,
        "isbn": book.isbn,
        "title": book.title,
        "cover_image": book.cover_image if book.cover_image is not None else Config.DEFAULT_BOOK_COVER_GET,
        "author": book.author,
        "publication": book.publication,
        "publish_time": book.publish_time.strftime("%Y-%m-%d") if book.publish_time is not None else "",
        "isborrowed": book.isborrowed,
        "tag_list": tags_list,
    }
    return book_temp


def comment_in_book(id: int, isbn, comment):
    if comment is not None and not check_comment_format(comment):
        return 401
    if isbn is None or not check_isbn_format(isbn):
        return 404
    book = Book.query.filter(Book.isbn == isbn).first()

    if book is not None:
        comment = Comment(bid=book.id, uid=id, comment=comment)
        db.session.add(comment)
        db.session.commit()
        return 0

    return 404


def delete_comment_by_id(comment_id):
    comment = Comment.query.get(comment_id)
    if comment is None:
        return False, None
    else:
        book = Book.query.get(comment.bid)
        isbn = book.isbn
        db.session.delete(comment)
        db.session.commit()
        return True, isbn


def get_comment_id_detail(comment):
    if comment is None:
        return None
    book = Book.query.filter_by(id=comment.bid).first()
    user = User.query.filter_by(id=comment.uid).first()
    if book is None or user is None:
        return None
    comment_temp = {
        "id": comment.id,
        "isbn": book.isbn,
        "user_id": comment.uid,
        "book_id": comment.bid,
        "content": comment.comment,
        "username": user.username,
        "face": user.face if user.face is not None else Config.DEFAULT_USER_FACE_GET,
        "title": book.title,
        "addtime": comment.addtime.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return comment_temp


def check_comment_search_date(data):
    user_id = data.get('user_id', type=int)
    isbn = data.get('isbn')
    before_time = data.get('before_time')
    after_time = data.get('after_time')
    page = data.get('page')
    per_page = data.get('per_page')
    if per_page is None:
        per_page = 20
    if page is None:
        page = 1

    data = ImmutableMultiDict.to_dict(data)
    data['page'] = page
    data['per_page'] = per_page

    if isbn is not None and not check_isbn_format(isbn):
        return make_json({}, ErrorCode.INVALID_KEY, "isbn格式错误"), False
    if before_time is not None and not is_datetime_format(before_time):
        return make_json({}, ErrorCode.INVALID_KEY, "before_time格式错误"), False
    if after_time is not None and not is_datetime_format(after_time):
        return make_json({}, ErrorCode.INVALID_KEY, "after_time格式错误"), False

    return data, True


def search_comments(data):
    user_id = none_type_to_str(data.get('user_id'))
    isbn = none_type_to_str(data.get('isbn'))
    before_time = none_type_to_str(data.get('before_time'))
    after_time = none_type_to_str(data.get('after_time'))

    bid = None
    if isbn is not None:
        book_temp = Book.query.filter_by(isbn=isbn).first()
        if book_temp is not None:
            bid = book_temp.id
        else:
            return None
    comments = Comment.query.filter(
        Comment.uid==user_id if user_id is not None else True,
        Comment.bid==bid if bid is not None else True,
        Comment.addtime <= before_time if before_time is not None else True,
        Comment.addtime >= after_time if after_time is not None else True
    ).order_by(Comment.addtime.desc())
    comments = comments.paginate(page=data.get('page'), per_page=data.get('per_page'), error_out=False)
    return comments


def check_record_date(data):
    isbn = data.get('isbn')
    title = data.get('title')
    author = data.get('author')
    publication = data.get('publication')
    publish_time = data.get('publish_time')
    isreturned = data.get('isreturned')
    per_page = data.get('per_page')
    page = data.get('page')
    if isreturned is None:
        isreturned = 0
    if per_page is None:
        per_page = 20
    if page is None:
        page = 1

    data = ImmutableMultiDict.to_dict(data)
    data['isreturned'] = isreturned
    data['per_page'] = per_page
    data['page'] = page

    if isbn is not None and not check_isbn_format(isbn):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'ISBN号'格式错误"), False
    if title is not None and not check_title_format(title):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'标题'格式错误"), False
    if author is not None and not check_author_format(author):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'作者'格式错误"), False
    if publication is not None and not check_publication_format(publication):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'出版社'格式错误"), False
    if publish_time is not None and not check_publish_time_format(publish_time):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'出版日期'格式错误"), False
    if isreturned is not None and not check_isreturned_format(isreturned):
        return make_json({}, ErrorCode.INVALID_KEY, "参数'是否归还'格式错误"), False

    return data, True


def user_record_by_id(id: int, isreturned=0, page=1, per_page=20):
    data = []
    if isreturned == 0:
        data_r = Return.query.filter_by(uid=id).order_by(Return.borrow_time.desc()).paginate(page=page,
                                                                                             per_page=per_page,
                                                                                             error_out=False)
        for i in data_r.items:
            temp = {
                "bid": i.bid,
                "borrow_time": i.borrow_time,
                "return_time": i.addtime,
                "isreturned": isreturned,
            }
            data.append(temp)
    else:
        data_r = Borrow.query.filter_by(uid=id).order_by(Borrow.addtime.desc()).paginate(page, per_page=per_page,
                                                                                         error_out=False)

        for i in data_r.items:
            temp = {
                "bid": i.bid,
                "borrow_time": i.addtime,
                "return_time": i.return_time,
                "isreturned": isreturned,
            }
            data.append(temp)

    return data


def search_record(data, user_data):
    isbn = none_type_to_str(data.get('isbn'))
    title = none_type_to_str(data.get('title'))
    author = none_type_to_str(data.get('author'))
    publication = none_type_to_str(data.get('publication'))
    publish_time = none_type_to_str(data.get('publish_time'))
    isreturned = data.get('isreturned')
    isbn_list = []
    for x in user_data:
        isbn_list.append(Book.query.get(x['bid']).isbn)
    isbn_list = list(set(isbn_list))

    data_list = [x for x in user_data]
    books = Book.query.filter(
        Book.isbn.in_(isbn_list) if len(isbn_list) != 0 else True,
        Book.isbn == isbn if isbn is not None else True,
        Book.title.like("%{keyword}%".format(keyword=title)) if title is not None else True,
        Book.author.like("%{keyword}%".format(keyword=author)) if author is not None else True,
        Book.publication.like("%{keyword}%".format(keyword=publication)) if publication is not None else True,
        Book.publish_time.like("%{keyword}%".format(keyword=publish_time)) if publish_time is not None else True
    ).all()

    ret = []
    for record in data_list:
        view_temp = create_record(books, record)
        if view_temp is not None:
            ret.append(view_temp)

    return ret


def create_record(books, record):
    book = None
    for item in books:
        if record['bid'] == item.id:
            book = item
    if book is None:
        return None

    view_temp = {
        "id": book.id,
        "isbn": book.isbn,
        "title": book.title,
        "cover_image": book.cover_image if book.cover_image is not None else Config.DEFAULT_BOOK_COVER,
        "author": book.author,
        "publication": book.publication if book.publication is not None else "",
        "publish_time": book.publish_time.strftime("%Y-%m-%d") if book.publish_time is not None else "",
        "borrow_time": record.get('borrow_time').strftime("%Y-%m-%d %H:%M:%S"),
        "return_time": record.get('return_time').strftime("%Y-%m-%d %H:%M:%S"),
        "isreturned": record.get('isreturned'),
    }

    return view_temp


def get_tag_detail(tag):
    if tag is not None:
        return {
            "id": tag.id,
            "name": tag.name,
        }
    return None


def recommend_book_to_user(id: int,page,per_page):
    user = User.query.get(id)
    if user is None:
        return None
    b_books = Return.query.filter(Return.uid==id).order_by(Return.addtime.desc()).limit(10)
    isbn_list = []
    for i in b_books:
        book = Book.query.filter(Book.id==i.bid).first()
        isbn_list.append(book.isbn)
    re_isbn_list = re_book_isbn(isbn_list)
    books = []
    cnt = 0
    for i in re_isbn_list:
        book = Book.query.filter(Book.isbn==i).first()
        if book is not None:
            books.append(book)
            cnt+=1
            if cnt>=per_page:
                break
    if cnt<per_page:
        boks = Book.query.order_by(func.rand()).limit(per_page-cnt)
        for i in boks:
            books.append(i)
    return books

def re_book_isbn(isbn_list):

    user = np.zeros((1,len(re_items)))[0]
    for i in isbn_list:
        user[items_kv[i]] = 7
    RES = top10_simliar(user)

    userid_list = []
    for i in RES:
        userid = i[0]
        userid_list.append(dataset.iloc[userid, 0])
    # print(dataset.iloc[userid,0])

    per_page = 10 * 2
    cnt = 0
    book_list = []
    for it in dataset.itertuples():
        # print(it[0],userid_list)
        if it[1] in userid_list:
            # print(it)
            book_list.append(it[3])
            cnt += 1
            if cnt >= per_page:
                break
    return book_list


def Euclidean(user1, user2):
    # 取出两位用户评论过的书和评分
    user1_data = train_data_matrix[user1]
    user2_data = user2
    distance = 0
    # 找到两位用户都评论过的书，并计算欧式距离
    for i in range(0, len(user1_data)):
        if user1_data[i] != 0 and user2_data[i] != 0:
            # 注意，distance越大表示两者越相似
            distance += pow(float(user1_data[i]) - float(user2_data[i]), 2)

    return 1 / (1 + sqrt(distance))  # 这里返回值越小，相似度越大

# 计算某个用户与其他用户的相似度
def top10_simliar(user):
    res = []
    for userid in range(random.randint(0, 20), re_users.shape[0], int(re_users.shape[0] / 20)):
        # 排除与自己计算相似度
        simliar = Euclidean(userid, user)
        res.append((userid, simliar))
    res.sort(key=lambda val: val[1])
    print(res[:20])
    return res[:20]



def add_user_log(sid, code, objects=None):
    if objects is None:
        log = User_log(sid=sid, operation=code)
    else:
        log = User_log(sid=sid, operation=code, object=objects)
    db.session.add(log)
    db.session.commit()


# -*---------------------------------------------


def check_modify_user_data(dict,user_face):
    sid = dict.get("sid")
    institute = dict.get("institute")
    username = dict.get("username")
    realname = dict.get("realname")
    birthday = dict.get("birthday")
    email = dict.get("email")
    phone = dict.get("phone")
    sex = dict.get("sex")
    left_borrow = dict.get("left_borrow")
    totle_borrowed = dict.get("totle_borrowed")
    overtime_borrowed = dict.get("overtime_borrowed")
    if sex is None:
        sex = -1
    if left_borrow is None:
        left_borrow = -1
    if totle_borrowed is None:
        totle_borrowed = -1
    if overtime_borrowed is None:
        overtime_borrowed = -1

    dict = ImmutableMultiDict(dict).to_dict()

    if sid is not None and not check_sid_format(sid):
        return make_json({}, 400, "学号格式错误"), False

    if username is not None and not check_username_format(username):
        return make_json({}, 400, "用户名格式错误"), False
    if realname is not None and not check_realname_format(realname):
        return make_json({}, 400, "姓名格式错误"), False
    if user_face is not None and not check_face_format(user_face):
        return make_json({}, 400, "头像格式错误"), False

    if institute is not None and not check_institute_format(institute):
        return make_json({}, 400, "学院格式错误"), False
    if sex != -1 and not check_sex_format(sex):
        return make_json({}, 400, "性别数字大小错误"), False
    else:
        dict['sex'] = None
    if birthday is not None and not check_birthday_format(birthday):
        return make_json({}, 400, "生日格式错误"), False
    else:
        if not dict.get("birthday") is None:
            dict['birthday'] = to_date_type(birthday)
    if email is not None and not check_email_format(email):
        return make_json({}, 400, "邮箱格式错误"), False
    if phone is not None and not check_phone_format(phone):
        return make_json({}, 400, "电话格式错误"), False

    if left_borrow!=-1 and not left_borrow >= 0:
        return make_json({}, 400, "用户可借书上限应大于等于0"), False
    else:
        dict['left_borrow'] = None

    if totle_borrowed!=-1 and not totle_borrowed >= 0:
        return make_json({}, 400, "用户总借书数量应大于等于0"), False
    else:
        dict['totle_borrowed'] = None

    if overtime_borrowed!=-1 and not overtime_borrowed >= 0:
        return make_json({}, 400, "用户逾期还书数量应大于等于0"), False
    else:
        dict['overtime_borrowed'] = None
    return dict, True


def check_query_user_data(data):
    sid = data.get("sid")
    institute = data.get("institute")
    username = data.get("username")
    birthday = data.get("birthday")
    email = data.get("email")
    phone = data.get("phone")
    sex = data.get("sex")
    left_borrow = data.get("left_borrow")  #
    totle_borrowed = data.get("totle_borrowed")  #
    overtime_borrowed = data.get("overtime_borrowed")  #
    per_page = data.get('per_page')
    page = data.get('page')
    if sex is None:
        sex = -1
    if left_borrow is None:
        left_borrow = -1
    if totle_borrowed is None:
        totle_borrowed = -1
    if overtime_borrowed is None:
        overtime_borrowed = -1
    if per_page is None:
        per_page = 20
    if page is None:
        page = 1

    data = ImmutableMultiDict(data).to_dict()
    data['per_page'] = per_page
    data['page'] = page
    data['sex'] = sex
    data['left_borrow'] = left_borrow
    data['totle_borrowed'] = totle_borrowed
    data['overtime_borrowed'] = overtime_borrowed

    if sid is not None and not check_sid_format(sid):
        return make_json({}, 400, "学号格式错误"), False

    if username is not None and not check_username_format(username):
        return make_json({}, 400, "用户名格式错误"), False

    if institute is not None and not check_institute_format(institute):
        return make_json({}, 400, "学院格式错误"), False
    if sex != -1 and not check_sex_format(sex):
        return make_json({}, 400, "性别数字大小错误"), False
    elif sex == -1:
        data['sex'] = None
    if birthday is not None and not check_birthday_format(birthday):
        return make_json({}, 400, "生日格式错误"), False

    if email is not None and not check_email_format(email):
        return make_json({}, 400, "邮箱格式错误"), False
    if phone is not None and not check_phone_format(phone):
        return make_json({}, 400, "电话格式错误"), False

    if left_borrow != -1 and not left_borrow >= 0:
        return make_json({}, 400, "用户可借书上限应大于等于0的纯数字"), False
    elif left_borrow == -1:
        data['left_borrow'] = None

    if totle_borrowed != -1 and not totle_borrowed >= 0:
        return make_json({}, 400, "用户总借书数量应大于等于0的纯数字"), False
    elif totle_borrowed == -1:
        data['totle_borrowed'] = None

    if overtime_borrowed != -1 and not overtime_borrowed >= 0:
        return make_json({}, 400, "用户逾期还书数量应大于等于0的纯数字"), False
    elif overtime_borrowed == -1:
        data['overtime_borrowed'] = None

    return data, True


def check_add_user_data(dict):
    sid = dict.get("sid")
    pwd = dict.get("password")
    institute = dict.get("institute")
    username = dict.get("username")
    realname = dict.get("realname")
    birthday = dict.get("birthday")
    email = dict.get("email")
    phone = dict.get("phone")
    # sex = 0

    sex = dict.get("sex")
    if sex is None:
        sex = 0
    dict = ImmutableMultiDict(dict).to_dict()

    if sid is None:
        return make_json({}, 400, "缺少学号参数"), False
    if pwd is None:
        return make_json({}, 400, "缺少密码参数"), False
    if username is None:
        return make_json({}, 400, "缺少用户名参数"), False
    if realname is None:
        return make_json({}, 400, "缺少真实姓名参数"), False

    if not check_sid_format(sid):
        return make_json({}, 400, "学号格式错误"), False
    if not check_pwd_format(pwd):
        return make_json({}, 400, "密码格式错误"), False
    if not check_username_format(username):
        return make_json({}, 400, "用户名格式错误"), False
    if not check_institute_format(institute):
        return make_json({}, 400, "学院格式错误"), False
    if not check_sex_format(sex):
        return make_json({}, 400, "性别数字大小错误"), False
    else:
        dict['sex'] = sex
    if not check_birthday_format(birthday):
        return make_json({}, 400, "生日格式错误"), False
    else:
        if not dict.get("birthday") is None:
            dict['birthday'] = to_date_type(birthday)
    if not check_email_format(email):
        return make_json({}, 400, "邮箱格式错误"), False
    if not check_phone_format(phone):
        return make_json({}, 400, "电话格式错误"), False

    if dict.get("email") is None and dict.get("phone") is None:
        return make_json({}, 400, "电话和邮箱不能同时为空"), False

    return dict, True


def search_users(data):
    id = data.get("id")
    sid = none_type_to_str(data.get("sid"))
    institute = none_type_to_str(data.get("institute"))
    username = none_type_to_str(data.get("username"))
    realname = none_type_to_str(data.get("realname"))
    birthday = none_type_to_str(data.get("birthday"))
    email = none_type_to_str(data.get("email"))
    phone = none_type_to_str(data.get("phone"))
    sex = data.get("sex")
    left_borrow = data.get("left_borrow")
    totle_borrowed = data.get("totle_borrowed")
    overtime_borrowed = data.get("overtime_borrowed")

    users = User.query.filter(
        (User.id==id) if id is not None else True,
        (User.sid==sid) if sid is not None else True,
        User.institute.like("%{keyword}%".format(keyword=institute)) if institute is not None else True,
        User.username.like("%{keyword}%".format(keyword=username)) if username is not None else True,
        User.realname.like("%{keyword}%".format(keyword=realname)) if realname is not None else True,
        User.birthday.is_(birthday) if birthday is not None else True,
        User.email.like("%{keyword}%".format(keyword=email)) if email is not None else True,
        User.phone.like("%{keyword}%".format(keyword=phone)) if phone is not None else True,
        User.sex==sex if sex is not None else True,
        User.left_borrow==left_borrow if left_borrow is not None else True,
        User.total_borrowed==totle_borrowed if totle_borrowed is not None else True,
        User.overtime_borrowed==overtime_borrowed if overtime_borrowed is not None else True,
    ).order_by(User.id)
    page = data.get('page')
    per_page = data.get('per_page')
    if id is None:
        users = users.paginate(page=page if page is not None else 1, per_page=per_page if per_page is not None else 1, error_out=False)
    else:
        users = users.all()
    return users


def save_user_image(face, count=0):
    if count > 1:
        return None, False
    if face is None:
        return None, False
    try:
        filename = secure_filename("user_face_%s" % (face.filename))
        path = os.path.join(Config.UPLOAD_FOLDER, filename)
        if not os.path.exists(path):
            face.save(path)
        return "/" + Config.XD_USER_DIR+"/" + filename, True
    except Exception as e:
        print("Error:", e.args)
        return save_user_image(face, count + 1)


def change_user_to_db(id, changed_data: dict,user_face):
    user = User.query.filter_by(id=id).first()
    sid = changed_data.get("sid")
    institute = changed_data.get("institute")
    username = changed_data.get("username")
    password = changed_data.get("password")
    if password is not None:
        password = User.create_hash_pwd(password)
    realname = changed_data.get("realname")
    birthday = changed_data.get("birthday")
    email = changed_data.get("email")
    phone = changed_data.get("phone")
    sex = changed_data.get("sex")

    left_borrow = changed_data.get("left_borrow")
    totle_borrowed = changed_data.get("totle_borrowed")
    overtime_borrowed = changed_data.get("overtime_borrowed")

    if sid is not None:
        user.sid = sid
    if institute is not None:
        user.institute = institute
    if password is not None:
        user.password = password
    if user_face is not None:
        filename,is_save = save_user_image(user_face)
        if is_save:
            user.face = filename
    if username is not None:
        user.username = username
    if realname is not None:
        user.realname = realname
    if birthday is not None:
        user.birthday = birthday
    if email is not None:
        user.email = email
    if phone is not None:
        user.phone = phone
    if sex is not None and sex != -1:
        user.sex = sex
    if left_borrow is not None and left_borrow !=-1:
        user.left_borrow = left_borrow
    if totle_borrowed is not None and totle_borrowed !=-1:
        user.total_borrowed = totle_borrowed
    if overtime_borrowed is not None and overtime_borrowed !=-1:
        user.overtime_borrowed = overtime_borrowed

    db.session.commit()

    return True


def check_cover_image_format(cover_image):
    if cover_image and allow_pic(cover_image.filename):  # 文件不为空and文件格式正确
        return True
    return False


def check_tag_list_format(tag_list):
    for i in range(0,len(tag_list)):
        if not is_int_number(tag_list[i]):
            return False
        tag_list[i] = int(tag_list[i])
        tag = db.session.query(Tag.id).filter(Tag.id==tag_list[i]).first()
        if tag is None:
            return False
    return True


def save_book_cover(cover, count=0):
    if count > 1:
        return None, False
    if cover is None:
        return None, False
    try:

        filename = secure_filename("book_cover_%s" % (cover.filename))
        path = os.path.join(Config.UPLOAD_FOLDER_BOOK, filename)
        if not os.path.exists(path):
            cover.save(path)
        return "/"+Config.XD_BOOK_DIR+"/"+filename, True
    except Exception as e:
        print("Error:", e.args)
        return save_book_cover(cover, count + 1)


def check_change_book_data(data,cover_image):
    title = data.get("title")
    author = data.get("author")
    publish_time = data.get("publish_time")
    publication = data.get("publication")

    tag_list = data.get("tag_list")
    data = ImmutableMultiDict.to_dict(data)
    data['tag_list'] = tag_list

    if title is not None and not check_title_format(title):
        return make_json({}, ErrorCode.INVALID_KEY, "标题格式不规范"), False
    if author is not None and not check_author_format(author):
        return make_json({}, ErrorCode.INVALID_KEY, "作者格式不规范"), False
    if publish_time is not None and not check_publish_time_format(publish_time):
        return make_json({}, ErrorCode.INVALID_KEY, "出版时间格式不规范"), False
    if publication is not None and not check_publication_format(publication):
        return make_json({}, ErrorCode.INVALID_KEY, "出版社格式不规范"), False
    if cover_image is not None and not check_cover_image_format(cover_image):
        return make_json({}, ErrorCode.INVALID_KEY, "封面格式不规范"), False
    if tag_list is not None and not check_tag_list_format(tag_list):
        return make_json({}, ErrorCode.INVALID_KEY, "标签列表格式不规范或有标签不存在"), False

    return data, True


def change_book_data(book, data,cover_image):
    title = data.get("title")
    author = data.get("author")
    publish_time = data.get("publish_time")
    publication = data.get("publication")
    tag_list = data.get("tag_list")

    if title is not None:
        book.title = title
    if author is not None:
        book.author = author
    if publish_time is not None:
        book.publish_time = publish_time
    if publication is not None:
        book.publication = publication
    if cover_image is not None:
        filename, is_save = save_book_cover(cover_image)
        if is_save:
            book.cover_image = filename
    if tag_list is not None:
        tags = Book_Tag.query.filter(Book_Tag.bid == book.id).all()
        for tag in tags:
            db.session.delete(tag)
        for tag_num in tag_list:
            db.session.add(Book_Tag(bid=book.id, tid=tag_num))
    db.session.commit()


def check_book_rank(data):
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    per_page = data.get('per_page')
    page = data.get('page')
    if per_page is None:
        per_page = 10
    if page is None:
        page = 1

    data = ImmutableMultiDict.to_dict(data)
    data['per_page'] = per_page
    data['page'] = page

    if start_time is not None and not is_date_format(start_time):
        return make_json({}, ErrorCode.INVALID_KEY, "开始时间格式错误"), False
    if end_time is not None and not is_date_format(end_time):
        return make_json({}, ErrorCode.INVALID_KEY, "结束时间格式错误"), False

    return data, True


def borrow_rank(data):
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    per_page = data.get('per_page')
    page = data.get('page')

    ret_list1 = db.session.query(Return.uid.label("uid"), func.count(Return.id).label("counts1")).filter(
        Return.borrow_time >= start_time if start_time is not None else True,
        Return.borrow_time <= end_time if end_time is not None else True
    ).group_by(Return.uid).subquery()

    ret_list2 = db.session.query(Borrow.uid.label("uid"), func.count(Borrow.uid).label("counts2")).filter(
        Borrow.addtime >= start_time if start_time is not None else True,
        Borrow.addtime <= end_time if end_time is not None else True
    ).group_by(Borrow.uid).subquery()

    out_link_list = db.session.query(
        ret_list1.c.uid.label("uid1"), ret_list2.c.uid.label("uid2"),
        func.coalesce(ret_list1.c.uid, ret_list2.c.uid).label("uid"),
        (func.coalesce(ret_list1.c.counts1, 0) + func.coalesce(ret_list2.c.counts2, 0)).label("sums")
    ).outerjoin(
        ret_list1, ret_list2.c.uid == ret_list1.c.uid
    ).subquery()

    ret_list = db.session.query(
        User.id,
        User.sid,
        User.username,
        User.face,
        out_link_list.c.sums
    ).filter(or_(User.id == out_link_list.c.uid1, User.id == out_link_list.c.uid)).order_by(db.desc("sums"))

    ret = []
    for item in ret_list.paginate(page, per_page, error_out=False).items:
        temp = {
            "id": item.id,
            "sid": item.sid,
            "username": item.username,
            "face": item.face if item.face is not None else Config.DEFAULT_USER_FACE_GET,
            "totle_borrowed": item.sums,
        }
        ret.append(temp)
    return ret


def check_add_book_data(data,files):
    if data.get("title") is None:
        return make_json({}, ErrorCode.INVALID_KEY, "标题不能为空"), False
    data, is_checked = check_change_book_data(data,files)
    if not is_checked:
        return data, False
    return data, True


def add_one_book(isbn, data,cover_image):
    title = data.get("title")
    author = data.get("author")
    publish_time = data.get("publish_time")
    publication = data.get("publication")
    tag_list = data.get("tag_list")

    book = Book(isbn=isbn, title=title)
    if author is not None:
        book.author = author
    if publish_time is not None:
        book.publish_time = publish_time
    if publication is not None:
        book.publication = publication
    if cover_image is not None:
        filename, is_saved = save_book_cover(cover_image)
        if is_saved:
            book.cover_image = filename
    db.session.add(book)
    db.session.commit()
    try:
        if tag_list is not None:
            for i in tag_list:
                db.session.add(Book_Tag(bid=book.id, tid=i))
    except Exception:
        db.session.rollback()
        db.session.delete(book)
        db.session.commit()
        return False
    db.session.commit()
    return True


def search_admin_log(format_data):
    adminname = none_type_to_str(format_data.get("adminname"))
    operation = none_type_to_str(format_data.get("operation"))
    object = none_type_to_str(format_data.get("object"))
    start_time = none_type_to_str(format_data.get("start_time"))
    end_time = none_type_to_str(format_data.get("end_time"))

    admin_logs = Admin_log.query.filter(
        Admin_log.adminname == adminname if adminname is not None else True,
        Admin_log.operation == operation if operation is not None else True,
        Admin_log.object.like("%{keyword}%".format(keyword=object)) if object is not None else True,
        Admin_log.addtime >= start_time if start_time is not None else True,
        Admin_log.addtime <= end_time if end_time is not None else True,
    ).order_by(Admin_log.addtime.desc())
    admin_logs = admin_logs.paginate(page=format_data.get('page'), per_page=format_data.get('per_page'),
                                     error_out=False)
    return admin_logs


def search_user_log(format_data):
    sid = none_type_to_str(format_data.get("sid"))
    operation = none_type_to_str(format_data.get("operation"))
    object = none_type_to_str(format_data.get("object"))
    start_time = none_type_to_str(format_data.get("start_time"))
    end_time = none_type_to_str(format_data.get("end_time"))

    user_logs = User_log.query.filter(
        User_log.sid == sid if sid is not None else True,
        User_log.operation == operation if operation is not None else True,
        User_log.object.like("%{keyword}%".format(keyword=object)) if object is not None else True,
        User_log.addtime >= start_time if start_time is not None else True,
        User_log.addtime <= end_time if end_time is not None else True,
    ).order_by(User_log.addtime.desc())
    user_logs = user_logs.paginate(page=format_data.get('page'), per_page=format_data.get('per_page'), error_out=False)
    return user_logs


def check_user_log_data(data):
    uid = data.get("uid")
    operation = data.get("operation")
    object = data.get("object")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    per_page = data.get('per_page')
    page = data.get('page')
    if per_page is None:
        per_page = 20
    if page is None:
        page = 1

    data = ImmutableMultiDict(data).to_dict()
    data['per_page'] = per_page
    data['page'] = page

    if uid is not None and not check_uid_format(uid):
        return make_json({}, 400, "用户id格式错误"), False
    if operation is not None and not check_user_operation_format(operation):
        return make_json({}, 400, "操作代号格式错误"), False
    if object is not None and not check_object_format(object):
        return make_json({}, 400, "操作对象格式错误"), False
    if start_time is not None and not check_time_format(start_time):
        return make_json({}, 400, "开始操作时间格式错误"), False
    if end_time is not None and not check_time_format(end_time):
        return make_json({}, 400, "结束操作时间格式错误"), False

    return data, True


def check_adminname_format(adminname):
    if not len_is_between(adminname, 1, 50):
        return False
    return True


def user_op_to_data(op):
    index = op % 2000
    return ManageOrder.USER_OP_TO_STRING[index]


def admin_op_to_data(op):
    index = op % 5000
    return ManageOrder.ADMIN_OP_TO_STRING[index]


def check_admin_log_data(data):
    adminname = data.get("adminname")
    operation = data.get("operation")
    object = data.get("object")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    per_page = data.get('per_page')
    page = data.get('page')
    if per_page is None:
        per_page = 20
    if page is None:
        page = 1

    data = ImmutableMultiDict(data).to_dict()
    data['per_page'] = per_page
    data['page'] = page

    if adminname is not None and not check_adminname_format(adminname):
        return make_json({}, 400, "管理员用户名格式错误"), False
    if operation is not None and not check_admin_operation_format(operation):
        return make_json({}, 400, "操作代号格式错误"), False
    if object is not None and not check_object_format(object):
        return make_json({}, 400, "操作对象格式错误"), False
    if start_time is not None and not check_time_format(start_time):
        return make_json({}, 400, "开始操作时间格式错误"), False
    if end_time is not None and not check_time_format(end_time):
        return make_json({}, 400, "结束操作时间格式错误"), False

    return data, True


def user_log_detail(log):
    temp_log = {
        "id": log.id,
        "sid": log.sid,
        "operation": user_op_to_data(log.operation),
        "object": log.object if log.object is not None else "",
        "time": datetime.strftime(log.addtime, "%Y-%m-%d %H:%M:%S"),
    }

    return temp_log


def admin_log_detail(log):
    admin_log_temp = {
        "id": log.id,
        "adminname": log.adminname,
        "operation": admin_op_to_data(log.operation),
        "object": log.object if log.object is not None else "",
        "time": datetime.strftime(log.addtime, "%Y-%m-%d %H:%M:%S"),
    }

    return admin_log_temp


def add_admin_log(adminname, code, objects=None):
    if objects is None:
        log = Admin_log(adminname=adminname, operation=code)
    else:
        log = Admin_log(adminname=adminname, operation=code, object=objects)
    db.session.add(log)
    db.session.commit()


def medal_one_check(id):
    user = User.query.filter_by(id=id).first()
    if user is not None:
        if user.total_borrowed >= ManageOrder.MEDAL_1_NUM:
            print(user.total_borrowed)
            try:
                um = User_Medal(uid=user.id, mid=ManageOrder.MEDAL_1)
                db.session.add(um)
                db.session.commit()
                return True
            except Exception as e:
                print("Error:", e.args)
                return False

    return False


def medal_two_check(id):
    user = User.query.filter_by(id=id).first()
    if user is not None:
        book_num = user.total_borrowed - user.overtime_borrowed
        if book_num < ManageOrder.MEDAL_2_NUM:
            return False

        unreturn_book = db.session.query(func.count(Borrow.uid).label('sums')).filter(Borrow.uid == user.id).group_by(
            Borrow.uid).first()
        if unreturn_book is not None:
            num = book_num - unreturn_book.sums
            if num >= ManageOrder.MEDAL_2_NUM:
                try:
                    medal2 = User_Medal(uid=user.id, mid=ManageOrder.MEDAL_2)
                    db.session.add(medal2)
                    db.session.commit()
                    return True
                except Exception as e:
                    print("Error:", e.args)
                    return False
    return False
