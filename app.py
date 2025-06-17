from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
import os
import random
import datetime
from datetime import timedelta
import pytz

from models import db, User, Question, UserAnswer, UserCheck
from admin import admin_bp
from admin.routes import setup_admin_upload_folder
from forms import RegistrationForm, LoginForm, QuestionForm, EditProfileForm

app = Flask(__name__)

# --- Configuration ---
instance_folder_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'instance'
)
if not os.path.exists(instance_folder_path):
    os.makedirs(instance_folder_path)

database_uri = os.environ.get('DATABASE_URL')
if database_uri and database_uri.startswith("postgres://"):
    database_uri = database_uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri or 'sqlite:///' + os.path.join(instance_folder_path, 'quiz_app.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-key-for-dev-only')
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

# --- Extensions Initialization ---
csrf = CSRFProtect(app)
db.init_app(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "このページにアクセスするにはログインが必要です。"
login_manager.login_message_category = "info"

# --- Blueprint Registration ---
app.register_blueprint(admin_bp)

# --- Custom Filters ---
@app.template_filter('to_jst_str')
def to_jst_str_filter(dt):
    if dt is None: return ""
    utc_dt = dt.replace(tzinfo=pytz.utc)
    jst_dt = utc_dt.astimezone(pytz.timezone('Asia/Tokyo'))
    return jst_dt.strftime('%Y-%m-%d %H:%M')

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.date.today().year}

# --- Helper Functions ---
def get_dynamic_ranges(range_size=5):
    with app.app_context():
        max_id = db.session.query(func.max(Question.id)).scalar() or 0
        if max_id == 0:
            return {}
        ranges = {}
        start_id_loop = 1
        while start_id_loop <= max_id:
            end_id = min(start_id_loop + range_size - 1, max_id)
            count = Question.query.filter(Question.id.between(start_id_loop, end_id)).count()
            if count > 0:
                range_key = f'range_{start_id_loop}_{end_id}'
                if start_id_loop == end_id:
                    range_name = f'No.{start_id_loop}'
                else:
                    range_name = f'No.{start_id_loop} ~ No.{end_id}'
                ranges[range_key] = {'name': range_name}
            start_id_loop += range_size
    return ranges

# --- Constants ---
REVIEW_MODE_KEY = 'review_mode'
REVIEW_TYPE_KEY = 'review_type'
EXAM_MODE_KEY = 'is_exam_mode'

# --- Flask-Login User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- CLI Commands ---
def seed_initial_data():
    if not Question.query.first():
        questions_data = [
            {"id": 1, "text": "日本の首都はどこですか？", "options": ["東京", "大阪", "京都", "札幌"], "answer": ["東京"], "explanation": "東京は日本の政治、経済、文化の中心地です。", "image": None},
            {"id": 2, "text": "Pythonの主要なWebフレームワークはFlaskと何ですか？", "options": ["Node.js", "Django", "Ruby on Rails", "PHP"], "answer": ["Django"], "explanation": "Djangoは、Pythonのもう一つのフルスタックなWebフレームワークです。", "image": "images/image_e0a79a.jpg"},
            {"id": 3, "text": "HTMLは何の略ですか？", "options": ["High-Tech Markup Language", "HyperText Markup Language", "Home Tool Markup Language", "Hyperlink and Text Markup Language"], "answer": ["HyperText Markup Language"], "explanation": "HTMLはWebページの構造を記述するための言語です。", "image": None},
            {"id": 4, "text": "TCP/IPモデルで、HTTPプロトコルが動作するのはどの層ですか？", "options": ["ネットワーク層", "トランスポート層", "アプリケーション層", "データリンク層"], "answer": ["アプリケーション層"], "explanation": "HTTPはTCP/IPの最上位層であるアプリケーション層で動作します。", "image": None},
            {"id": 5, "text": "MACアドレスは何ビットで構成されますか？", "options": ["16ビット", "32ビット", "48ビット", "64ビット"], "answer": ["48ビット"], "explanation": "MACアドレスは、ネットワークインターフェースに割り当てられる物理アドレスで、48ビット（6バイト）です。", "image": None},
            {"id": 6, "text": "Webページのスタイルを指定する言語は何ですか？", "options": ["HTML", "JavaScript", "CSS", "Python"], "answer": ["CSS"], "explanation": "CSS（Cascading Style Sheets）はWebページのスタイルを指定するための言語です。", "image": None},
            {"id": 7, "text": "HTTPステータスコード200は何を意味しますか？", "options": ["リクエストエラー", "サーバーエラー", "成功", "リダイレクト"], "answer": ["成功"], "explanation": "HTTPステータスコード200は「OK」を意味し、リクエストが成功したことを示します。", "image": None},
            {"id": 8, "text": "Gitで変更を記録するコマンドは何ですか？", "options": ["git push", "git pull", "git commit", "git clone"], "answer": ["git commit"], "explanation": "git commitは、ローカルリポジトリに変更を記録するために使われます。", "image": None},
            {"id": 9, "text": "データベースにおける「行」の別名は何ですか？", "options": ["カラム", "テーブル", "レコード", "フィールド"], "answer": ["レコード"], "explanation": "データベースのテーブルにおける行はレコード、列はフィールド（またはカラム）と呼ばれます。", "image": None},
            {"id": 10, "text": "プログラミングで条件分岐を行う際に使用されるキーワードは何ですか？", "options": ["loop", "function", "if", "array"], "answer": ["if"], "explanation": "if文は、条件に基づいて異なる処理を実行するために使われます。", "image": None},
            {"id": 11, "text": "ポート番号80を使用するプロトコルは何ですか？", "options": ["HTTPS", "FTP", "SSH", "HTTP"], "answer": ["HTTP"], "explanation": "HTTPプロトコルはデフォルトでポート番号80を使用します。", "image": None},
            {"id": 12, "text": "データを永続的に保存するためのシステムは何ですか？", "options": ["RAM", "CPU", "データベース", "キャッシュ"], "answer": ["データベース"], "explanation": "データベースは大量のデータを効率的に管理し、永続的に保存するためのシステムです。", "image": None},
            {"id": 13, "text": "Pythonのパッケージ管理システムは何ですか？", "options": ["npm", "RubyGems", "pip", "Composer"], "answer": ["pip"], "explanation": "pipはPythonの公式パッケージ管理ツールです。", "image": None},
            {"id": 14, "text": "JavaScriptで要素を取得するDOMメソッドの1つは何ですか？", "options": ["getElementById", "get_element_by_id", "selectElement", "queryElement"], "answer": ["getElementById"], "explanation": "JavaScriptのdocument.getElementById()は、IDを指定して要素を取得します。", "image": None},
            {"id": 15, "text": "WebブラウザでHTML、CSS、JavaScriptを実行するものは何ですか？", "options": ["サーバー", "インタープリタ", "レンダリングエンジン", "コンパイラ"], "answer": ["レンダリングエンジン"], "explanation": "Webブラウザ内のレンダリングエンジンがこれらのファイルを解析し、表示します。", "image": None}
        ]
        for data in questions_data:
            question = Question(
                id=data.get('id'), 
                question_text=data.get('text'), 
                options=data.get('options'), 
                correct_answer=data.get('answer'),
                explanation=data.get('explanation'), 
                image_filename=data.get('image')
            )
            db.session.add(question)
        print('INFO: Initial question data loaded.')
    db.session.commit()

@app.cli.command("seed-db")
def seed_db_command():
    seed_initial_data()
    print("Database seeded with questions.")

@app.cli.command("create-admin")
def create_admin_command():
    """管理者ユーザーを作成します。"""
    if User.query.filter_by(username='admin').first():
        print('INFO: Admin user already exists.')
        return
    admin_user = User(username='admin', email='admin@example.com', is_admin=True)
    admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'defaultadminpass'))
    db.session.add(admin_user)
    db.session.commit()
    print('SUCCESS: Admin user created.')

# --- ルート定義 ---
@app.route('/question/<int:question_id>')
@login_required
def show_question(question_id):
    question = Question.query.get_or_404(question_id)
    options_list = question.options
    correct_answers_list = question.correct_answer 
    is_multi_select_question = isinstance(correct_answers_list, list) and len(correct_answers_list) > 1
    
    # ... (以下のロジックは変更なし)
    quiz_order_ids = session.get('quiz_order_ids', [])
    total_questions = len(quiz_order_ids)
    current_question_index_in_order = session.get('current_question_index_in_order', 0)
    display_question_number = current_question_index_in_order + 1

    display_correct_count = 0
    display_total_answered = 0
    display_accuracy = 0.0
    if not session.get(REVIEW_MODE_KEY) and not session.get(EXAM_MODE_KEY):
        display_correct_count = session.get('correct_count', 0)
        display_total_answered = session.get('total_questions_answered', 0)
        if display_total_answered > 0:
            display_accuracy = (display_correct_count / display_total_answered * 100)
    
    checked_status = {'type1': False, 'type2': False, 'type3': False}
    if current_user.is_authenticated:
        user_id = current_user.id
        for check_type_key in checked_status.keys():
            existing_check = UserCheck.query.filter_by(user_id=user_id, question_id=question_id, check_type=check_type_key).first()
            if existing_check and existing_check.is_checked:
                checked_status[check_type_key] = True

    last_answer_result = session.pop('last_answer_result', None) 
    last_user_answer = session.pop('last_user_answer', None)     
    
    return render_template('question.html',
                           question=question,
                           options=options_list,
                           total_questions=total_questions,
                           current_question_index=display_question_number,
                           correct_count=display_correct_count,
                           total_answered=display_total_answered,
                           accuracy=f"{display_accuracy:.1f}",
                           checked_status=checked_status,
                           last_answer_result=last_answer_result,
                           last_user_answer=last_user_answer,
                           is_multi_select_question=is_multi_select_question)

@app.route('/answer', methods=['POST'])
@login_required
def handle_answer():
    if session.get(EXAM_MODE_KEY):
        end_time_str = session.get('exam_end_time')
        if end_time_str:
            end_time = datetime.datetime.fromisoformat(end_time_str)
            if datetime.datetime.now(pytz.utc) > end_time:
                flash("時間切れです！試験を終了します。", "warning")
                return redirect(url_for('submit_exam'))

    user_selected_options = request.form.getlist('selected_option')
    question_id = request.form.get('question_id', type=int)

    if not user_selected_options or question_id is None:
        flash("解答が選択されていないか、問題IDが不明です。", "warning")
        return redirect(request.referrer or url_for('quiz_range_select'))

    question = Question.query.get_or_404(question_id)
    correct_answers_list = question.correct_answer

    is_correct = (set(user_selected_options) == set(correct_answers_list))
    
    correct_answer_for_display = " & ".join(map(str, correct_answers_list))

    if current_user.is_authenticated:
        user_id = current_user.id
        new_user_answer = UserAnswer(
            user_id=user_id,
            question_id=question.id,
            user_selected_option=user_selected_options,
            is_correct=is_correct
        )
        db.session.add(new_user_answer)
        db.session.commit()
    
    session['last_answer_result'] = {
        'is_correct': is_correct,
        'message': "正解！" if is_correct else "不正解！",
        'correct_answer': correct_answer_for_display,
        'explanation': question.explanation
    }
    session['last_user_answer'] = " & ".join(user_selected_options)

    return redirect(url_for('show_question', question_id=question_id))


@app.route('/next_question')
@login_required # ★★★ 修正箇所 ★★★
def next_question():
    if session.get(EXAM_MODE_KEY):
        end_time_str = session.get('exam_end_time')
        if end_time_str:
            end_time = datetime.datetime.fromisoformat(end_time_str)
            if datetime.datetime.now(pytz.utc) > end_time:
                flash("時間切れです！試験を終了します。", "warning")
                return redirect(url_for('submit_exam'))

    quiz_order_ids = session.get('quiz_order_ids', [])
    current_index = session.get('current_question_index_in_order', -1)
    next_index = current_index + 1
    
    session.pop('last_answer_result', None) 
    session.pop('last_user_answer', None)

    if next_index < len(quiz_order_ids):
        next_question_id = quiz_order_ids[next_index]
        session['current_question_index_in_order'] = next_index
        return redirect(url_for('show_question', question_id=next_question_id))
    else:
        if session.get(EXAM_MODE_KEY):
            return redirect(url_for('submit_exam'))
        
        review_mode = session.pop(REVIEW_MODE_KEY, None)
        review_type = session.pop(REVIEW_TYPE_KEY, None)
        
        correct_count_for_completion = session.pop('correct_count', 0)
        total_answered = session.pop('total_questions_answered', 0)
        session.pop('current_question_index_in_order', None)
        session.pop('quiz_order_ids', None)
        session.pop('answered_question_ids', None)
        session.pop('current_range_key', None)
        
        if review_mode:
            flash_message = "復習が完了しました。"
            target_url = url_for('quiz_range_select')
            if review_type == 'incorrect':
                flash_message = '間違えた問題の復習が完了しました。'
                target_url = url_for('review_incorrect')
            elif review_type and review_type.startswith('checked_'):
                flash_message = 'チェック問題の復習が完了しました。'
                target_url = url_for('my_checked_questions_by_type', check_type=review_type.replace('checked_', ''))
            flash(flash_message, 'info')
            return redirect(target_url)
        else:
            return redirect(url_for('quiz_completion', correct_count=correct_count_for_completion, total_answered=total_answered))

@app.route('/submit_exam')
@login_required # ★★★ 修正箇所 ★★★
def submit_exam():
    if not session.get(EXAM_MODE_KEY):
        return redirect(url_for('quiz_range_select'))

    correct_count = session.get('correct_count', 0)
    total_answered = session.get('total_questions_answered', 0)
    total_questions_in_exam = len(session.get('quiz_order_ids', []))

    session.pop(EXAM_MODE_KEY, None)
    session.pop('exam_end_time', None)
    session.pop('correct_count', None)
    session.pop('total_questions_answered', None)
    session.pop('answered_question_ids', None)
    session.pop('current_range_key', None)
    session.pop('quiz_order_ids', None)
    session.pop('current_question_index_in_order', None)

    return redirect(url_for(
        'quiz_completion',
        correct_count=correct_count,
        total_answered=total_questions_in_exam,
        answered_count=total_answered,
        exam_completed=True
    ))


@app.route('/quiz_completion')
@login_required # ★★★ 修正箇所 ★★★
def quiz_completion():
    correct_count = request.args.get('correct_count', type=int)
    total_answered = request.args.get('total_answered', type=int)
    answered_count = request.args.get('answered_count', type=int)
    exam_completed = request.args.get('exam_completed', type=bool, default=False)

    if correct_count is None or total_answered is None:
        flash("結果を表示できませんでした。", "warning")
        return redirect(url_for('quiz_range_select'))
        
    return render_template('completion.html', 
                           correct_count=correct_count, 
                           total_answered=total_answered,
                           answered_count=answered_count,
                           exam_completed=exam_completed)


@app.route('/review_incorrect')
@login_required
def review_incorrect():
    user_id = current_user.id
    incorrect_answers_raw = UserAnswer.query.filter_by(user_id=user_id, is_correct=False).order_by(UserAnswer.timestamp.desc()).all()
    
    reviewed_questions = []
    seen_question_ids = set()
    for ua in incorrect_answers_raw:
        if ua.question_id not in seen_question_ids:
            if ua.question_detail:
                # ▼▼▼ json.loads() を削除 ▼▼▼
                user_selected_display = " & ".join(map(str, ua.user_selected_option)) if ua.user_selected_option else ""
                correct_answer_display = " & ".join(map(str, ua.question_detail.correct_answer)) if ua.question_detail.correct_answer else ""
                reviewed_questions.append({
                    'question': ua.question_detail,
                    'user_selected_option': user_selected_display,
                    'correct_answer_display': correct_answer_display,
                })
                seen_question_ids.add(ua.question_id)
    return render_template('review_incorrect.html', reviewed_questions=reviewed_questions)

@app.route('/api/toggle_check', methods=['POST'])
@login_required
def toggle_check():
    data = request.get_json()
    question_id = data.get('question_id')
    if question_id is not None:
        question_id = int(question_id)
    check_type = data.get('check_type')
    user_id = current_user.id

    allowed_check_types = ['type1', 'type2', 'type3']
    if check_type not in allowed_check_types or question_id is None:
        return jsonify({'status': 'error', 'message': '無効なパラメータです。'}), 400

    existing_check = UserCheck.query.filter_by(user_id=user_id, question_id=question_id, check_type=check_type).first()

    if existing_check:
        db.session.delete(existing_check)
        db.session.commit()
        return jsonify({'status': 'success', 'checked': False, 'question_id': question_id, 'check_type': check_type}), 200
    else:
        new_check = UserCheck(user_id=user_id, question_id=question_id, check_type=check_type, is_checked=True)
        db.session.add(new_check)
        db.session.commit()
        return jsonify({'status': 'success', 'checked': True, 'question_id': question_id, 'check_type': check_type}), 200

@app.route('/my_checked_questions/<string:check_type>')
@login_required
def my_checked_questions_by_type(check_type):
    user_id = current_user.id
    check_type_display_names = {'type1': '重要（緑）', 'type2': '苦手（オレンジ）', 'type3': '後で（ピンク）'}
    if check_type not in check_type_display_names:
        abort(404)

    checked_entries = UserCheck.query.join(Question).filter(UserCheck.user_id == user_id, UserCheck.check_type == check_type, UserCheck.is_checked == True)\
                                  .order_by(UserCheck.timestamp.desc()).all()
    
    checked_questions_data = []
    for entry in checked_entries:
        if entry.question_detail:
            # ▼▼▼ json.loads() を削除 ▼▼▼
            correct_answer_display = " & ".join(map(str, entry.question_detail.correct_answer)) if entry.question_detail.correct_answer else ""
            checked_questions_data.append({
                'question': entry.question_detail,
                'correct_answer_display': correct_answer_display,
                'check_type': entry.check_type
            })
    
    return render_template('my_checked_questions.html',
                           checked_questions=checked_questions_data,
                           current_check_type=check_type)


@app.route('/checked_questions_overview')
@login_required
def checked_questions_overview():
    user_id = current_user.id
    check_counts = {}
    check_type_display_names = {'type1': '重要（緑）', 'type2': '苦手（オレンジ）', 'type3': '後で（ピンク）'}
    
    for key, name in check_type_display_names.items():
        count = UserCheck.query.filter_by(user_id=user_id, check_type=key, is_checked=True).count()
        check_counts[key] = {'name': name, 'count': count}
    
    return render_template('checked_questions_overview.html', check_counts=check_counts)


@app.route('/reset_my_progress', methods=['POST'])
@login_required
def reset_my_progress():
    user_id = current_user.id
    UserAnswer.query.filter_by(user_id=user_id).delete()
    UserCheck.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    session.pop('correct_count', None)
    session.pop('total_questions_answered', None)
    session.pop('answered_question_ids', None)
    session.pop('current_range_key', None)
    session.pop('quiz_order_ids', None)
    session.pop('current_question_index_in_order', None)
    session.pop('last_answer_result', None) 
    session.pop('last_user_answer', None)
    session.pop(REVIEW_MODE_KEY, None)
    session.pop(REVIEW_TYPE_KEY, None)
    
    flash('あなたの学習進捗をリセットしました。', 'success')
    return redirect(url_for('quiz_range_select'))


@app.route('/retry_question/<int:question_id>')
@login_required # ★★★ 修正箇所 ★★★
def retry_question(question_id):
    _ = Question.query.get_or_404(question_id)

    session.pop(REVIEW_MODE_KEY, None)
    session.pop(REVIEW_TYPE_KEY, None)
    session.pop('correct_count', None)
    session.pop('total_questions_answered', None)
    session.pop('answered_question_ids', None)
    session.pop('last_answer_result', None) 
    session.pop('last_user_answer', None)

    session['quiz_order_ids'] = [question_id]
    session['current_question_index_in_order'] = 0
    session['current_range_key'] = f'retry_{question_id}'

    return redirect(url_for('show_question', question_id=question_id))


@app.route('/review_all_incorrect')
@login_required
def review_all_incorrect():
    user_id = current_user.id
    incorrect_question_ids = [
        ua.question_id for ua in 
        UserAnswer.query.filter_by(user_id=user_id, is_correct=False)\
                        .with_entities(UserAnswer.question_id).distinct().all()
    ]
    
    if not incorrect_question_ids:
        flash("復習対象の間違えた問題はありません。", "info")
        return redirect(url_for('review_incorrect'))

    random.shuffle(incorrect_question_ids)

    session.pop('correct_count', None)
    session.pop('total_questions_answered', None)
    session.pop('answered_question_ids', None)
    session.pop('current_range_key', None)
    session.pop('last_answer_result', None) 
    session.pop('last_user_answer', None)

    session['quiz_order_ids'] = incorrect_question_ids
    session['current_question_index_in_order'] = 0
    session[REVIEW_MODE_KEY] = True
    session[REVIEW_TYPE_KEY] = 'incorrect'

    return redirect(url_for('show_question', question_id=incorrect_question_ids[0]))


@app.route('/review_all_checked/<string:check_type>')
@login_required
def review_all_checked(check_type):
    user_id = current_user.id
    allowed_check_types = ['type1', 'type2', 'type3']
    if check_type not in allowed_check_types:
        abort(404)

    checked_question_ids = [
        uc.question_id for uc in 
        UserCheck.query.filter_by(user_id=user_id, check_type=check_type, is_checked=True)\
                       .with_entities(UserCheck.question_id).distinct().all()
    ]

    if not checked_question_ids:
        flash(f"このタイプのチェック問題はありません。", "info")
        return redirect(url_for('my_checked_questions_by_type', check_type=check_type))

    random.shuffle(checked_question_ids)

    session.pop('correct_count', None)
    session.pop('total_questions_answered', None)
    session.pop('answered_question_ids', None)
    session.pop('current_range_key', None)
    session.pop('last_answer_result', None) 
    session.pop('last_user_answer', None)

    session['quiz_order_ids'] = checked_question_ids
    session['current_question_index_in_order'] = 0
    session[REVIEW_MODE_KEY] = True
    session[REVIEW_TYPE_KEY] = f'checked_{check_type}'

    return redirect(url_for('show_question', question_id=checked_question_ids[0]))


if __name__ == '__main__':
    app.run(debug=True)