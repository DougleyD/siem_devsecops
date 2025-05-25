from flask import Blueprint, redirect, render_template, url_for

from app.services.auth_service import login_required

view_bp = Blueprint('view', __name__)

@view_bp.route('/events', methods=['GET'])
@login_required
def events(user):
   return render_template('application/events.html', title='EventTrace | Event View', user=user)
