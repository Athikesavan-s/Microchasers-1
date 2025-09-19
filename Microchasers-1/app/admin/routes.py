from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Sample, Image, Detection
from app.database import db
from app.auth.forms import ADMIN_CREDENTIALS
from functools import wraps
import os

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in first.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_administrator:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    stats = {
        'users': User.query.count(),
        'samples': Sample.query.count(),
        'images': Image.query.count(),
        'detections': Detection.query.count(),
    }
    
    users = User.query.all()
    recent_samples = Sample.query.order_by(Sample.timestamp.desc()).limit(5).all()
    recent_images = Image.query.order_by(Image.timestamp.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         users=users,
                         recent_samples=recent_samples,
                         recent_images=recent_images,
                         admin_email=ADMIN_CREDENTIALS['email'])

@bp.route('/delete/user/<int:id>')
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.username == ADMIN_CREDENTIALS['username']:
        flash('Cannot delete admin user.', 'error')
        return redirect(url_for('admin.index'))
    
    # Delete all associated data
    for sample in user.samples:
        for image in sample.images:
            # Delete image files
            if image.filepath:
                try:
                    file_path = os.path.join(current_app.root_path, 'static', image.filepath)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    flash(f'Error deleting image file: {str(e)}', 'warning')
            
            # Delete database records
            Detection.query.filter_by(image_id=image.id).delete()
            db.session.delete(image)
        db.session.delete(sample)
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} and all associated data have been deleted.', 'success')
    return redirect(url_for('admin.index'))

@bp.route('/delete/sample/<int:id>')
@login_required
@admin_required
def delete_sample(id):
    sample = Sample.query.get_or_404(id)
    for image in sample.images:
        Detection.query.filter_by(image_id=image.id).delete()
        db.session.delete(image)
    db.session.delete(sample)
    db.session.commit()
    flash(f'Sample and all associated data have been deleted.', 'success')
    return redirect(url_for('admin.index'))

@bp.route('/clear/all', methods=['POST'])
@login_required
@admin_required
def clear_all():
    # Don't delete admin user
    admin = User.query.filter_by(username=ADMIN_CREDENTIALS['username']).first()
    
    Detection.query.delete()
    Image.query.delete()
    Sample.query.delete()
    User.query.filter(User.id != admin.id).delete()
    
    db.session.commit()
    flash('All data has been cleared except admin account.', 'success')
    return redirect(url_for('admin.index'))