from app.api import bp
from app.models import Sample
from flask import jsonify, Response, request
from flask_login import current_user, login_required
import json
import csv
import io

@bp.route('/sample/<int:id>/export/json')
@login_required
def export_sample_json(id):
    sample = Sample.query.get_or_404(id)
    if sample.author != current_user:
        return jsonify({'error': 'unauthorized'}), 403

    images_data = []
    for image in sample.images:
        detections_data = []
        for detection in image.detections:
            detections_data.append({
                'id': detection.id,
                'x_coordinate': detection.x_coordinate,
                'y_coordinate': detection.y_coordinate,
                'confidence': detection.confidence,
            })
        images_data.append({
            'id': image.id,
            'filepath': image.filepath,
            'timestamp': image.timestamp.isoformat(),
            'detections': detections_data,
        })

    readings_data = []
    for reading in sample.readings:
        readings_data.append({
            'id': reading.id,
            'temperature': reading.temperature,
            'ph': reading.ph,
            'timestamp': reading.timestamp.isoformat(),
        })

    data = {
        'id': sample.id,
        'name': sample.name,
        'timestamp': sample.timestamp.isoformat(),
        'user_id': sample.user_id,
        'images': images_data,
        'sensor_readings': readings_data,
    }

    return jsonify(data)

@bp.route('/sample/<int:id>/export/csv')
@login_required
def export_sample_csv(id):
    sample = Sample.query.get_or_404(id)
    if sample.author != current_user:
        return jsonify({'error': 'unauthorized'}), 403

    # We will export detections data to CSV
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['image_id', 'detection_id', 'x_coordinate', 'y_coordinate', 'confidence'])

    for image in sample.images:
        for detection in image.detections:
            writer.writerow([
                image.id,
                detection.id,
                detection.x_coordinate,
                detection.y_coordinate,
                detection.confidence
            ])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=sample_{sample.id}_detections.csv"}
    )
