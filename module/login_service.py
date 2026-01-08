from database.db import get_db

def authenticate_user(login_id: str, login_password: str):
    conn = get_db()
    return conn.execute(
        "SELECT user_name FROM user WHERE login_id = ? AND login_password = ? ",
        (login_id, login_password),
    ).fetchone()
