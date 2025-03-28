from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
import open3d as o3d
import pye57
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
PLY_FOLDER = "ply_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLY_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload and converts E57 to PLY."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    e57_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(e57_path)

    try:
        # Read the E57 file
        e57 = pye57.E57(e57_path)
        data = e57.read_scan(0)  # Read the first scan

        # Extract XYZ coordinates
        xyz = np.vstack((data["cartesianX"], data["cartesianY"], data["cartesianZ"])).T

        # Create Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz)

        # Save as PLY
        ply_filename = file.filename.replace(".e57", ".ply")
        ply_path = os.path.join(PLY_FOLDER, ply_filename)
        o3d.io.write_point_cloud(ply_path, pcd)

        return jsonify({'message': 'File converted successfully', 'ply_file': ply_path})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_ply(filename):
    """Serves the converted PLY file."""
    ply_path = os.path.join(PLY_FOLDER, filename)
    if os.path.exists(ply_path):
        return send_file(ply_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
