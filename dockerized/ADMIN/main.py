# main.py  (Flask — legacy)
# FastAPI equivalent: dockerized/ADMIN_FASTAPI/routers/main_router.py
# Conversion notes:
#   - Blueprint replaced by FastAPI APIRouter
#   - @login_required replaced by Depends(security.get_optional_user) with redirect
#   - current_user passed explicitly via template context instead of Flask-Login global

from flask import Blueprint, render_template
from flask_login import login_required, current_user

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)