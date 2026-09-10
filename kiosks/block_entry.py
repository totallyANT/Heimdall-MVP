import os
import customtkinter as ctk
import cv2
import face_recognition
from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# --- 1. GLOBAL STATE & THEME ---
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
ctk.set_window_scaling(1.0)
ctk.set_widget_scaling(1.0)

LATEST_FRAME = None
FRAME_LOCK = threading.Lock()

known_face_encodings = []
known_face_names = []
db_sync_lock = threading.Lock()

# --- 2. MONGODB CONFIGURATION ---
MONGO_URI = os.getenv("MONGO_URI")

try:
    print("Connecting to MongoDB Atlas 'heimdall' Cluster...")
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    
    # DB Route Update
    db_main = mongo_client["heimdall"]
    db_security = mongo_client["heimdall"]
    
    # Collections mapped to the new tree
    residents_collection = db_main["residents"]
    worker_passes_collection = db_main["worker_passes"]
    guest_passes_collection = db_main["guest_passes"]
    delivery_collection = db_main["delivery_notifications"]
    
    # Logs now strictly routed to a custom 'entry_logs' collection
    incident_collection = db_security["entry_logs"]
    
    print("MongoDB Connected Successfully.")
except Exception as e:
    print(f"MongoDB Connection Failed: {e}")
    residents_collection = None
    worker_passes_collection = None
    guest_passes_collection = None
    delivery_collection = None
    incident_collection = None

def async_db_log(payload, is_tailgate=False):
    if incident_collection is None: return
    try:
        incident_collection.insert_one(payload)
        if is_tailgate:
            print(f"[!!! TAILGATE ALARM !!!] {payload['metrics']['intruder_count']} Intruders followed {payload['resident_compromised']}!")
        else:
            print(f"[DB LOG] Saved {payload['incident_type']}: {payload['identity']}")
    except Exception as e:
        pass

# --- 3. DATABASE EMBEDDING SYNC ---
def load_embeddings_from_db():
    global known_face_encodings, known_face_names
    
    if residents_collection is None:
        print("Cannot sync faces: Database offline.")
        return

    temp_encodings = []
    temp_names = []
    
    # Universal query: Find any document where 'embedding' exists, is an array, and isn't empty
    embedding_filter = {"embedding": {"$exists": True, "$type": "array", "$not": {"$size": 0}}}

    try:
        # 1. Load Residents
        for res in residents_collection.find(embedding_filter):
            encoding = np.array(res["embedding"], dtype=np.float64)
            temp_encodings.append(encoding)
            temp_names.append(res.get("full_name", f"Resident_Flat_{res.get('flat_number')}"))

        # 2. Load Workers
        for worker in worker_passes_collection.find(embedding_filter):
            encoding = np.array(worker["embedding"], dtype=np.float64)
            temp_encodings.append(encoding)
            temp_names.append(f"{worker.get('worker_name')} (Flat {worker.get('resident_flat')})")

        # 3. Load Guests / Walk-in Visitors
        for guest in guest_passes_collection.find(embedding_filter):
            encoding = np.array(guest["embedding"], dtype=np.float64)
            temp_encodings.append(encoding)
            temp_names.append(f"Guest: {guest.get('guest_name', 'Visitor')}")
            
        # 4. Load Vendors / Deliveries 
        if delivery_collection is not None:
            for vendor in delivery_collection.find(embedding_filter):
                encoding = np.array(vendor["embedding"], dtype=np.float64)
                temp_encodings.append(encoding)
                temp_names.append(f"Vendor: {vendor.get('delivery_service', 'Delivery')}")

        with db_sync_lock:
            known_face_encodings = temp_encodings
            known_face_names = temp_names
            
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Database Hot-Sync Complete. Armed with {len(known_face_names)} profiles.")
    except Exception as e:
        print(f"Error syncing embeddings: {e}")

load_embeddings_from_db()

# --- 4. LOAD AI MODELS ---
print("Loading YOLOv8 Nano...")
yolo_model = YOLO("yolov8n.pt") 

# --- 5. PASSIVE WATCHDOG AI ENGINE ---
def run_ai_engine():
    global LATEST_FRAME, known_face_encodings, known_face_names
    cap = cv2.VideoCapture(0)
    
    tracked_targets = []
    process_this_frame = True 
    active_logs = {}
    
    last_db_sync_time = time.time()
    COOLDOWN_SECONDS = 30  
    TAILGATE_TIME_WINDOW, TAILGATE_DISTANCE_LIMIT, TAILGATE_COOLDOWN = 5.0, 250, 10.0
    MATCH_DISTANCE_THRESHOLD = 15000 
    
    last_authorized_time = None
    last_authorized_name = "None"
    last_tailgate_log_time = datetime.min
    
    while True:
        if time.time() - last_db_sync_time > 30:
            threading.Thread(target=load_embeddings_from_db, daemon=True).start()
            last_db_sync_time = time.time()

        for _ in range(2): cap.grab()
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.resize(frame, (640, 480))
        results = yolo_model(frame, classes=0, conf=0.5, iou=0.3, verbose=False)
        current_yolo_boxes = [(int(x1), int(y1), int(x2), int(y2)) for r in results for x1, y1, x2, y2 in r.boxes.xyxy]
        
        new_tracked_targets = []
        claimed_old_targets = set()
        active_names_in_frame = set() 

        for (x1, y1, x2, y2) in current_yolo_boxes:
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            matched_old_target, min_distance, matched_index = None, float('inf'), -1
            
            for i, old_target in enumerate(tracked_targets):
                if i in claimed_old_targets: continue 
                ox1, oy1, ox2, oy2 = old_target['body_box']
                ocenter_x, ocenter_y = (ox1 + ox2) // 2, (oy1 + oy2) // 2
                distance = (center_x - ocenter_x)**2 + (center_y - ocenter_y)**2
                
                if distance < min_distance and distance < MATCH_DISTANCE_THRESHOLD:
                    min_distance = distance
                    matched_old_target = old_target
                    matched_index = i

            if matched_old_target:
                claimed_old_targets.add(matched_index) 
                assigned_name, assigned_face_box = matched_old_target['name'], matched_old_target['face_box']
                if assigned_face_box:
                    dx, dy = x1 - matched_old_target['body_box'][0], y1 - matched_old_target['body_box'][1]
                    assigned_face_box = (assigned_face_box[0]+dx, assigned_face_box[1]+dy, assigned_face_box[2]+dx, assigned_face_box[3]+dy)
            else:
                assigned_name = "Analyzing Target..." if process_this_frame else "Unknown Intruder"
                assigned_face_box = None

            if process_this_frame and assigned_name in ["Analyzing Target...", "Unknown Intruder"]:
                crop_img = frame[max(0, y1-50):y2, max(0, x1-50):x2+50]
                if crop_img.size > 0:
                    rgb_crop = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_crop, model="hog")
                    if face_locations:
                        face_encodings = face_recognition.face_encodings(rgb_crop, face_locations)
                        top, right, bottom, left = face_locations[0]
                        
                        with db_sync_lock: 
                            if len(known_face_encodings) > 0:
                                matches = face_recognition.compare_faces(known_face_encodings, face_encodings[0], tolerance=0.65)
                                face_distances = face_recognition.face_distance(known_face_encodings, face_encodings[0])
                                best_match_index = np.argmin(face_distances)
                                if matches[best_match_index]: 
                                    assigned_name = known_face_names[best_match_index]
                                else: 
                                    assigned_name = "Unknown Intruder"
                            else: 
                                assigned_name = "Unknown Intruder"
                                
                        assigned_face_box = (left + max(0, x1-50), top + max(0, y1-50), right + max(0, x1-50), bottom + max(0, y1-50))

            if assigned_name not in ["Analyzing Target...", "Unknown Intruder"]:
                if assigned_name in active_names_in_frame:
                    assigned_name = "Unknown Intruder"
                else:
                    active_names_in_frame.add(assigned_name)

            new_tracked_targets.append({'body_box': (x1, y1, x2, y2), 'face_box': assigned_face_box, 'name': assigned_name})
        
        tracked_targets = new_tracked_targets
        process_this_frame = not process_this_frame

        current_time = datetime.now()
        auth_positions, unknown_positions = [], []

        for target in tracked_targets:
            bx1, by1, bx2, by2 = target['body_box']
            raw_name = target['name']
            if raw_name == "Analyzing Target...": continue
            
            center_x, center_y = (bx1 + bx2) // 2, (by1 + by2) // 2
            
            if raw_name == "Unknown Intruder": 
                unknown_positions.append((center_x, center_y, target['body_box'], target['face_box']))
            else:
                auth_positions.append((center_x, center_y, raw_name))
                last_authorized_time, last_authorized_name = current_time, raw_name
            
            should_log = raw_name not in active_logs or (current_time - active_logs[raw_name]).total_seconds() > COOLDOWN_SECONDS
            if should_log and incident_collection is not None:
                status = "CRITICAL_BREACH" if raw_name == "Unknown Intruder" else "AUTHORIZED_ACCESS"
                inc_type = "STANDARD_ENTRY"
                payload = {"timestamp": current_time, "incident_type": inc_type, "identity": raw_name, "clearance_status": status, "bounding_boxes": {"body": target['body_box'], "face": target['face_box']}}
                threading.Thread(target=async_db_log, args=(payload, False)).start()
                active_logs[raw_name] = current_time

            color = (0, 0, 255) if "Unknown" in raw_name else ((255, 165, 0) if "Analyzing" in raw_name else (0, 255, 0))
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2)
            cv2.putText(frame, raw_name, (bx1, by1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            if target['face_box']:
                fl, ft, fr, fb = target['face_box']
                cv2.rectangle(frame, (fl, ft), (fr, fb), color, 2)
                cv2.rectangle(frame, (fl, fb - 25), (fr, fb), color, cv2.FILLED)
                cv2.putText(frame, raw_name, (fl + 6, fb - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        if incident_collection is not None and (current_time - last_tailgate_log_time).total_seconds() > TAILGATE_COOLDOWN:
            tailgate_triggered = False
            for ax, ay, resident_name in auth_positions:
                tailgating_intruders = []
                min_distance = float('inf')
                for ux, uy, u_body, u_face in unknown_positions:
                    distance = ((ax - ux)**2 + (ay - uy)**2)**0.5
                    if distance < TAILGATE_DISTANCE_LIMIT:
                        tailgating_intruders.append({"body": u_body, "face": u_face})
                        min_distance = min(min_distance, distance)
                
                if tailgating_intruders:
                    tailgate_triggered = True
                    payload = {"timestamp": current_time, "date_string": current_time.strftime("%Y-%m-%d %H:%M:%S"), "incident_type": "TAILGATING_SPATIAL", "clearance_status": "HIGH_ALERT_BREACH", "resident_compromised": resident_name, "metrics": {"intruder_count": len(tailgating_intruders), "closest_distance_pixels": round(min_distance, 1), "time_delta_seconds": 0.0}, "intruders_data": tailgating_intruders}
                    threading.Thread(target=async_db_log, args=(payload, True)).start()
                    last_tailgate_log_time = current_time
                    break

            if not tailgate_triggered and last_authorized_time and unknown_positions:
                time_delta = (current_time - last_authorized_time).total_seconds()
                if 0 < time_delta <= TAILGATE_TIME_WINDOW:
                    tailgating_intruders = [{"body": u[2], "face": u[3]} for u in unknown_positions]
                    tailgate_triggered = True
                    payload = {"timestamp": current_time, "date_string": current_time.strftime("%Y-%m-%d %H:%M:%S"), "incident_type": "TAILGATING_TEMPORAL", "clearance_status": "HIGH_ALERT_BREACH", "resident_compromised": last_authorized_name, "metrics": {"intruder_count": len(tailgating_intruders), "closest_distance_pixels": None, "time_delta_seconds": round(time_delta, 2)}, "intruders_data": tailgating_intruders}
                    threading.Thread(target=async_db_log, args=(payload, True)).start()
                    last_tailgate_log_time = current_time

        with FRAME_LOCK:
            LATEST_FRAME = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# --- 6. FULLSCREEN KIOSK UI ---
class BlockEntryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Block Entry Watchdog")
        
        self.state("zoomed")
        self.bind("<Escape>", lambda e: self.destroy())
        self.configure(fg_color="#F8FAFC")

        self.main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_container.pack(expand=True, fill="both")

        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="#FFFFFF", height=90, corner_radius=0)
        self.header_frame.pack(fill="x", side="top")
        
        ctk.CTkLabel(self.header_frame, text="BLOCK SECURITY SCANNER", font=("Helvetica", 32, "bold"), text_color="#0F172A").pack(pady=(15, 2))
        ctk.CTkLabel(self.header_frame, text="Live Tailgating & Entry Verification Active", font=("Helvetica", 18, "bold"), text_color="#10B981").pack(pady=(0, 15))
        
        self.video_canvas = ctk.CTkLabel(self.main_container, text="")
        self.video_canvas.pack(expand=True)
        
        self.update_video_feed()

    def update_video_feed(self):
        with FRAME_LOCK:
            if LATEST_FRAME is not None:
                img = Image.fromarray(LATEST_FRAME)
                imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(800, 600))
                self.video_canvas.configure(image=imgtk)
                
        self.after(30, self.update_video_feed)

if __name__ == "__main__":
    ai_thread = threading.Thread(target=run_ai_engine, daemon=True)
    ai_thread.start()
    app = BlockEntryApp()
    app.mainloop()