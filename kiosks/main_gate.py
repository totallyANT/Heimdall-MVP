import customtkinter as ctk
import cv2
import face_recognition
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient

# --- 1. GLOBAL STATE & THEME ---
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

LATEST_FRAME = None
FRAME_LOCK = threading.Lock()

# Toggle switches to control what the camera looks for
SCAN_MODE = "IDLE" 
QR_RESULT = None

# --- 2. MONGODB CONFIGURATION ---
MONGO_URI = "mongodb+srv://poojithamalleswari_db_user:bwBTe9tkuhve4goF@cluster0.3zl7rtj.mongodb.net/"

try:
    print("Connecting to MongoDB Atlas cluster...")
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    
    # Primary Database Mapping based on Schema
    db_admin_res = mongo_client["admin_res"]
    db_heimdall = mongo_client["heimdall_security"]
    
    # Collections
    residents_collection = db_admin_res["residents"]
    worker_passes_collection = db_admin_res["worker_passes"]
    delivery_collection = db_admin_res["delivery_notifications"]
    guest_passes_collection = db_admin_res["guest_passes"]
    group_passes_collection = db_admin_res["group_passes"]
    
    # Logs
    incident_collection = db_heimdall["alert_actions"]
    
    print("MongoDB Connected Successfully.")
except Exception as e:
    print(f"MongoDB Connection Failed: {e}")
    residents_collection = None
    worker_passes_collection = None
    delivery_collection = None
    guest_passes_collection = None
    group_passes_collection = None
    incident_collection = None

def async_db_log(payload):
    if incident_collection is None: return
    try:
        incident_collection.insert_one(payload)
        print(f"[DB LOG] Saved Entry: {payload.get('identity', 'Unknown')}")
    except Exception as e:
        pass

# --- 3. LIGHTWEIGHT CAMERA ENGINE ---
def run_camera_engine():
    global LATEST_FRAME, SCAN_MODE, QR_RESULT
    cap = cv2.VideoCapture(0)
    qr_detector = cv2.QRCodeDetector() 
    
    while True:
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.resize(frame, (640, 480))

        if SCAN_MODE == "QR":
            data, bbox, _ = qr_detector.detectAndDecode(frame)
            if bbox is not None and len(bbox) > 0:
                pts = bbox[0].astype(int)
                for i in range(len(pts)):
                    cv2.line(frame, tuple(pts[i]), tuple(pts[(i+1) % len(pts)]), (0, 255, 255), 3)
                    
            if data and QR_RESULT is None:
                clean_data = data.strip()
                QR_RESULT = clean_data
                print(f"\n[MAIN GATE] Successfully locked onto QR Code: '{clean_data}'")

        elif SCAN_MODE == "PROCESSING":
            pass 

        with FRAME_LOCK:
            LATEST_FRAME = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
        time.sleep(0.03)

# --- 4. BACKGROUND SECURITY SWEEPER ---
def database_sweeper():
    """
    Runs continuously in the background. Wakes up once an hour to 
    delete facial biometrics from expired guest passes.
    """
    print("[SYSTEM] Background Security Sweeper Initialized.")
    while True:
        if guest_passes_collection is not None:
            try:
                today = datetime.now().date()
                
                # Find all passes that currently have a face stored
                active_passes = guest_passes_collection.find({"embedding": {"$exists": True, "$ne": None}})
                
                for g_pass in active_passes:
                    entry_str = g_pass.get("entry_date")
                    duration = g_pass.get("duration_days", 1)
                    
                    if entry_str:
                        # Convert string to date and calculate expiration
                        entry_date = datetime.strptime(entry_str, "%Y-%m-%d").date()
                        expiration_date = entry_date + timedelta(days=duration)
                        
                        # If the pass has expired
                        if today > expiration_date:
                            guest_passes_collection.update_one(
                                {"_id": g_pass["_id"]},
                                {
                                    "$unset": {"embedding": ""}, 
                                    "$set": {"status": "expired"}
                                }
                            )
                            print(f"[SECURITY] Pass {g_pass.get('passId')} expired. Biometric data securely wiped.")
                            
            except Exception as e:
                print(f"[ERROR] Sweeper encountered an issue: {e}")
                
        # Sleep for 1 hour (3600 seconds) before sweeping again
        time.sleep(3600)

# --- 5. MAIN GATE KIOSK APPLICATION ---
class MainGateApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Main Gate Kiosk")
        self.geometry("900x750")
        self.configure(fg_color="#F8FAFC")
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(expand=True, fill="both")

        self.build_idle_screen()
        self.build_menu_screen()
        self.build_resident_setup_screen()
        self.build_visiting_help_screen()
        self.build_vendor_screen()
        self.build_visitor_screen()
        self.build_status_screen()
        
        self.update_video_feed()
        self.show_screen(self.idle_frame)

    def show_screen(self, frame_to_show):
        for frame in [self.idle_frame, self.menu_frame, self.resident_setup_frame, 
                      self.visiting_help_frame, self.vendor_frame, self.visitor_frame, 
                      self.status_frame]:
            frame.pack_forget()
        frame_to_show.pack(expand=True, fill="both")

    # --- SCREENS ---
    def build_idle_screen(self):
        self.idle_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        center_frame = ctk.CTkFrame(self.idle_frame, fg_color="transparent")
        center_frame.pack(expand=True)

        ctk.CTkLabel(center_frame, text="MAIN GATE TERMINAL", font=("Helvetica", 42, "bold"), text_color="#0F172A").pack(pady=(0, 10))
        ctk.CTkLabel(center_frame, text="Touch below to begin", font=("Helvetica", 22), text_color="#64748B").pack(pady=(0, 50))
        ctk.CTkButton(center_frame, text="Start Access Request", font=("Helvetica", 24, "bold"), height=80, width=400, corner_radius=10, command=lambda: self.show_screen(self.menu_frame)).pack()

    def build_menu_screen(self):
        self.menu_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        ctk.CTkLabel(self.menu_frame, text="Select Access Type", font=("Helvetica", 32, "bold"), text_color="#0F172A").pack(pady=(40, 20))
        primary_frame = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        primary_frame.pack(pady=10)
        
        # UI UPDATE: Adjusted widths to fit 3 buttons nicely in a single row
        ctk.CTkButton(primary_frame, text="Visitor", font=("Helvetica", 20, "bold"), height=80, width=250, command=lambda: self.show_screen(self.visitor_frame)).grid(row=0, column=0, padx=10)
        ctk.CTkButton(primary_frame, text="Delivery / Vendor", font=("Helvetica", 20, "bold"), height=80, width=250, command=lambda: self.show_screen(self.vendor_frame)).grid(row=0, column=1, padx=10)
        
        # NEW WORKER ENTRY BUTTON
        ctk.CTkButton(primary_frame, text="Worker Entry", font=("Helvetica", 20, "bold"), height=80, width=250, command=self.start_qr_scan).grid(row=0, column=2, padx=10)
        
        ctk.CTkLabel(self.menu_frame, text="Administration & Setup", font=("Helvetica", 18, "bold"), text_color="#64748B").pack(pady=(60, 10))
        secondary_frame = ctk.CTkFrame(self.menu_frame, fg_color="transparent")
        secondary_frame.pack(pady=10)
        
        ctk.CTkButton(secondary_frame, text="Resident Registration", font=("Helvetica", 18), height=50, width=220, fg_color="#475569", hover_color="#334155", command=lambda: self.show_screen(self.resident_setup_frame)).grid(row=0, column=0, padx=15)
        ctk.CTkButton(secondary_frame, text="Worker / Help Setup", font=("Helvetica", 18), height=50, width=220, fg_color="#475569", hover_color="#334155", command=lambda: self.show_screen(self.visiting_help_frame)).grid(row=0, column=1, padx=15)
        ctk.CTkButton(self.menu_frame, text="Cancel", font=("Helvetica", 18), fg_color="#b30000", hover_color="#800000", height=50, width=200, command=self.return_to_home).pack(pady=50)

    def build_resident_setup_screen(self):
        self.resident_setup_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(self.resident_setup_frame, text="Resident Face Sync", font=("Helvetica", 28, "bold"), text_color="#0F172A").pack(pady=10)
        
        self.video_canvas_resident = ctk.CTkLabel(self.resident_setup_frame, text="")
        self.video_canvas_resident.pack(pady=10)
        
        self.res_flat_entry = ctk.CTkEntry(self.resident_setup_frame, placeholder_text="Enter Flat No.", font=("Helvetica", 16), width=250, height=40)
        self.res_flat_entry.pack(pady=5)
        self.res_name_entry = ctk.CTkEntry(self.resident_setup_frame, placeholder_text="Enter Full Name", font=("Helvetica", 16), width=250, height=40)
        self.res_name_entry.pack(pady=5)
        self.res_auth_entry = ctk.CTkEntry(self.resident_setup_frame, placeholder_text="Enter Resident Badge ID", show="*", font=("Helvetica", 16), width=250, height=40)
        self.res_auth_entry.pack(pady=5)
        
        ctk.CTkButton(self.resident_setup_frame, text="Verify Badge & Sync Face", font=("Helvetica", 18), height=50, width=250, command=self.submit_resident_registration).pack(pady=10)
        ctk.CTkButton(self.resident_setup_frame, text="Back", font=("Helvetica", 16), fg_color="#b30000", hover_color="#800000", command=lambda: self.show_screen(self.menu_frame)).pack(pady=10)

    def build_visiting_help_screen(self):
        self.visiting_help_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(self.visiting_help_frame, text="Worker Pass Registration", font=("Helvetica", 28, "bold"), text_color="#0F172A").pack(pady=10)
        
        self.video_canvas_setup = ctk.CTkLabel(self.visiting_help_frame, text="")
        self.video_canvas_setup.pack(pady=10)
        
        self.help_flat_entry = ctk.CTkEntry(self.visiting_help_frame, placeholder_text="Enter Assigned Flat No.", font=("Helvetica", 16), width=250, height=40)
        self.help_flat_entry.pack(pady=10)
        self.help_name_entry = ctk.CTkEntry(self.visiting_help_frame, placeholder_text="Enter Worker Type (e.g. Maid)", font=("Helvetica", 16), width=250, height=40)
        self.help_name_entry.pack(pady=10)
        
        ctk.CTkButton(self.visiting_help_frame, text="Validate Pass & Save Face", font=("Helvetica", 18), height=50, width=300, command=self.submit_help_registration).pack(pady=10)
        ctk.CTkButton(self.visiting_help_frame, text="Back", font=("Helvetica", 16), fg_color="#b30000", hover_color="#800000", command=lambda: self.show_screen(self.menu_frame)).pack(pady=10)

    def build_vendor_screen(self):
        self.vendor_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(self.vendor_frame, text="Delivery / Vendor Access", font=("Helvetica", 28, "bold"), text_color="#0F172A").pack(pady=40)
        
        ctk.CTkButton(self.vendor_frame, text="Check Pre-Approval", font=("Helvetica", 18), height=50, width=300, command=self.check_vendor_approval).pack(pady=10)
        ctk.CTkLabel(self.vendor_frame, text="— OR REQUEST WALK-IN ENTRY —", font=("Helvetica", 14, "bold"), text_color="#64748B").pack(pady=20)
        
        self.vendor_flat_entry = ctk.CTkEntry(self.vendor_frame, placeholder_text="Destination Flat No. (e.g. 202)", font=("Helvetica", 18), width=350, height=50)
        self.vendor_flat_entry.pack(pady=5)
        
        self.vendor_service_entry = ctk.CTkEntry(self.vendor_frame, placeholder_text="Delivery Service (e.g. Myntra)", font=("Helvetica", 18), width=350, height=50)
        self.vendor_service_entry.pack(pady=5)
        
        ctk.CTkButton(self.vendor_frame, text="Generate Delivery Pass", font=("Helvetica", 18, "bold"), height=50, width=350, fg_color="#cc7000", hover_color="#b35f00", command=self.process_vendor_request).pack(pady=20)
        ctk.CTkButton(self.vendor_frame, text="Back", font=("Helvetica", 16), fg_color="#b30000", hover_color="#800000", command=lambda: self.show_screen(self.menu_frame)).pack(pady=10)

    def build_visitor_screen(self):
        self.visitor_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(self.visitor_frame, text="Visitor Entry", font=("Helvetica", 28, "bold"), text_color="#0F172A").pack(pady=40)
        
        ctk.CTkButton(self.visitor_frame, text="Scan Mobile QR Code", font=("Helvetica", 20), height=50, width=350, command=self.start_qr_scan).pack(pady=10)
        ctk.CTkLabel(self.visitor_frame, text="— OR REQUEST WALK-IN ENTRY —", font=("Helvetica", 14, "bold"), text_color="#64748B").pack(pady=20)
        
        self.visitor_flat_entry = ctk.CTkEntry(self.visitor_frame, placeholder_text="Destination Flat No. (e.g. 444)", font=("Helvetica", 18), width=350, height=50)
        self.visitor_flat_entry.pack(pady=5)
        
        self.visitor_name_entry = ctk.CTkEntry(self.visitor_frame, placeholder_text="Guest Name", font=("Helvetica", 18), width=350, height=50)
        self.visitor_name_entry.pack(pady=5)
        
        ctk.CTkButton(self.visitor_frame, text="Generate Guest Pass", font=("Helvetica", 18, "bold"), height=50, width=350, fg_color="#059669", hover_color="#047857", command=self.process_visitor_request).pack(pady=20)
        ctk.CTkButton(self.visitor_frame, text="Back", font=("Helvetica", 16), fg_color="#b30000", hover_color="#800000", command=lambda: self.show_screen(self.menu_frame)).pack(pady=10)

    def build_status_screen(self):
        self.status_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.status_msg = ctk.CTkLabel(self.status_frame, text="Awaiting...", font=("Helvetica", 24, "bold"), text_color="#0F172A")
        self.status_msg.pack(pady=30)
        self.video_canvas_status = ctk.CTkLabel(self.status_frame, text="")
        self.video_canvas_status.pack(pady=10)
        ctk.CTkButton(self.status_frame, text="Return to Home", font=("Helvetica", 18), fg_color="#b30000", hover_color="#800000", command=self.return_to_home).pack(pady=20)

    # --- UI UPDATES & RESET ---
    def update_video_feed(self):
        with FRAME_LOCK:
            if LATEST_FRAME is not None:
                img = Image.fromarray(LATEST_FRAME)
                imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(500, 375))
                self.video_canvas_resident.configure(image=imgtk)
                self.video_canvas_setup.configure(image=imgtk)
                self.video_canvas_status.configure(image=imgtk)
        self.after(30, self.update_video_feed)

    def return_to_home(self):
        global SCAN_MODE
        SCAN_MODE = "IDLE"
        self.show_screen(self.idle_frame)

    # --- CONSOLIDATED WALK-IN ENTRY LOGIC ---
    def process_visitor_request(self):
        flat = self.visitor_flat_entry.get()
        name = self.visitor_name_entry.get()

        if not flat or not name:
            self.status_msg.configure(text="Error: Flat Number and Name are required.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(3000, self.return_to_home)
            return

        self.status_msg.configure(text=f"Preparing Pass for {name}...\nPlease look directly at the camera.", text_color="#0F172A")
        self.show_screen(self.status_frame)
        self.after(1500, lambda: self.finalize_visitor_pass(flat, name))

    def finalize_visitor_pass(self, flat, guest_name):
        with FRAME_LOCK:
            if LATEST_FRAME is None: 
                self.status_msg.configure(text="❌ Error: Camera Feed Offline.", text_color="#FF0000")
                self.after(3000, self.return_to_home)
                return
            frame_to_scan = LATEST_FRAME.copy()

        face_locations = face_recognition.face_locations(frame_to_scan, model="hog")
        if not face_locations:
            self.status_msg.configure(text="❌ Error: No face detected.\nPass Generation Cancelled.", text_color="#FF0000")
            self.after(3000, self.return_to_home)
            return

        face_encodings = face_recognition.face_encodings(frame_to_scan, face_locations)
        encoding_list = face_encodings[0].tolist()

        resident = residents_collection.find_one({"flat_number": str(flat)})
        resident_id = resident.get("resident_id") if resident else None
        
        today_str = datetime.now().strftime("%Y-%m-%d")

        pass_payload = {
            "passId": None,
            "resident_id": resident_id, 
            "resident_flat": str(flat),
            "guest_name": guest_name,
            "entry_date": today_str,
            "duration_days": 1,
            "status": "pending",
            "embedding": encoding_list
        }

        try:
            result = guest_passes_collection.insert_one(pass_payload)
            self.visitor_flat_entry.delete(0, 'end')
            self.visitor_name_entry.delete(0, 'end')
            
            self.status_msg.configure(text=f"Request Sent to Flat {flat}.\nAwaiting Resident Approval...", text_color="#0F172A")
            threading.Thread(target=self.poll_visitor_approval, args=(result.inserted_id,), daemon=True).start()
        except Exception as e:
            self.status_msg.configure(text=f"❌ Failed to create pass:\n{str(e)}", text_color="#FF0000")
            self.after(5000, self.return_to_home)

    def process_vendor_request(self):
        flat = self.vendor_flat_entry.get()
        service = self.vendor_service_entry.get()

        if not flat or not service:
            self.status_msg.configure(text="Error: Flat Number and Service are required.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(3000, self.return_to_home)
            return

        self.status_msg.configure(text=f"Logging {service} Delivery...\nPlease look directly at the camera.", text_color="#0F172A")
        self.show_screen(self.status_frame)
        self.after(1500, lambda: self.finalize_vendor_pass(flat, service))

    def finalize_vendor_pass(self, flat, service):
        with FRAME_LOCK:
            if LATEST_FRAME is None: 
                self.status_msg.configure(text="❌ Error: Camera Feed Offline.", text_color="#FF0000")
                self.after(3000, self.return_to_home)
                return
            frame_to_scan = LATEST_FRAME.copy()

        face_locations = face_recognition.face_locations(frame_to_scan, model="hog")
        if not face_locations:
            self.status_msg.configure(text="❌ Error: No face detected.\nLogging Cancelled.", text_color="#FF0000")
            self.after(3000, self.return_to_home)
            return

        face_encodings = face_recognition.face_encodings(frame_to_scan, face_locations)
        encoding_list = face_encodings[0].tolist()

        resident = residents_collection.find_one({"flat_number": str(flat)})
        resident_id = resident.get("resident_id") if resident else None
        
        delivery_payload = {
            "delivery_id": None,
            "resident_id": resident_id, 
            "resident_flat": str(flat),
            "delivery_service": service,
            "arrival_window": "1hour",
            "status": "pending",
            "embedding": encoding_list 
        }

        try:
            result = delivery_collection.insert_one(delivery_payload)
            self.vendor_flat_entry.delete(0, 'end')
            self.vendor_service_entry.delete(0, 'end')
            
            self.status_msg.configure(text=f"Delivery Logged.\nAwaiting Resident Approval from Flat {flat}...", text_color="#0F172A")
            threading.Thread(target=self.poll_vendor_approval, args=(result.inserted_id, service, flat), daemon=True).start()
        except Exception as e:
            self.status_msg.configure(text=f"❌ Failed to log delivery:\n{str(e)}", text_color="#FF0000")
            self.after(5000, self.return_to_home)

    def check_vendor_approval(self):
        flat = self.vendor_flat_entry.get()
        if not flat:
            self.status_msg.configure(text="Error: Please enter a Flat Number for Pre-Approval check.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(3000, self.return_to_home)
            return
            
        match = delivery_collection.find_one({"resident_flat": flat, "status": "active"})
        
        if match:
            window = match.get("arrival_window", "").lower()
            
            if window == "1hour":
                self.status_msg.configure(text=f"✅ Delivery Pre-Approval Verified.\nACCESS GRANTED.", text_color="#10B981")
                delivery_collection.update_one({"_id": match["_id"]}, {"$set": {"status": "PASSED_GATE", "gate_entry_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")}})
                threading.Thread(target=async_db_log, args=({"timestamp": datetime.now(), "incident_type": "VENDOR_ENTRY", "identity": match.get('delivery_service', 'Vendor'), "flat": flat},)).start()
            else:
                self.status_msg.configure(text=f"❌ Access Denied: Arrived outside of scheduled '{window}' window.", text_color="#F59E0B")
        else:
            self.status_msg.configure(text=f"❌ No active deliveries found for Flat {flat}.", text_color="#FF0000")
            
        self.show_screen(self.status_frame)
        self.after(4000, self.return_to_home)

    def poll_visitor_approval(self, doc_id):
        max_attempts = 30
        for _ in range(max_attempts):
            time.sleep(2)
            req = guest_passes_collection.find_one({"_id": doc_id})
            if not req: continue
            
            if req["status"] == "active":
                self.after(0, lambda: self.status_msg.configure(text=f"✅ ACCESS GRANTED by Resident!\nPass {req.get('passId', '')} Activated.", text_color="#10B981"))
                self.after(5000, self.return_to_home)
                return
            elif req["status"] == "denied":
                self.after(0, lambda: self.status_msg.configure(text="❌ ACCESS DENIED by Resident.", text_color="#FF0000"))
                self.after(5000, self.return_to_home)
                return
                
        self.after(0, lambda: self.status_msg.configure(text="⏳ No response from resident.\nRequest is still pending.", text_color="#F59E0B"))
        self.after(5000, self.return_to_home)

    def poll_vendor_approval(self, doc_id, service, flat):
        max_attempts = 30
        for _ in range(max_attempts):
            time.sleep(2)
            req = delivery_collection.find_one({"_id": doc_id})
            if not req: continue
            
            if req["status"] in ["active", "PASSED_GATE"]:
                self.after(0, lambda: self.status_msg.configure(text=f"✅ ACCESS GRANTED by Resident!\nDelivery Logged for Flat {flat}.", text_color="#10B981"))
                threading.Thread(target=async_db_log, args=({"timestamp": datetime.now(), "incident_type": "VENDOR_WALK_IN_APPROVED", "identity": service, "flat": flat},)).start()
                self.after(5000, self.return_to_home)
                return
            elif req["status"] == "denied":
                self.after(0, lambda: self.status_msg.configure(text="❌ ACCESS DENIED by Resident.", text_color="#FF0000"))
                self.after(5000, self.return_to_home)
                return
                
        self.after(0, lambda: self.status_msg.configure(text="⏳ No response from resident.\nRequest is still pending.", text_color="#F59E0B"))
        self.after(5000, self.return_to_home)

    # --- DB SETUP LOGIC ---
    def submit_resident_registration(self):
        flat = self.res_flat_entry.get()
        name = self.res_name_entry.get()
        badge_code = self.res_auth_entry.get()

        if not flat or not name or not badge_code:
            self.status_msg.configure(text="Error: Please fill all fields.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(3000, self.return_to_home)
            return

        if residents_collection is None:
            self.status_msg.configure(text="Database offline.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            return

        valid_resident = residents_collection.find_one({
            "flat_number": flat, 
            "full_name": name, 
            "badge": badge_code
        })

        if not valid_resident:
            self.status_msg.configure(text="Error: Invalid Name, Flat, or Badge ID mismatch.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(4000, self.return_to_home)
            return

        with FRAME_LOCK:
            if LATEST_FRAME is None: return
            frame_to_scan = LATEST_FRAME.copy()

        face_locations = face_recognition.face_locations(frame_to_scan, model="hog")
        if not face_locations:
            self.status_msg.configure(text="Error: No face detected. Look directly at camera.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(3000, self.return_to_home)
            return

        face_encodings = face_recognition.face_encodings(frame_to_scan, face_locations)
        encoding_list = face_encodings[0].tolist()
        
        residents_collection.update_one(
            {"_id": valid_resident["_id"]}, 
            {"$set": {"embedding": encoding_list, "is_initialized": True}}
        )

        self.status_msg.configure(text=f"✅ Resident Verified!\nFace Biometrics successfully synced to profile.", text_color="#10B981")
        self.show_screen(self.status_frame)
        self.after(4000, self.return_to_home)

    def submit_help_registration(self):
        flat = self.help_flat_entry.get()
        name = self.help_name_entry.get()
        
        if not flat or not name:
            self.status_msg.configure(text="Error: Please enter both Name and Flat No.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(3000, self.return_to_home)
            return

        worker_pass = worker_passes_collection.find_one({"resident_flat": flat, "worker_name": name, "status": "active"})
        
        if not worker_pass:
            self.status_msg.configure(text=f"Error: No active worker pass found for {name} at Flat {flat}.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(4000, self.return_to_home)
            return
            
        if worker_pass.get("worker_registration") == "done":
            self.status_msg.configure(text="❌ Registration Denied: A face is already mapped to this worker pass.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(4000, self.return_to_home)
            return

        with FRAME_LOCK:
            if LATEST_FRAME is None: return
            frame_to_scan = LATEST_FRAME.copy()

        face_locations = face_recognition.face_locations(frame_to_scan, model="hog")
        if not face_locations:
            self.status_msg.configure(text="Error: No face detected. Look directly at the camera.", text_color="#FF0000")
            self.show_screen(self.status_frame)
            self.after(3000, self.return_to_home)
            return

        face_encodings = face_recognition.face_encodings(frame_to_scan, face_locations)
        encoding_list = face_encodings[0].tolist()

        worker_passes_collection.update_one(
            {"_id": worker_pass["_id"]},
            {"$set": {"embedding": encoding_list, "worker_registration": "done"}}
        )

        self.status_msg.configure(text=f"✅ Identity Secured.\nWorker mapping finalized for Flat {flat}.", text_color="#10B981")
        self.show_screen(self.status_frame)
        self.after(4000, self.return_to_home)

    # --- QR SCAN LOGIC ---
    def start_qr_scan(self):
        global SCAN_MODE, QR_RESULT
        SCAN_MODE = "QR"
        QR_RESULT = None
        self.status_msg.configure(text="Hold QR Code up to Camera...", text_color="#0F172A")
        self.show_screen(self.status_frame)
        self.poll_for_qr()

    def poll_for_qr(self):
        global QR_RESULT, SCAN_MODE
        if SCAN_MODE != "QR": return 
        
        if QR_RESULT is not None:
            scanned_token = QR_RESULT
            SCAN_MODE = "PROCESSING"  
            QR_RESULT = None 
            today_str = datetime.now().strftime("%Y-%m-%d")

            # 1. Check Worker Passes (NEW FEATURE)
            worker_match = worker_passes_collection.find_one({"$or": [{"passId": scanned_token}, {"qrData": scanned_token}], "status": "active"})
            if worker_match:
                self.status_msg.configure(text=f"✅ Welcome {worker_match.get('worker_name', 'Worker')}!\nWorker Pass Verified. ACCESS GRANTED.", text_color="#10B981")
                threading.Thread(target=async_db_log, args=({"timestamp": datetime.now(), "incident_type": "WORKER_ENTRY", "identity": worker_match.get('worker_name', 'Worker'), "flat": worker_match.get('resident_flat', 'Unknown')},)).start()
                self.after(4000, self.return_to_home)
                return

            # 2. Check Guest Passes
            guest_match = guest_passes_collection.find_one({"$or": [{"passId": scanned_token}, {"qrData": scanned_token}], "status": "active"})
            if guest_match:
                if guest_match.get("entry_date") != today_str:
                    self.status_msg.configure(text="❌ Pass date mismatch. Valid for " + guest_match.get("entry_date", "unknown date"), text_color="#FF0000")
                else:
                    self.status_msg.configure(text=f"✅ QR Valid!\nPlease look at the camera for Face Capture...", text_color="#0F172A")
                    self.update()
                    time.sleep(1.5) 
                    
                    with FRAME_LOCK:
                        if LATEST_FRAME is not None:
                            frame_to_scan = LATEST_FRAME.copy()
                            face_locations = face_recognition.face_locations(frame_to_scan, model="hog")
                            if face_locations:
                                face_encodings = face_recognition.face_encodings(frame_to_scan, face_locations)
                                encoding_list = face_encodings[0].tolist()
                                
                                guest_passes_collection.update_one(
                                    {"_id": guest_match["_id"]}, 
                                    {"$set": {"embedding": encoding_list, "status": "used"}}
                                )
                                self.status_msg.configure(text=f"✅ Welcome {guest_match.get('guest_name', 'Guest')}!\nFace Securely Stored. ACCESS GRANTED.", text_color="#10B981")
                            else:
                                self.status_msg.configure(text="❌ Verification Failed: Face could not be localized.", text_color="#FF0000")
                self.after(4000, self.return_to_home)
                return

            # 3. Check Group Passes
            group_match = group_passes_collection.find_one({"$or": [{"passId": scanned_token}, {"qrData": scanned_token}], "status": "active"})
            if group_match:
                if group_match.get("entry_date") != today_str:
                    self.status_msg.configure(text="❌ Pass date mismatch. Valid for " + group_match.get("entry_date", "unknown date"), text_color="#FF0000")
                else:
                    current_uses = group_match.get("used_count", 0)
                    limit = group_match.get("visitor_limit", 1)
                    
                    if current_uses < limit:
                        new_count = current_uses + 1
                        update_payload = {"used_count": new_count}
                        if new_count >= limit:
                            update_payload["status"] = "used"
                            
                        group_passes_collection.update_one({"_id": group_match["_id"]}, {"$set": update_payload})
                        self.status_msg.configure(text=f"✅ Welcome to the {group_match.get('group_name', 'Event')}!\nPasses Used: {new_count} / {limit}", text_color="#10B981")
                    else:
                        self.status_msg.configure(text="❌ Group Pass Visitor Limit Reached.", text_color="#FF0000")
                self.after(4000, self.return_to_home)
                return
            
            self.status_msg.configure(text="❌ Invalid or Expired QR Code.", text_color="#FF0000")
            self.after(4000, self.return_to_home)
            return

        self.after(100, self.poll_for_qr) 


if __name__ == "__main__":
    # Start the Camera Engine
    camera_thread = threading.Thread(target=run_camera_engine, daemon=True)
    camera_thread.start()
    
    # Start the Data Sweeper
    sweeper_thread = threading.Thread(target=database_sweeper, daemon=True)
    sweeper_thread.start()
    
    # Launch UI
    app = MainGateApp()
    app.mainloop()