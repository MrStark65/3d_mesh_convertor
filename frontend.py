import streamlit as st
import requests
import open3d as o3d
import numpy as np
import tempfile
import os
import plotly.graph_objects as go
import time
import zipfile

# 🎨 Streamlit UI Enhancements
st.set_page_config(page_title="3D Mesh Converter", page_icon="🔷", layout="wide")

SERVER_URL = "http://127.0.0.1:5000"

# 🌟 Stylish Header
st.markdown(
    """
    <h1 style="text-align: center; color: #4A90E2;">🚀 Problem Statement: 3D Mesh Converter</h1>
    <h4 style="text-align: center; color: #555;">Convert E57 point clouds into PLY, OBJ, or STL 3D meshes</h4>
    <hr style="border: 1px solid #ddd;">
    """,
    unsafe_allow_html=True
)

# 🔄 Animated file upload section
uploaded_files = st.file_uploader("🗄 Upload E57 files", type=["e57"], accept_multiple_files=True)

converted_files = []

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")

    # 🎨 Format selection with clear UI
    file_format = st.radio(
        "🎯 Choose your preferred 3D format:",
        ["PLY", "OBJ", "STL", "ZIP"],
        horizontal=True
    )

    # User color selection
    color_scheme = st.selectbox("🔧 Select Point Cloud Color Scheme",
                                ["Viridis", "Plasma", "Cividis", "Inferno", "Magma", "Rainbow", "Jet"])

    # 🔄 Processing Animation
    with st.spinner("🛠️ Processing files... Please wait..."):
        time.sleep(1.5)

        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".e57") as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_file_path = temp_file.name

            # Upload file to the backend
            with open(temp_file_path, "rb") as file:
                response = requests.post(f"{SERVER_URL}/upload", files={"file": file})

            if response.status_code == 200:
                data = response.json()
                ply_file_path = data.get("ply_file")
                st.success(f"🎉 {uploaded_file.name} converted successfully!")

                # Load the PLY file
                pcd = o3d.io.read_point_cloud(ply_file_path)
                mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha=0.03)
                mesh.compute_vertex_normals()

                # Convert to selected format
                if file_format == "OBJ":
                    obj_path = ply_file_path.replace(".ply", ".obj")
                    o3d.io.write_triangle_mesh(obj_path, mesh)
                    converted_files.append(obj_path)

                elif file_format == "STL":
                    stl_path = ply_file_path.replace(".ply", ".stl")
                    o3d.io.write_triangle_mesh(stl_path, mesh)
                    converted_files.append(stl_path)

                else:  # Default to PLY
                    converted_files.append(ply_file_path)

                # Convert to Plotly 3D visualization with color customization
                points = np.asarray(pcd.points)
                fig = go.Figure(data=[go.Scatter3d(
                    x=points[:, 0],
                    y=points[:, 1],
                    z=points[:, 2],
                    mode='markers',
                    marker=dict(size=1, color=points[:, 2], colorscale=color_scheme)
                )])

                fig.update_layout(
                    title=f"📌 3D Visualization - {uploaded_file.name}",
                    margin=dict(l=0, r=0, b=0, t=40),
                    scene=dict(bgcolor="rgba(0, 0, 0, 0)"),
                    template="plotly_dark"
                )

                # Display in Streamlit
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.error(f"⚠️ Error converting {uploaded_file.name}: {response.json().get('error', 'Upload failed')}")

            # Cleanup temporary files
            os.remove(temp_file_path)

    # 🎯 Download Section
    st.markdown("<h3 style='color: #4A90E2;'>👅 Download Your Files</h3>", unsafe_allow_html=True)

    for converted_file in converted_files:
        with open(converted_file, "rb") as f:
            st.download_button(f"🗂 Download {os.path.basename(converted_file)}", f,
                               file_name=os.path.basename(converted_file))

    # Provide ZIP download option if multiple files were converted
    if len(converted_files) > 1:
        zip_filename = "converted_meshes.zip"
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for file in converted_files:
                zipf.write(file, os.path.basename(file))

        with open(zip_filename, "rb") as f:
            st.download_button("📦 Download All Files as ZIP", f, file_name="converted_meshes.zip")

# 🚀 Footer
st.markdown(
    """
    <hr style="border: 1px solid #ddd;">
    <h5 style="text-align: center; color: #555;">Developed by Lakshay Singh & Priya Singh 🚀 | Powered by Streamlit & Open3D</h5>
    """,
    unsafe_allow_html=True
)