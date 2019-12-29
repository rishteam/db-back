from sqlalchemy import text

from db import db

# TODO(roy4801): implement this in the future

def get_user(uid):
    """Returns a user from table `user`"""
    res = db.session.execute(text('''
        SELECT * FROM user WHERE uid=:uid
    '''), {'uid': uid})
    if res.rowcount:
        return res.fetchone()
    else:
        return None
