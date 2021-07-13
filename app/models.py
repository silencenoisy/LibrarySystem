import random

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired

from app import db, Config
from datetime import datetime, timedelta


class User(db.Model):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sid = db.Column(db.String(9), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    face = db.Column(db.String(1024))
    institute = db.Column(db.String(50))
    username = db.Column(db.String(20), nullable=False)
    realname = db.Column(db.String(255), nullable=False)
    sex = db.Column(db.SmallInteger, nullable=False, default=0)
    birthday = db.Column(db.Date)
    email = db.Column(db.String(50))
    phone = db.Column(db.String(11))
    left_borrow = db.Column(db.SmallInteger, nullable=False, default=0)
    total_borrowed = db.Column(db.SmallInteger, nullable=False, default=0)
    overtime_borrowed = db.Column(db.SmallInteger, nullable=False, default=0)

    def hash_password(self, pwd):
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(pwd)

    def check_pwd(self, pwdd):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, pwdd)

    def generate_auth_token(self, expiration=600):
        s = Serializer(Config.SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def create_hash_pwd(pwd):
        from werkzeug.security import generate_password_hash
        return generate_password_hash(pwd)

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(Config.SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user

    @staticmethod
    def create_token(user_id):
        """
        生成token
        :param user_id: 用户id
        :return:
        """

        # 第一个参数是内部的私钥，这里写在配置信息里，如果只是测试可以写死
        # 第二个参数是有效期（秒）
        s = Serializer(Config.SECRET_KEY, expires_in=Config.EXPIRES_IN)
        # 接收用户id转换与编码
        token = s.dumps({"id": user_id}).decode('ascii')
        return token

    def __repr__(self):
        return "User:%s %s %s %d %d %d" % \
               (self.sid, self.username, self.realname, self.left_borrow,
                self.total_borrowed, self.overtime_borrowed)


class Book(db.Model):
    __tablename__ = "book"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(50), nullable=False, unique=True)
    title = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(255),nullable=False,default="佚名")
    publication = db.Column(db.String(255), nullable=False,default="未知")
    publish_time = db.Column(db.Date)
    isborrowed = db.Column(db.SmallInteger, nullable=False, default=0)
    cover_image = db.Column(db.String(255))

    def __repr__(self):
        return "Book:%s %s %s %s %s %s" % \
               (self.isbn, self.title, self.author, self.publication,
                self.publish_time, ("未借出" if self.isborrowed is 0 else "已借出"))


class Return(db.Model):
    __tablename__ = "return"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bid = db.Column(db.Integer,db.ForeignKey('book.id'), nullable=False)
    uid = db.Column(db.Integer,db.ForeignKey('user.id'), nullable=False)
    addtime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    borrow_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "Return:%d %d %s %s" % \
               (self.bid, self.uid, self.addtime, self.borrow_time)


class Borrow(db.Model):
    __tablename__ = "borrow"
    __table_args__ = {"extend_existing": True}
    bid = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    return_time = db.Column(db.DateTime, nullable=False)
    addtime = db.Column(db.DateTime, nullable=False, default=datetime.now)


    def __init__(self, bid, uid, addtime=0, time_give=30):
        if addtime == 0:
            self.return_times(datetime.now(),time_give)
        elif Borrow.is_datetime_format(addtime):
            self.return_times(addtime,time_give)
        else:
            raise ValueError("日期格式错误")
        self.bid = bid
        self.uid = uid

    def return_times(self, addtime, time_give):
        # start_time = datetime.strptime(addtime, "%Y-%m-%d %H:%M:%S")

        return_time = (addtime + (timedelta(days=time_give))).strftime("%Y-%m-%d %H:%M:%S")
        self.addtime = addtime.strftime("%Y-%m-%d %H:%M:%S")
        self.return_time = return_time
        print(type(return_time), return_time)


    @staticmethod
    def is_datetime_format(addtime):
        try:
            datetime.strftime(addtime, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            return False

    def __repr__(self):
        return "Borrow:%d %d %s %s" % (self.bid, self.uid, self.addtime, self.return_time)


class Comment(db.Model):
    __tablename__ = "comment"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bid = db.Column(db.Integer, db.ForeignKey('book.id'))
    uid = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment = db.Column(db.Text, nullable=False,default="")
    addtime = db.Column(db.DateTime, nullable=False, default=datetime.now)


    def __repr__(self):
        return "Comment:%d %d %s %s" % (self.bid, self.uid, self.comment, self.addtime)


class Medal(db.Model):
    __tablename__ = "medal"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return "Medal:%d %s" % (self.id, self.name)

class User_Medal(db.Model):
    __tablename__ = "user_medal"
    __table_args__ = {"extend_existing": True}
    uid = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    mid = db.Column(db.Integer, db.ForeignKey('medal.id'), primary_key=True)
    addtime = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return "User_Medal:%d %d %s" % (self.uid,self.mid,self.name)


class Tag(db.Model):
    __tablename__ = "tag"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return "Tag:%d %s" % (self.id, self.name)


class Book_Tag(db.Model):
    __tablename__ = "book_tag"
    __table_args__ = {"extend_existing": True}
    bid = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)

    def __repr__(self):
        return "Book_Tag:%d %d" % (self.bid,self.tid)


class Admin(db.Model):
    __tablename__ = "admin"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    power = db.Column(db.SmallInteger, nullable=False,default=0)

    def hash_password(self, pwd):
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(pwd)

    def check_pwd(self, pwdd):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, pwdd)

    def generate_auth_token(self, expiration=600):
        s = Serializer(Config.SECRET_KEY, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def create_hash_pwd(pwd):
        from werkzeug.security import generate_password_hash
        return generate_password_hash(pwd)

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(Config.SECRET_KEY_ADMIN)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        admin = Admin.query.get(data['id'])
        return admin

    @staticmethod
    def create_token(admin_id):
        """
        生成token
        :param admin_id: 管理员id
        :return:
        """

        # 第一个参数是内部的私钥，这里写在配置信息里，如果只是测试可以写死
        # 第二个参数是有效期（秒）
        s = Serializer(Config.SECRET_KEY_ADMIN, expires_in=Config.EXPIRES_IN)
        # 接收用户id转换与编码
        token = s.dumps({"id": admin_id}).decode('ascii')
        return token

    def __repr__(self):
        return "Admin:%s %s %s" % (self.id, self.username,self.power)

class User_log(db.Model):
    __tablename__ = "user_log"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sid = db.Column(db.Integer, nullable=False)
    operation = db.Column(db.SmallInteger, nullable=False)
    object = db.Column(db.Text)
    addtime = db.Column(db.DateTime, nullable=False, default=datetime.now)


    def __repr__(self):
        return "User_log:%d %s %d %s %s" % (self.id, self.sid,self.operation,self.object,self.addtime)

class Admin_log(db.Model):
    __tablename__ = "admin_log"
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    adminname = db.Column(db.Integer, nullable=False)
    operation = db.Column(db.SmallInteger, nullable=False)
    object = db.Column(db.Text)
    addtime = db.Column(db.DateTime, nullable=False, default=datetime.now)


    def __repr__(self):
        return "Admin_log:%d %s %d %s %s" % (self.id, self.adminname,self.operation,self.object,self.addtime)


if __name__ == "__main__":
    # db.drop_all() # 没事别用这句话，会炸
    # db.create_all()

    # user1 = User(sid="221900330",password=User.create_hash_pwd("221900330"),institute=r"数学与计算机科学",
    #              username="ZPX",realname="詹鹏翔",sex=1,birthday="2001-01-01",email="123456@qq.com",
    #              phone="12345678911",left_borrow=50)
    # db.session.add(user1)
    #
    # book1 = Book(isbn="7-12345-78",title="书名",author="作者",publication="出版社",publish_time=datetime.now().strftime("%Y-%m-%d"))
    # db.session.add(book1)

    # for i in range(190,200):
    #     x = random.randint(1,200)
    #     x1 = random.randint(1, 200)
    #     x2 = random.randint(1, 200)
    #     if x!=x1 and x1!=x2 and x!=x2:
    #     # y = random.randint(1,200)
    #         book = Book_Tag(bid=i,tid=x)
    #         book1 = Book_Tag(bid=i, tid=x1)
    #         book2 = Book_Tag(bid=i, tid=x2)
    #         db.session.add(book)
    #         db.session.add(book1)
    #         db.session.add(book2)
    #         db.session.commit()

    # books = Book_Tag.query.all()
    # print(len(books))
    # for b in books:
    #     # b.isborrowed = 0
    #     print(b)
    # book = Book(isbn="145613123",title="dasdsad")
    # print(book.id)
    # db.session.add(book)
    # print(book.id)
    # db.session.commit()
    # print(book.id)
    # medal = Medal(name="借阅达人")
    # medal2 = Medal(name="值得信赖的伙伴")
    # db.session.add(medal)
    # db.session.add(medal2)
    # db.session.commit()

    admin1 = Admin(username="admin",password="admin",power=999)
    # admin1 = Admin.query.filter_by(username="admin").first()
    admin1.password = Admin.create_hash_pwd("admin")
    db.session.add(admin1)

    # for i in range(20):
    #     medal = Medal(name="徽章测试"+str(i))
    #     db.session.add(medal)
    #     if i%3==0:
    #         user_medal = User_Medal(uid=1,mid=i+1)
    #         db.session.add(user_medal)
    # db.session.commit()
    # date = Borrow.query.all()
    # print([i for i in date])

    # date = Admin.query.all()
    # print([i for i in date])
    # borrow = Borrow(1,1)
    # db.session.add(borrow)

    # import pandas as pd
    # import numpy as np
    #
    # book_path = "../bookdatasets/Books.csv"
    #
    # book_data = pd.read_csv(book_path, low_memory=False, usecols=(0, 1, 2, 3, 4, 7))
    # book_data = np.array(book_data)
    # cnt=0
    # flag= 99999999
    # for i in book_data:
    #     if i[0] == "0060242388":
    #         flag = 1
    #
    #     flag-=1
    #     try:
    #         if(int(i[3])!=0) and flag<0:
    #             book = Book(isbn=i[0],title=i[1],author=i[2],publication=i[4],
    #                         publish_time=datetime(year=int(i[3]),month=1,day=1).strftime("%Y-%m-%d") if i[3]!="0" else None,cover_image=i[5])
    #             db.session.add(book)
    #             cnt += 1
    #             if cnt%500==0:
    #                 print(cnt)
    #                 db.session.commit()
    #                 print("success")
    #         else:
    #             pass
    #     except TypeError:
    #         print(i[0])
    db.session.commit()


    # testDate = Test1.query.filter().all()
    # for i in testDate:
    #     print(i)


