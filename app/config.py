import os
import pymysql
class Config(object):
    # dsn = "Provider=ODBC Driver 17 for SQL Server;Data Source=47.99.169.188,1433;Initial Catalog=LibraryApp;User ID=sa;Password=yrd00929.;"
    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://username:password@ODBCname' # please change this config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    XD_USER_DIR = "static/upload/users"
    XD_BOOK_DIR = "static/upload/books"
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), XD_USER_DIR)
    UPLOAD_FOLDER_BOOK = os.path.join(os.path.abspath(os.path.dirname(__file__)), XD_BOOK_DIR)
    DEFAULT_USER_FACE = UPLOAD_FOLDER+"/default_face.png"
    DEFAULT_USER_FACE_GET = "/" + XD_USER_DIR + "/default_face.png"
    DEFAULT_BOOK_COVER = UPLOAD_FOLDER_BOOK + "/default_cover.png"
    DEFAULT_BOOK_COVER_GET = "/"+XD_BOOK_DIR + "/default_cover.png"
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

    EXPIRES_IN = 36000
    SECRET_KEY = 'pig'
    SECRET_KEY_ADMIN = "dog"
    RATING_PATH = "./bookdatasets/Books_min.csv"

