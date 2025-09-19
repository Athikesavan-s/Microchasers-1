from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user, login_user
from werkzeug.utils import secure_filename
import os
import json
from collections import Counter
import numpy as np
from app.main import bp
from app.main.forms import SampleForm, ImageUploadForm
from app.models import Sample, Image, Detection, User
from app.database import db
from app.services.image_processing import detect_microplastics

@bp.route('/')
@bp.route('/index')
def index():
    samples = []
    if current_user.is_authenticated:
        samples = current_user.samples.order_by(Sample.timestamp.desc()).all()
    return render_template('index.html', title='Home', samples=samples)

@bp.route('/create_sample', methods=['GET', 'POST'])
@login_required
def create_sample():
    form = SampleForm()
    if form.validate_on_submit():
        sample = Sample(name=form.name.data, author=current_user)
        db.session.add(sample)
        db.session.commit()
        flash('Your sample has been created!')
        return redirect(url_for('main.index'))
    return render_template('create_sample.html', title='Create Sample', form=form)

@bp.route('/sample/<int:id>', methods=['GET', 'POST'])
@login_required
def sample(id):
    sample = Sample.query.get_or_404(id)
    if sample.author != current_user:
        flash('You are not authorized to view this sample.')
        return redirect(url_for('main.index'))

    form = ImageUploadForm()
    
    # Pass Detection model to template for access to its properties
    Detection_model = Detection
    if form.validate_on_submit():
        f = form.image.data
        filename = secure_filename(f.filename)
        upload_path = os.path.join(current_app.root_path, 'static/uploads', filename)
        f.save(upload_path)

        # Create a new image record
        new_image = Image(filepath=f'uploads/{filename}', sample=sample)
        db.session.add(new_image)
        db.session.commit()

        # Process the image
        detections, processed_image_path = detect_microplastics(upload_path)

        # Update image record with the path to the processed image
        if processed_image_path:
            processed_filename = os.path.basename(processed_image_path)
            new_image.filepath = f'uploads/{processed_filename}'
            db.session.add(new_image) # Ensure the change is staged for commit

        # Save detections
        for det in detections:
            detection = Detection(
                x_coordinate=det['x_coordinate'],
                y_coordinate=det['y_coordinate'],
                size=det['size'],
                shape=det['shape'],
                color=det['color'],
                image=new_image
            )
            db.session.add(detection)

        db.session.commit()

        flash('Image uploaded and processed successfully!')
        return redirect(url_for('main.sample', id=id))

    images = sample.images.order_by(Image.timestamp.desc()).all()
    images_with_stats = []
    for image in images:
        detections = image.detections.all()
        if detections:
            sizes = [d.size for d in detections]
            size_stats = {
                'min': min(sizes),
                'max': max(sizes),
                'avg': np.mean(sizes)
            }
        else:
            size_stats = {'min': 0, 'max': 0, 'avg': 0}
        images_with_stats.append({'image': image, 'stats': size_stats})

    return render_template('sample.html', title=sample.name, sample=sample, form=form, images_with_stats=images_with_stats, Detection=Detection_model)

@bp.route('/samples')
@login_required
def samples():
    samples = current_user.samples.order_by(Sample.timestamp.desc()).all()
    return render_template('samples.html', title='My Samples', samples=samples)

@bp.route('/dashboard/<int:image_id>')
@login_required
def dashboard(image_id):
    image = Image.query.get_or_404(image_id)
    if image.sample.author != current_user:
        flash('You are not authorized to view this dashboard.')
        return redirect(url_for('main.index'))

    detections = image.detections.all()

    # Prepare data for tables
    total_particles = len(detections)

    # Shape distribution
    shapes = [d.shape for d in detections]
    shape_counts = Counter(shapes)

    # Size distribution
    sizes = [d.size for d in detections]
    size_stats = {
        'min': min(sizes) if sizes else 0,
        'max': max(sizes) if sizes else 0,
        'avg': np.mean(sizes) if sizes else 0
    }


    # Color analysis
    colors = [d.color for d in detections]
    color_counts = Counter(colors)


    return render_template('dashboard.html',
                           title='Analysis Dashboard',
                           image=image,
                           total_particles=total_particles,
                           shape_counts=shape_counts,
                           size_stats=size_stats,
                           color_counts=color_counts,
                           detections=detections)

@bp.route('/demo')
def demo():
    # Check if demo user exists, if not create one
    demo_user = User.query.filter_by(username='demo_user').first()
    if not demo_user:
        demo_user = User(username='demo_user', email='demo@example.com')
        demo_user.set_password('demo123')  # Set a secure password even though it won't be used directly
        db.session.add(demo_user)
        db.session.commit()
    
    # Log in as demo user
    login_user(demo_user)
    flash('You are now logged in as a demo user. Any samples you create will be associated with this demo account.')
    
    # Redirect to create sample page
    return redirect(url_for('main.create_sample'))
