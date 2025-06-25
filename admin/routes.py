from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
import os

from . import admin_bp
from .decorators import admin_required
# modelsとformsはアプリケーションルートからインポート
from models import db, Question, UserAnswer, UserCheck, ExamResult, User
from forms import QuestionForm, QuestionImportForm # QuestionImportFormを追加
import csv
import io
from sqlalchemy import text

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

            correct_answers_list = [ans.strip() for ans in form.correct_answers_text.data.split(',') if ans.strip()]
            if not correct_answers_list: raise ValueError("正解は1つ以上入力してください。")
            for ca in correct_answers_list:
                if ca not in options_list:
                    raise ValueError(f"正解 '{ca}' は選択肢の中に存在しません。")

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
                options=options_list,
                correct_answer=correct_answers_list,
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
            if question.options:
                form.options_text.data = ', '.join(map(str, question.options))
            if question.correct_answer:
                form.correct_answers_text.data = ', '.join(map(str, question.correct_answer))

    if form.validate_on_submit():
        try:
            question.question_text = form.question_text.data
            
            options_list = [opt.strip() for opt in form.options_text.data.split(',') if opt.strip()]
            if not options_list: raise ValueError("選択肢は1つ以上入力してください。")
            question.options = options_list

            correct_answers_list = [ans.strip() for ans in form.correct_answers_text.data.split(',') if ans.strip()]
            if not correct_answers_list: raise ValueError("正解は1つ以上入力してください。")
            for ca in correct_answers_list:
                if ca not in options_list:
                    raise ValueError(f"正解 '{ca}' は選択肢の中に存在しません。")
            question.correct_answer = correct_answers_list
            
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

# ... delete_question 関数の下に、以下の関数をまるごと追加 ...

@admin_bp.route('/question/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_questions():
    form = QuestionImportForm()
    if form.validate_on_submit():
        try:
            delete_all = request.form.get('delete_all')

            if delete_all:
                UserAnswer.query.delete()
                UserCheck.query.delete()
                Question.query.delete()
                # 'question'テーブルのIDシーケンスをリセットするSQLを実行
                # このSQLはPostgreSQLに特有のものです
                try:
                    db.session.execute(text('TRUNCATE TABLE question RESTART IDENTITY CASCADE;'))
                    db.session.commit()
                except Exception:
                    # SQLiteなど、TRUNCATEをサポートしないDBの場合は通常のDELETEに戻す
                    db.session.rollback()
                    Question.query.delete()
                    db.session.commit()
                flash("既存の全問題データを削除しました。", "warning")

            # --- ▼▼▼【ここが修正のポイントです】▼▼▼ ---
            csv_file = form.csv_file.data
            # 1. アップロードされたバイナリデータを、UTF-8形式のテキストに変換します
            stream = io.TextIOWrapper(csv_file.stream, 'utf-8-sig')
            # 2. 変換後のテキストストリームをCSVリーダーに渡します
            reader = csv.DictReader(stream)
            # --- ▲▲▲【ここまでが修正のポイントです】▲▲▲ ---

            questions_to_add = []
            questions_to_update_count = 0
            
            for row in reader:
                options_list = [opt.strip() for opt in row['options'].split('|') if opt.strip()]
                correct_answers_list = [ans.strip() for ans in row['correct_answers'].split('|') if ans.strip()]
                question_id = row.get('id')

                if question_id and Question.query.get(question_id):
                    q = Question.query.get(question_id)
                    q.question_text = row['question_text']
                    q.options = options_list
                    q.correct_answer = correct_answers_list
                    q.explanation = row['explanation']
                    q.image_filename = row['image_filename'] or None
                    questions_to_update_count += 1
                else:
                    new_question = Question(
                        question_text=row['question_text'],
                        options=options_list,
                        correct_answer=correct_answers_list,
                        explanation=row['explanation'],
                        image_filename=row['image_filename'] or None
                    )
                    questions_to_add.append(new_question)

            if questions_to_add:
                db.session.add_all(questions_to_add)
            
            db.session.commit()
            flash(f"{len(questions_to_add)}件の問題を新規追加し、{questions_to_update_count}件の問題を更新しました。", "success")
        
        except Exception as e:
            db.session.rollback()
            flash(f"インポート中にエラーが発生しました: {e}", "danger")
            current_app.logger.error(f"Error importing questions: {e}", exc_info=True)
        
        return redirect(url_for('admin.import_questions'))

    return render_template('admin_question_import.html', title='問題の一括インポート', form=form)

# 試験結果の一覧を表示するルート
@admin_bp.route('/exam_results')
@login_required
@admin_required
def list_exam_results():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    # User情報も一緒に取得するためにjoinする
    results_pagination = ExamResult.query.join(User).order_by(ExamResult.submitted_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin_exam_results.html', title='本番試験結果一覧', results_pagination=results_pagination)

# 個別の試験結果詳細を表示するルート
@admin_bp.route('/exam_result/<int:result_id>')
@login_required
@admin_required
def view_exam_result(result_id):
    result = ExamResult.query.get_or_404(result_id)
    return render_template('admin_exam_result_detail.html', title=f"試験結果詳細 (User: {result.user.username})", result=result)