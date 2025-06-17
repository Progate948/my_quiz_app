from flask import Blueprint

# Blueprintオブジェクトを作成
# 'admin' はBlueprintの名前
# __name__ はBlueprintが定義されているPythonモジュール名
# url_prefix='/admin' はこのBlueprintのルート全てに '/admin' が付与される
# template_folder='templates' はこのBlueprint専用のテンプレートフォルダを指定
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')

from . import routes # このBlueprintのルート定義をインポート (後で作成)