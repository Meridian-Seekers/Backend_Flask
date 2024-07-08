from flask import Blueprint, jsonify, request, current_app
import os
import uuid
from db_config import get_db

main_model_api = Blueprint('main_model_api', __name__)

@main_model_api.before_request
def setup_image_folder():
    # Define the folder to save images
    global IMAGE_FOLDER
    IMAGE_FOLDER = os.path.join(current_app.root_path, 'static', 'images')
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

@main_model_api.route('/main_model', methods=['POST'])
def main_model():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image = request.files['image']
        if image.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        pose_name = request.form.get('pose_name')
        single_pose_result = request.form.get('single_pose_result')

        if not pose_name or not single_pose_result:
            return jsonify({'error': 'Pose_name or Single_pose_result missing or null'}), 400

        r_id = request.form.get('r_id')
        c_id = request.form.get('c_id')

        # Save the image with a unique filename
        filename = str(uuid.uuid4()) + os.path.splitext(image.filename)[1]
        filepath = os.path.join(IMAGE_FOLDER, filename)
        image.save(filepath)

        # Save pose_name and single_pose_result to the database
        single_pose_id = save_single_pose(pose_name, single_pose_result, r_id, c_id)

        return jsonify({
            'message': 'Main model processing completed successfully', 
            'image_url': f'/static/images/{filename}', 
            'single_pose_id': single_pose_id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@main_model_api.route('/delete_image', methods=['POST'])
def delete_image():
    single_pose_id = request.json.get('single_pose_id')
    if not single_pose_id:
        return jsonify({'error': 'No single_pose_id provided'}), 400

    try:
        filepath = get_image_filepath(single_pose_id)
        if not filepath:
            return jsonify({'error': 'Image not found'}), 404

        if os.path.exists(filepath):
            os.remove(filepath)
            delete_single_pose(single_pose_id)
            return jsonify({'message': 'Image deleted successfully'}), 200
        else:
            return jsonify({'error': 'Image file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def save_single_pose(pose_name, single_pose_result, r_id, c_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO Single_pose (Pose_name, Single_pose_result, R_id, C_id)
            VALUES (%s, %s, %s, %s)
        ''', (pose_name, single_pose_result, r_id, c_id))
        db.commit()
        single_pose_id = cursor.lastrowid
        cursor.close()
        return single_pose_id
    except Exception as e:
        db.rollback()
        raise e



def get_image_filepath(single_pose_id):
    # Logic to determine the image filepath based on single_pose_id
    # Assuming a naming convention for images
    filename = f'{single_pose_id}.jpg'
    filepath = os.path.join(IMAGE_FOLDER, filename)
    return filepath

def delete_single_pose(single_pose_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM Single_pose WHERE Single_pose_id = %s', (single_pose_id,))
    db.commit()
    cursor.close()

# No need to run the app here, leave it to the main application script
