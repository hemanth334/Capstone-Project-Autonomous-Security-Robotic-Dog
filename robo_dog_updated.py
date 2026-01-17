import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import uuid
import faiss
import insightface
import onnxruntime as ort
import winsound
import threading
import time
from twilio.rest import Client
from ultralytics import YOLO

# ==============================
# Twilio Credentials
# ==============================
TWILIO_ACCOUNT_SID = "AC7dbf7b7469aa80655a2a350a517bbbe0"
TWILIO_AUTH_TOKEN = "1ef5b2a9e51f301d7133fa3ecbb2ff6b"
TWILIO_PHONE_NUMBER = "+12187182229"
MY_PHONE_NUMBER = "+91 xxxxx xxxxx"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Async SMS sender
def send_sms_async(body, to):
    def send():
        try:
            message = twilio_client.messages.create(
                body=body,
                from_=TWILIO_PHONE_NUMBER,
                to=to
            )
            print(f"📩 SMS sent, status: {message.status}")
        except Exception as e:
            print(f"❌ SMS send error: {e}")
    threading.Thread(target=send).start()

class FixedInsightFaceSystem:
    def __init__(self):  # Fixed: __init__ not _init_
        print("🚀 Initializing RoboDog Security System...")
        self.setup_gpu()
        self.setup_insightface()
        self.yolo_model = YOLO("yolov8n.pt")
        self.dimension = 512
        self.index = faiss.IndexFlatIP(self.dimension)
        print("💻 FAISS using CPU")
        self.face_names = []
        self.face_embeddings = []
        self.face_metadata = []
        self.stats = {'faces_added': 0, 'total_detections': 0, 'total_recognitions': 0}
        self.database_file = 'fixed_insightface_database.pkl'
        self.load_database()
        self.resize_factor = 0.8
        self.similarity_threshold = 0.3
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()
        self.intruder_folder = "intruders"
        os.makedirs(self.intruder_folder, exist_ok=True)
        self.last_sms_time = 0
        self.sms_cooldown = 30  # seconds

        # Accuracy counters
        self.total_faces_seen = 0
        self.correct_recognitions = 0

        print(f"✅ RoboDog ready: {len(self.face_names)} family members loaded")

    def setup_gpu(self):
        try:
            providers = ort.get_available_providers()
            self.gpu_available = 'CUDAExecutionProvider' in providers
            self.providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.gpu_available else ['CPUExecutionProvider']
            device_type = "GPU" if self.gpu_available else "CPU"
            print(f"🔥 ONNX Runtime using {device_type}")
        except Exception as e:
            print(f"❌ GPU setup error: {e}")
            self.gpu_available = False
            self.providers = ['CPUExecutionProvider']

    def setup_insightface(self):
        try:
            self.app = insightface.app.FaceAnalysis(
                providers=self.providers,
                allowed_modules=['detection', 'recognition']
            )
            self.app.prepare(ctx_id=0 if self.gpu_available else -1, det_size=(640, 640))
            device_type = "GPU" if self.gpu_available else "CPU"
            print(f"✅ InsightFace loaded on {device_type}")
        except Exception as e:
            print(f"❌ InsightFace setup error: {e}")
            exit(1)

    def load_database(self):
        try:
            if os.path.exists(self.database_file):
                with open(self.database_file, 'rb') as f:
                    data = pickle.load(f)
                self.face_names = data.get('face_names', [])
                self.face_embeddings = data.get('face_embeddings', [])
                self.face_metadata = data.get('face_metadata', [])
                if self.face_embeddings:
                    embeddings_array = np.array(self.face_embeddings, dtype=np.float32)
                    norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
                    embeddings_array = embeddings_array / norms
                    self.index.add(embeddings_array)
                print(f"📖 Loaded {len(self.face_names)} family members")
        except Exception as e:
            print(f"❌ Load error: {e}")

    def save_database(self):
        try:
            data = {
                'face_names': self.face_names,
                'face_embeddings': self.face_embeddings,
                'face_metadata': self.face_metadata,
                'stats': self.stats,
                'version': '2.0_fixed',
                'saved_at': datetime.now().isoformat()
            }
            with open(self.database_file, 'wb') as f:
                pickle.dump(data, f)
            print(f"💾 Database saved with {len(self.face_names)} members")
        except Exception as e:
            print(f"❌ Save error: {e}")

    def add_face_to_database(self, name, face_embedding):
        try:
            face_embedding_normalized = face_embedding / np.linalg.norm(face_embedding)
            self.index.add(face_embedding_normalized.reshape(1, -1).astype('float32'))
            self.face_names.append(name)
            self.face_embeddings.append(face_embedding_normalized.tolist())
            self.face_metadata.append({
                'name': name,
                'timestamp': datetime.now().isoformat(),
                'id': str(uuid.uuid4())
            })
            self.stats['faces_added'] += 1
            self.save_database()
            print(f"✅ Added {name} (Total: {len(self.face_names)})")
            return True
        except Exception as e:
            print(f"❌ Error adding face: {e}")
            return False

    def recognize_face(self, face_embedding):
        try:
            if self.index.ntotal == 0:
                return "Unknown", 0.0
            face_embedding_normalized = face_embedding / np.linalg.norm(face_embedding)
            similarities, indices = self.index.search(
                face_embedding_normalized.reshape(1, -1).astype('float32'), 1
            )
            similarity = float(similarities[0][0])
            if similarity > self.similarity_threshold:
                idx = int(indices[0][0])
                return self.face_names[idx], similarity
            else:
                return "Unknown", similarity
        except Exception as e:
            print(f"❌ Recognition error: {e}")
            return "Unknown", 0.0

    def detect_motion(self, frame):
        fg_mask = self.bg_subtractor.apply(frame)
        motion_level = np.sum(fg_mask > 0)
        return motion_level > 5000

    def liveness_check(self, face):
        bbox = face.bbox
        h, w = bbox[3] - bbox[1], bbox[2] - bbox[0]
        return h > 60 and w > 60

    def trigger_alert(self, frame, reason="Unknown intruder", send_sms=False):
        print(f"🚨 ALERT! {reason}")
        try:
            winsound.Beep(1000, 500)
        except:
            pass

        filename = os.path.join(
            self.intruder_folder,
            f"intruder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        )
        cv2.imwrite(filename, frame)
        print(f"📸 Intruder snapshot saved: {filename}")

        if send_sms:
            current_time = time.time()
            if current_time - self.last_sms_time > self.sms_cooldown:
                send_sms_async(f"🚨 RoboDog Alert: {reason} at {datetime.now().strftime('%H:%M:%S')}", MY_PHONE_NUMBER)
                self.last_sms_time = current_time

    def run_detection(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open webcam.")
            return
        print("📷 RoboDog Security running... Press 'q' to quit, 'n' to add new face")

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            resized_frame = cv2.resize(frame, None, fx=self.resize_factor, fy=self.resize_factor)
            motion_detected = self.detect_motion(resized_frame)
            results = self.yolo_model(resized_frame, verbose=False)

            faces_detected_in_frame = 0

            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    if cls_id == 0 and conf > 0.3:  # Person class
                        person_crop = resized_frame[y1:y2, x1:x2]
                        if person_crop.size == 0:
                            continue
                            
                        faces = self.app.get(person_crop)
                        faces_detected_in_frame += len(faces)

                        for face in faces:
                            # Get face bounding box coordinates
                            fx1, fy1, fx2, fy2 = face.bbox.astype(int)
                            # Convert to full frame coordinates
                            fx1, fy1, fx2, fy2 = x1 + fx1, y1 + fy1, x1 + fx2, y1 + fy2

                            embedding = face.normed_embedding
                            name, sim = self.recognize_face(embedding)

                            live = self.liveness_check(face)
                            if not live:
                                name = "Spoof"

                            # Accuracy tracking
                            self.total_faces_seen += 1
                            if name not in ["Unknown", "Spoof"]:
                                self.correct_recognitions += 1
                            accuracy = 0.0
                            if self.total_faces_seen > 0:
                                accuracy = (self.correct_recognitions / self.total_faces_seen) * 100

                            color = (0, 255, 0) if name not in ["Unknown", "Spoof"] else (0, 0, 255)
                            cv2.rectangle(resized_frame, (fx1, fy1), (fx2, fy2), color, 2)
                            cv2.putText(resized_frame, f"{name} ({sim:.2f})", (fx1, fy1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                            # Show real-time accuracy
                            cv2.putText(resized_frame, f"Accuracy: {accuracy:.2f}%", (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                            # Trigger SMS only for unknown faces
                            if name == "Unknown" and motion_detected:
                                self.trigger_alert(resized_frame, "Unknown intruder detected", send_sms=True)

            cv2.imshow("RoboDog Security", resized_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('n'):
                if faces_detected_in_frame > 0:
                    entered_name = input("Enter name: ").strip()
                    if entered_name:
                        # Get the first detected face for adding to database
                        person_crop = resized_frame[y1:y2, x1:x2]
                        faces = self.app.get(person_crop)
                        if faces:
                            self.add_face_to_database(entered_name, faces[0].normed_embedding)

        cap.release()
        cv2.destroyAllWindows()

        # Print final overall accuracy
        if self.total_faces_seen > 0:
            final_accuracy = (self.correct_recognitions / self.total_faces_seen) * 100
            print(f"\n📊 Overall Accuracy: {final_accuracy:.2f}% ({self.correct_recognitions}/{self.total_faces_seen})")
        else:
            print("\n📊 No faces detected, accuracy unavailable.")

def main():
    system = FixedInsightFaceSystem()
    try:
        system.run_detection()
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    finally:
        system.save_database()
        print("✅ RoboDog stopped!")

if __name__ == "__main__":  # Fixed: __name__ not _name_
    main()