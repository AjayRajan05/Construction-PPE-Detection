import streamlit as st
import cv2
import pandas as pd
from ultralytics import YOLO
import tempfile
import time
from PIL import Image
import numpy as np

# Optional: Suppress PyTorch warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Load YOLO model
model = YOLO("C:\\Users\\amudh\\OneDrive\\Desktop\\PPE_DET\\Project\\models\\best.pt")  # Update with your best model

# Set up Streamlit page
st.set_page_config(page_title="PPE Detection Dashboard")

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'detection_type' not in st.session_state:
    st.session_state.detection_type = None
if 'run_detection' not in st.session_state:
    st.session_state.run_detection = False
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'cap' not in st.session_state:
    st.session_state.cap = None

# Step 1: Login Page
if not st.session_state.logged_in:
    st.title("🏗️ PPE Detection Dashboard")
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "shaj0416":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid login. Try again.")

# Step 2: Detection Type Selection
if st.session_state.logged_in:
    if st.session_state.detection_type is None:
        st.title("Select Detection Type")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Image Detection"):
                st.session_state.detection_type = "Image Detection"
                st.rerun()
        with col2:
            if st.button("Video Detection"):
                st.session_state.detection_type = "Video Detection"
                st.rerun()
        with col3:
            if st.button("Real-time Detection"):
                st.session_state.detection_type = "Real-time Detection"
                st.rerun()

        st.write("")
        col_logout, col_empty = st.columns([1,3])
        with col_logout:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.detection_type = None
                st.rerun()

# Step 3: Main App
if st.session_state.detection_type:
    mode = st.session_state.detection_type

    # Step 4.1: Image Detection
    if mode == "Image Detection":
        st.header("🖼️ Image-Based PPE Detection")
        uploaded_image = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            image = Image.open(uploaded_image)
            img_array = np.array(image)
            results = model(img_array)[0]
            annotated = results.plot()
            st.image(annotated, caption="Detected Image", channels="BGR")

        if st.button("Go Back", key="go_back_image"):
            st.session_state.detection_type = None
            st.rerun()

    # Step 4.2: Video Detection
    # Step 4.2: Video Detection
    elif mode == "Video Detection":
        st.header("🎞️ Video-Based PPE Detection")
        uploaded_video = st.file_uploader("Upload a Video", type=["mp4", "avi"])
        if uploaded_video:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_video.read())
            cap = cv2.VideoCapture(tfile.name)
            stframe = st.empty()

            stop_button = st.button("Stop Video Detection", key="stop_video_detection_button")

            while cap.isOpened() and not stop_button:
                ret, frame = cap.read()
                if not ret:
                    break
                results = model(frame)[0]
                annotated = results.plot()
                stframe.image(annotated, channels="BGR")
                #stop_button = st.button("Stop Video Detection", key="stop_video_detection_button_inside")
            
            cap.release()

        if st.button("Go Back", key="go_back_video"):
            st.session_state.detection_type = None
            st.rerun()


    # Step 4.3: Real-Time Detection
    # Step 4.3: Real-Time Detection
    elif mode == "Real-time Detection":
        st.header("📹 Real-Time Webcam PPE Detection")

        if 'run_detection' not in st.session_state:
            st.session_state.run_detection = False
        if 'log_messages' not in st.session_state:
            st.session_state.log_messages = []
        if 'cap' not in st.session_state:
            st.session_state.cap = None

        def log_violation(violation):
            timestamp = time.strftime("%H:%M:%S")
            st.session_state.log_messages.append(f"[{timestamp}] {violation}")

        # Sidebar UI
        with st.sidebar:
            st.subheader("🔍 Detection Status")

            # Go Back Button
            if st.button("Go Back", key="go_back_sidebar"):
                if st.session_state.cap:
                    st.session_state.cap.release()
                st.session_state.detection_type = None
                st.session_state.run_detection = False
                st.session_state.cap = None
                st.rerun()

            # Violation Logs
            st.text_area(
                "🔔 Violation Logs",
                value="\n".join(st.session_state.log_messages[-20:]),
                height=300,
                disabled=True,
                key="violation_logs_sidebar"
            )

            # Metrics Placeholders
            people_count_placeholder = st.empty()
            no_helmet_placeholder = st.empty()
            no_vest_placeholder = st.empty()
            alert_placeholder = st.empty()

            # Start and Stop buttons
            col_start, col_stop = st.columns(2)
            with col_start:
                if st.button("Start Detection"):
                    st.session_state.run_detection = True
                    st.session_state.log_messages = []
                    if st.session_state.cap is None:
                        try:
                            st.session_state.cap = cv2.VideoCapture(0)
                        except Exception as e:
                            st.error(f"Error opening camera: {e}")
                            st.session_state.run_detection = False
            with col_stop:
                if st.button("Stop Detection"):
                    st.session_state.run_detection = False
                    if st.session_state.cap:
                        st.session_state.cap.release()
                        st.session_state.cap = None

        # Center main camera feed
        stframe = st.empty()

        # Detection Loop
        while st.session_state.run_detection and st.session_state.cap is not None:
            ret, frame = st.session_state.cap.read()
            if not ret:
                st.warning("Camera not accessible.")
                st.session_state.cap.release()
                st.session_state.cap = None
                st.session_state.run_detection = False
                break

            results = model(frame)[0]
            boxes = []
            if results.boxes is not None and hasattr(results.boxes, 'cls'):
                try:
                    boxes = results.boxes.cls.tolist()
                except Exception:
                    boxes = []

            labels = [model.names[int(cls)] for cls in boxes]

            people_count = labels.count("Person")
            no_helmet = labels.count("NO-Hardhat")
            no_vest = labels.count("NO-Safety Vest")

            annotated = results.plot()
            stframe.image(annotated, channels="BGR")  # Only video here!

            # Update Sidebar placeholders
            people_count_placeholder.markdown(f"👷 **People Detected**: {people_count}")
            no_helmet_placeholder.markdown(f"❌ **No Helmet**: {no_helmet}")
            no_vest_placeholder.markdown(f"❌ **No Safety Vest**: {no_vest}")

            if no_helmet > 0:
                alert_placeholder.error("🚨 Helmet violation detected!")
                log_violation("No Helmet Detected!")
            elif no_vest > 0:
                alert_placeholder.warning("⚠️ Vest violation detected!")
                log_violation("No Safety Vest Detected!")
            else:
                alert_placeholder.success("✅ All safety measures followed.")

            time.sleep(0.05)




#SHA
