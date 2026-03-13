import cv2
from flask import Flask, render_template, Response, jsonify, request
from ultralytics import YOLO
import threading
import time
import numpy as np

app = Flask(__name__)

# --- Global Configurations & State ---
# Assuming camera 0, you could use an IP camera URL here if needed.
CAMERA_SOURCE = 0
CROWD_MODEL_PATH = "yolov8s.pt"

camera_lock = threading.Lock()
# Initialize YOLOv8 Model (Using 'small' model for better accuracy than 'nano')
model = YOLO(CROWD_MODEL_PATH)

# Global variables to store the latest simulation metrics inputted by user
# Or we can just calculate these dynamically on request.
# Let's keep a global variable for the number of people detected.
current_people_detected = 0

# Base parameters that users can modify via UI
app.__config = {
    "capacity": 50,      # Default max capacity
    "exit_doors": 2,     # Default exit doors
    "camera_source": 0,  # Default camera source (0 is webcam)
    "focus_area": None   # None, 'low', 'medium', 'high'
}


def generate_frames():
    """Generator function to stream webcam frames and detect people."""
    global current_people_detected
    
    current_source = app.__config['camera_source']
    try:
        src = int(current_source) if str(current_source).isdigit() else current_source
    except:
        src = 0
    cap = cv2.VideoCapture(src)
    
    # If camera fails, fallback to a dummy generator or log warning
    if not cap.isOpened():
        print(f"[WARNING] Could not open video source {src}. Generating blank frames.")
        # Optional: yield dummy image if camera is broken.
        
    while True:
        # Check if source changed dynamically from UI
        if current_source != app.__config['camera_source']:
            cap.release()
            current_source = app.__config['camera_source']
            try:
                src = int(current_source) if str(current_source).isdigit() else current_source
                if isinstance(src, str) and not src.startswith("http") and str(src) != '0' and str(src) != '1' and str(src) != '2':
                    import os
                    src = os.path.abspath(src) # Ensure absolute path for local video files
            except:
                src = 0
            cap = cv2.VideoCapture(src)
            if not cap.isOpened():
                print(f"[WARNING] Could not open video source {src}.")
                
        success, frame = cap.read()
        if not success:
            # If a video file ends, loop it. If it's a camera stream that dies, wait.
            if isinstance(src, str) and not str(src).isdigit():
                # We reached end of video file, loop back to frame 0
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                # Read again to ensure we don't get stuck if file is truly unreadable
                success, frame = cap.read()
                if not success:
                    time.sleep(1)
                    continue
            else:
                time.sleep(1) # Prevent tight crash loop for frozen webcams
                continue
            
        # Resize base frame first
        frame = cv2.resize(frame, (640, 480))
        
        # Apply Simulation Focus Area if requested
        focus_area = app.__config.get('focus_area')
        current_source_str = str(current_source).lower()
        
        if focus_area == 'high':
            if 'mallcent' in current_source_str:
                cropped = frame[100:480, 200:600] # Mall central has crowds further back and centered
            elif 'foodcourt' in current_source_str:
                cropped = frame[150:480, 50:500] # Food court has crowds lower and left-aligned
            else:
                cropped = frame[150:480, 50:590]
            frame = cv2.resize(cropped, (640, 480))
            
        elif focus_area == 'medium':
            if 'mallcent' in current_source_str:
                cropped = frame[200:400, 100:300] # Left side of mall is sparser
            elif 'foodcourt' in current_source_str:
                cropped = frame[50:250, 400:640] # Top right of food court has fewer people
            else:
                cropped = frame[100:300, 150:400]
            frame = cv2.resize(cropped, (640, 480))
            
        elif focus_area == 'low':
            if 'mallcent' in current_source_str:
                cropped = frame[0:150, 400:640] # Top right of mall is completely empty
            elif 'foodcourt' in current_source_str:
                cropped = frame[100:250, 0:200]  # Middle left of foodcourt avoids signs and people
            else:
                cropped = frame[20:150, 20:150]
            frame = cv2.resize(cropped, (640, 480))
        
        # Run YOLO inference
        # Using a low confidence (0.08) with the stronger 'small' model
        results = model.predict(source=frame, classes=[0], conf=0.08, verbose=False)
        
        # Count number of bounding boxes (people)
        with camera_lock:
            current_people_detected = len(results[0].boxes)
            capacity = app.__config.get('capacity', 50)
            
        # Draw bounding boxes
        annotated_frame = results[0].plot()
        
        # Calculate density for the camera overlay
        density = current_people_detected / capacity
            
        if density < 0.4:
            density_label = "LOW DENSITY"
            d_color = (0, 255, 0) # Green
        elif density < 0.75:
            density_label = "MEDIUM DENSITY"
            d_color = (0, 165, 255) # Orange
        else:
            density_label = "HIGH DENSITY"
            d_color = (0, 0, 255) # Red
            
        # Add basic overlay for crowd
        cv2.putText(annotated_frame, f"People: {current_people_detected} | {density_label}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, d_color, 2)
                    
        # Add visual indicator if simulating a focus area
        if focus_area:
            cv2.putText(annotated_frame, f"SIMULATING CROP: {focus_area.replace('_', ' ').upper()}", (20, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                        
        # Encode frame back to JPEG for the stream
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()
        
        # Yeild the multipart byte stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
               
    cap.release()

@app.route("/")
def index():
    """Main dashboard dashboard."""
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    """Route that streams the webcam feed from the generator."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/config", methods=["POST"])
def update_config():
    """Endpoint for the frontend to update camera source and simulation triggers"""
    data = request.json
    if data:
        if 'camera_source' in data:
            app.__config['camera_source'] = data['camera_source']
        if 'focus_area' in data:
            app.__config['focus_area'] = data['focus_area']
    return jsonify({"success": True, "config": app.__config})

@app.route("/api/metrics")
def get_metrics():
    """Returns the live analytical metrics based on YOLO detections."""
    global current_people_detected
    
    with camera_lock:
        people = current_people_detected
        
    capacity = app.__config['capacity']
    exit_doors = app.__config['exit_doors']
    
    # Mathematical logic 
    density = np.clip(people / capacity, 0, 1.0) # avoid > 100% physically if we want, or allow overflow. Let's allow overflow.
    density = people / capacity
        
    density_percent = round(density * 100, 2)
    
    # Crowd classification based on pure density
    if density < 0.4:
         status = "Low Crowd"
         waiting_time = "2 minutes"
         status_class = "low"
    elif density < 0.75:
         status = "Medium Crowd"
         waiting_time = "5 minutes"
         status_class = "medium"
    else:
         status = "High Crowd"
         waiting_time = "10 minutes"
         status_class = "high"
         
    # Risk Score Calculation (0 to 100+)
    exit_factor = 1 / exit_doors
    risk_score = min(round((density * 70) + (exit_factor * 30), 2), 100)
    
    # Evacuation Time Calculation (minutes)
    # Assumes flow_rate of 50 people per minute per exit door.
    flow_rate = 50
    # Avoid zero division issues if people is 0
    if people == 0:
         evac_time_str = "0m"
    else:
         total_seconds = int((people / (exit_doors * flow_rate)) * 60)
         mins = total_seconds // 60
         secs = total_seconds % 60
         if mins > 0:
             evac_time_str = f"{mins}m {secs}s"
         else:
             evac_time_str = f"{secs}s"
         
    # Alert and Action Generation
    alert = None
    focus_area = app.__config.get('focus_area')
    action_call = "Monitoring Nominal"

    # Priority 3: High Density
    if density > 0.75 or focus_area == 'high':
         if focus_area == 'high' and density <= 0.75:
             # Force metrics to look high if simulation capacity allows it to technically be "safe"
             status_class = "high"
             risk_score = max(risk_score, 85)
             
         if exit_doors < 2:
             alert = "🚨 High Crowd + Low Exit Doors = Emergency Risk!"
         else:
             alert = "🚨 HIGH CROWD DENSITY DETECTED."
         action_call = "CALLING EMERGENCY SERVICES (Simulation)"
    else:
         alert = "Safe Environment"
         
    return jsonify({
         "people": people,
         "capacity": capacity,
         "exit_doors": exit_doors,
         "density_percent": density_percent,
         "status": status,
         "waiting_time": waiting_time,
         "status_class": status_class,
         "risk_score": risk_score,
         "evac_time": evac_time_str,
         "alert": alert,
         "action_call": action_call
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)