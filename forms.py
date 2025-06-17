from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from models import User # models.py から User をインポート
from wtforms import StringField, TextAreaField, SubmitField, FileField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Optional # Optionalバリデータを追加
from flask_wtf.file import FileAllowed, FileRequired # FileRequiredは新規追加時など
from flask_login import current_user
# (以降のフォームクラス定義は変更なし)

class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    password2 = PasswordField(
        'パスワード（確認）', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('登録')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('このユーザー名は既に使用されています。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('このメールアドレスは既に使用されています。')

class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を記憶する')
    submit = SubmitField('ログイン')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('問題文', validators=[DataRequired()])
    # 選択肢はカンマ区切りで入力し、ビュー側でパースしてJSONリストとして保存
    options_text = StringField('選択肢 (カンマ区切りで入力)', 
                               validators=[DataRequired()], 
                               description="例: 東京, 大阪, 京都")
    # 正解もカンマ区切りで入力 (選択肢のテキストと完全に一致させる)
    correct_answers_text = StringField('正解 (カンマ区切りで入力、選択肢と一致)', 
                                     validators=[DataRequired()],
                                     description="例: 東京, 京都 (複数正解の場合)")
    explanation = TextAreaField('解説')
    image = FileField('画像ファイル (任意)', 
                      validators=[
                          Optional(), # 画像は任意入力
                          FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '画像ファイルのみアップロード可能です！')
                      ])
    submit = SubmitField('保存')

class EditProfileForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('新しいパスワード', 
                             validators=[Optional()],
                             description='変更する場合のみ入力してください。')
    password2 = PasswordField('新しいパスワード（確認）', 
                              validators=[EqualTo('password', message='パスワードが一致しません。')])
    submit = SubmitField('更新する')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('このユーザー名は既に使用されています。')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('このメールアドレスは既に使用されています。')