from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
import open3d as o3d
import pye57
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Create directories for file storage
UPLOAD_FOLDER = "uploads"
PLY_FOLDER = "ply_files"
MESH_FOLDER = "mesh_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLY_FOLDER, exist_ok=True)
os.makedirs(MESH_FOLDER, exist_ok=True)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload, converts E57 to PLY, and generates a mesh."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save uploaded E57 file
    e57_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(e57_path)

    try:
        # Read the E57 file
        e57 = pye57.E57(e57_path)
        data = e57.read_scan(0)  # Read the first scan

        # Extract XYZ coordinates
        xyz = np.vstack((data["cartesianX"], data["cartesianY"], data["cartesianZ"])).T

        # Ensure there are enough points
        if xyz.shape[0] < 5000:
            return jsonify({'error': 'Point cloud is too sparse for meshing'}), 400

        # Create Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz)

        # Estimate normals
        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=50))
        pcd.orient_normals_consistent_tangent_plane(100)

        # Save as PLY
        ply_filename = file.filename.replace(".e57", ".ply")
        ply_path = os.path.join(PLY_FOLDER, ply_filename)
        o3d.io.write_point_cloud(ply_path, pcd)

        # Mesh using Ball Pivoting
        radii = [0.005, 0.01, 0.02]  # Adjust radii based on scan density
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
            pcd, o3d.utility.DoubleVector(radii)
        )

        # Save mesh as OBJ
        mesh_filename = file.filename.replace(".e57", ".obj")
        mesh_path = os.path.join(MESH_FOLDER, mesh_filename)
        o3d.io.write_triangle_mesh(mesh_path, mesh)

        return jsonify({
            'message': 'File converted successfully',
            'ply_file': ply_path,
            'mesh_file': mesh_path
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Serves the converted PLY or Mesh file."""
    ply_path = os.path.join(PLY_FOLDER, filename)
    mesh_path = os.path.join(MESH_FOLDER, filename)

    if os.path.exists(ply_path):
        return send_file(ply_path, as_attachment=True)
    elif os.path.exists(mesh_path):
        return send_file(mesh_path, as_attachment=True)

    return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)
