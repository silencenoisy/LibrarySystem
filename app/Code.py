class ManageOrder(object):
    # REGISTER = 2000
    USER_OP_TO_STRING = ["登录","修改密码","修改信息","登出","借书","还书","添加评论","删除评论"]
    USER_LOGIN_OP = 2000
    CHANGE_PWD = 2001
    CHANGE_INFO = 2002
    LOGOUT = 2003
    BORROW_BOOK = 2004
    RETURN_BOOK = 2005
    ADD_COMMENT = 2006
    DELETE_COMMENT = 2007

    # 管理员操作代码
    ADMIN_OP_TO_STRING = ["登录", "登出", "修改书籍", "添加书籍", "删除书籍", "用户修改", "用户删除", "用户添加",
                    "评论删除", "评论修改", "标签修改", "标签添加", "标签删除"]
    ADMIN_LOGIN_OP = 5000
    ADMIN_LOGOUT_OP = 5001
    ADMIN_MODIFY_BOOK_OP = 5002
    ADMIN_ADD_BOOK_OP = 5003
    ADMIN_DELETE_BOOK_OP = 5004
    ADMIN_MODIFY_USER_OP = 5005
    ADMIN_DELETE_USER_OP = 5006
    ADMIN_ADD_USER_OP = 5007
    ADMIN_DELETE_COMMENT_OP = 5008
    ADMIN_MODIFY_COMMENT_OP = 5009
    ADMIN_MODIFY_TAG_OP = 5010
    ADMIN_ADD_TAG_OP = 5011
    ADMIN_DELETE_TAG_OP = 5012

    # 勋章id
    MEDAL_1 = 1 # 累计借书达50本
    MEDAL_2 = 2 # 累计按时还书达20本
    MEDAL_3 = 3

    MEDAL_1_NUM = 2 #
    MEDAL_2_NUM = 1



