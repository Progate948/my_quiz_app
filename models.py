from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.types import JSON 

# app.py で初期化された db インスタンスをインポートすることを想定
# ただし、直接 app.py からインポートすると循環参照になるため、
# app.py 側で db = SQLAlchemy() を行い、このファイルが読み込まれる前に
# その db インスタンスがグローバルスコープに存在し、
# モデルクラスが定義される際にその db を利用する形にする。
# もしくは、db をこのファイル内で初期化し、app.py でそれを共有する。
# ここでは、app.py で db を初期化し、このファイルでそれを利用する前提で進める。
# そのため、このファイルのトップレベルでの from app import db のような記述はせず、
# app.py 側でこのファイルがインポートされる際に db が解決されることを期待する。

# より堅牢なのは、my_quiz_app/__init__.py などで db を初期化し、
# このファイルと app.py (ルーティングファイル) の両方がそれをインポートする形。

# 今回は、app.py で db = SQLAlchemy() を行い、
# この models.py では、その db を使ってモデルを定義する。
# そのため、このファイル自体には db の初期化コードは書かない。
# app.py 側で、db の初期化後にこのファイルがインポートされるようにする。

# グローバルな `db` オブジェクトを期待する
# この `db` は `app.py` で `db = SQLAlchemy()` によって作成される
# そして、`app.py` が `from .models import ...` を実行する前に `db` が存在している必要がある。
# 実際には、db = SQLAlchemy() は models.py の中で行うか、
# もしくは app.py で行い、models.py に渡すか、
# my_quiz_app/__init__.py で行うのが一般的。

# ここでは、app.py で db = SQLAlchemy() を宣言し、
# models.py はその db を使ってクラスを定義すると仮定する。
# そして、app.py は app = Flask() の後、db.init_app(app) を行い、
# その後 from .models import ... とする。

# これにより、models.py は SQLAlchemy の db オブジェクトを必要とするが、
# その実体は app.py で与えられる。

# SQLAlchemyインスタンスをここで生成する方が循環参照を避けやすい。
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user' # 明示的にテーブル名を指定 (推奨)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    is_admin = db.Column(db.Boolean, nullable=False, default=False) # 管理者フラグ

    answers = db.relationship('UserAnswer', backref='user', lazy='dynamic')
    checks = db.relationship('UserCheck', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Question(db.Model):
    __tablename__ = 'question' # 明示的にテーブル名を指定
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(JSON, nullable=False)
    correct_answer = db.Column(JSON, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)

    # UserAnswerとの関連 (Questionから見て多)
    user_answers = db.relationship('UserAnswer', backref='question_detail', lazy='dynamic')
    # UserCheckとの関連 (Questionから見て多)
    user_checks = db.relationship('UserCheck', backref='question_detail', lazy='dynamic')


    def __repr__(self):
        return f'<Question {self.id}>'

class UserAnswer(db.Model):
    __tablename__ = 'user_answer' # 明示的にテーブル名を指定
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_selected_option = db.Column(JSON, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # User モデルとの関連は User.answers で定義済み (backref='user')
    # Question モデルとの関連。backref名を変更して衝突を避ける
    # question = db.relationship('Question', backref='user_answers_on_question', lazy=True) # Question.user_answers と重複するため修正

    def __repr__(self):
        return f'<UserAnswer {self.id} (User:{self.user_id}, Q:{self.question_id}, Correct:{self.is_correct})>'

class UserCheck(db.Model):
    __tablename__ = 'user_check' # 明示的にテーブル名を指定
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    check_type = db.Column(db.String(50), nullable=False)
    is_checked = db.Column(db.Boolean, default=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'question_id', 'check_type', name='_user_question_check_uc'),)
    # User モデルとの関連は User.checks で定義済み (backref='user')
    # Question モデルとの関連。backref名を変更して衝突を避ける
    # question = db.relationship('Question', backref='user_checks_on_question', lazy=True) # Question.user_checks と重複するため修正


    def __repr__(self):
        return f'<UserCheck {self.id} (User:{self.user_id}, Q:{self.question_id}, Type:{self.check_type}, Checked:{self.is_checked})>'

