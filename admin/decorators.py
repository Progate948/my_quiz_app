from functools import wraps
from flask import abort
from flask_login import current_user
from flask import current_app

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # 未認証の場合はログインページへリダイレクトされる (Flask-Loginのデフォルト動作)
            # ここで直接 abort(401) や redirect(url_for('login')) も可能
            return current_app.login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)  # Forbidden - 認証済みだが権限なし
        return f(*args, **kwargs)
    return decorated_function
