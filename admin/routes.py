from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
import json

from . import admin_bp
from .decorators import admin_required
# modelsとformsはアプリケーションルートからインポート
from models import db, Question
from forms import QuestionForm

UPLOAD_FOLDER_NAME = 'question_images'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# この関数は app.py の初期化処理ブロックで呼び出される
def setup_admin_upload_folder():
    upload_path_abs = os.path.join(current_app.static_folder, UPLOAD_FOLDER_NAME)
    if not os.path.exists(upload_path_abs):
        try:
            os.makedirs(upload_path_abs)
            # サーバー起動時のコンソールに表示される
            print(f"INFO: Created upload folder for admin: {upload_path_abs}")
        except Exception as e:
            print(f"ERROR: Could not create upload folder {upload_path_abs}: {e}")


@admin_bp.route('/')
@login_required
@admin_required
def index():
    return redirect(url_for('admin.list_questions'))

@admin_bp.route('/questions')
@login_required
@admin_required
def list_questions():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    questions_pagination = Question.query.order_by(Question.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    questions = questions_pagination.items
    return render_template('admin_questions.html', title='問題管理', questions=questions, pagination=questions_pagination)

@admin_bp.route('/question/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question():
    form = QuestionForm()
    if form.validate_on_submit():
        try:
            options_list = [opt.strip() for opt in form.options_text.data.split(',') if opt.strip()]
            if not options_list: raise ValueError("選択肢は1つ以上入力してください。")
            options_json = json.dumps(options_list)

            correct_answers_list = [ans.strip() for ans in form.correct_answers_text.data.split(',') if ans.strip()]
            if not correct_answers_list: raise ValueError("正解は1つ以上入力してください。")
            for ca in correct_answers_list:
                if ca not in options_list:
                    raise ValueError(f"正解 '{ca}' は選択肢の中に存在しません。")
            correct_answers_json = json.dumps(correct_answers_list)

            image_filename_to_save = None
            if form.image.data:
                file = form.image.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_path_abs = os.path.join(current_app.static_folder, UPLOAD_FOLDER_NAME)
                    if not os.path.exists(upload_path_abs): # 念のためフォルダ存在確認
                        os.makedirs(upload_path_abs)
                    file.save(os.path.join(upload_path_abs, filename))
                    image_filename_to_save = os.path.join(UPLOAD_FOLDER_NAME, filename)
                elif file.filename != '':
                    flash('許可されていないファイル形式です。', 'warning')
                    return render_template('admin_question_form.html', title='問題追加', form=form, legend='新しい問題を追加')

            new_question = Question(
                question_text=form.question_text.data,
                options=options_json,
                correct_answer=correct_answers_json,
                explanation=form.explanation.data,
                image_filename=image_filename_to_save
            )
            db.session.add(new_question)
            db.session.commit()
            flash('新しい問題が追加されました！', 'success')
            return redirect(url_for('admin.list_questions'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'問題の追加中にエラーが発生しました: {str(e)}', 'danger')
            current_app.logger.error(f"Error adding question: {e}", exc_info=True)
            
    return render_template('admin_question_form.html', title='問題追加', form=form, legend='新しい問題を追加')


@admin_bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    form = QuestionForm(obj=question)

    if request.method == 'GET':
        try:
            if question.options:
                form.options_text.data = ', '.join(json.loads(question.options))
            if question.correct_answer:
                form.correct_answers_text.data = ', '.join(json.loads(question.correct_answer))
        except (json.JSONDecodeError, TypeError):
            flash('問題データ(選択肢/正解)の読み込みに失敗しました。手動で確認・修正してください。', 'warning')
            form.options_text.data = question.options if isinstance(question.options, str) else ''
            form.correct_answers_text.data = question.correct_answer if isinstance(question.correct_answer, str) else ''

    if form.validate_on_submit():
        try:
            question.question_text = form.question_text.data
            
            options_list = [opt.strip() for opt in form.options_text.data.split(',') if opt.strip()]
            if not options_list: raise ValueError("選択肢は1つ以上入力してください。")
            question.options = json.dumps(options_list)

            correct_answers_list = [ans.strip() for ans in form.correct_answers_text.data.split(',') if ans.strip()]
            if not correct_answers_list: raise ValueError("正解は1つ以上入力してください。")
            for ca in correct_answers_list:
                if ca not in options_list:
                    raise ValueError(f"正解 '{ca}' は選択肢の中に存在しません。")
            question.correct_answer = json.dumps(correct_answers_list)
            
            question.explanation = form.explanation.data

            if form.image.data:
                file = form.image.data
                if file and allowed_file(file.filename):
                    if question.image_filename:
                        old_image_path_abs = os.path.join(current_app.static_folder, question.image_filename)
                        if os.path.exists(old_image_path_abs):
                            try: os.remove(old_image_path_abs)
                            except OSError: flash(f"古い画像 '{question.image_filename}' の削除に失敗しました。", "warning")
                    
                    filename = secure_filename(file.filename)
                    upload_path_abs = os.path.join(current_app.static_folder, UPLOAD_FOLDER_NAME)
                    if not os.path.exists(upload_path_abs): os.makedirs(upload_path_abs)
                    file.save(os.path.join(upload_path_abs, filename))
                    question.image_filename = os.path.join(UPLOAD_FOLDER_NAME, filename)
                elif file.filename != '':
                     flash('許可されていないファイル形式です。画像は更新されませんでした。', 'warning')

            db.session.commit()
            flash('問題が更新されました！', 'success')
            return redirect(url_for('admin.list_questions'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'問題の更新中にエラーが発生しました: {str(e)}', 'danger')
            current_app.logger.error(f"Error editing question {question_id}: {e}", exc_info=True)

    current_image_url = None
    if question.image_filename:
        # パス区切り文字をURLセーフな '/' に統一
        current_image_url = url_for('static', filename=question.image_filename.replace(os.sep, '/'))

    return render_template('admin_question_form.html', title='問題編集', form=form, 
                           legend=f'問題 ID: {question.id} を編集', question_id=question.id,
                           current_image_url=current_image_url)


@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    if question.image_filename:
        image_path_abs = os.path.join(current_app.static_folder, question.image_filename)
        if os.path.exists(image_path_abs):
            try: os.remove(image_path_abs)
            except OSError as e: # エラーオブジェクトeをキャッチ
                flash(f"関連画像 '{question.image_filename}' の削除に失敗しました: {e}", "warning")
                current_app.logger.warning(f"Failed to delete image {image_path_abs}: {e}")


    try:
        db.session.delete(question)
        db.session.commit()
        flash(f'問題 ID: {question.id} が削除されました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'問題 ID: {question.id} の削除中にエラーが発生しました: {str(e)}', 'danger')
        current_app.logger.error(f"Error deleting question {question_id}: {e}", exc_info=True)

    return redirect(url_for('admin.list_questions'))
