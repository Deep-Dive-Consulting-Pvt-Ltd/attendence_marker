import io
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
from fastapi import UploadFile

from core.config import app_config
from core.logging import get_logger
from ml.face_engine import get_face_app
from repositories import mongo_repository as repo
from utils import l2_normalize

logger = get_logger(__name__)


def validate_roll_no(roll_no: str) -> bool:
    return bool(roll_no and re.match(r"^[a-zA-Z0-9\-_]+$", roll_no))


def parse_student_folder_name(folder_name: str):
    parts = folder_name.split("_", 1)
    if len(parts) < 2:
        return None, None
    roll_no = parts[0].strip()
    name = parts[1].strip()
    if not validate_roll_no(roll_no) or not name:
        return None, None
    return roll_no, name


def get_current_datetime():
    now = datetime.now()
    return {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S.%f")[:-3], "timestamp": now.strftime("%Y%m%d_%H%M%S_%f")[:-3]}


def get_attendance_crop_path(school_name: str, class_name: str, section: str, subject: Optional[str] = None):
    dt = get_current_datetime()
    base_path = os.path.join(app_config.attendance_crops_dir, dt["date"], school_name, class_name, section)
    if subject:
        base_path = os.path.join(base_path, subject)
    os.makedirs(base_path, exist_ok=True)
    return base_path, dt["timestamp"]


async def process_enrollment(school_name: str, session: str, class_name: Optional[str], section: Optional[str], subject: Optional[str], faces_zip: UploadFile, endpoint_name: str):
    temp_dir = tempfile.mkdtemp(dir=app_config.temp_dir)
    zip_path = os.path.join(temp_dir, "upload.zip")
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(faces_zip.file, f)
    class_dir = os.path.join(app_config.faces_dir, f"{school_name}_{class_name}_{section}")
    os.makedirs(class_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(class_dir)

    enrolled = []
    skipped = []
    processed_roll_nos = set()
    for student_dir in os.listdir(class_dir):
        full_student_path = os.path.join(class_dir, student_dir)
        if not os.path.isdir(full_student_path):
            continue
        roll_no, name = parse_student_folder_name(student_dir)
        if not roll_no:
            skipped.append({"folder": student_dir, "reason": "Invalid folder name format"})
            continue
        if roll_no in processed_roll_nos:
            skipped.append({"folder": student_dir, "reason": f"Duplicate roll number: {roll_no}"})
            continue
        processed_roll_nos.add(roll_no)
        emb_list = []
        for img_file in os.listdir(full_student_path):
            if not img_file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            img = cv2.imread(os.path.join(full_student_path, img_file))
            if img is None:
                continue
            faces = get_face_app().get(img)
            if not faces:
                continue
            face = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
            emb_list.append(l2_normalize(face.embedding))
        if not emb_list:
            skipped.append({"folder": student_dir, "reason": "No valid face embeddings found"})
            continue
        emb_stack = np.stack([np.array(e, dtype=np.float32) for e in emb_list], axis=0)
        mean_emb = l2_normalize(np.mean(emb_stack, axis=0))
        repo.save_student(school_name, roll_no, session, name, class_name, section, subject, full_student_path, mean_emb)
        repo.log_database_change(school_name=school_name, class_name=class_name, section=section, subject=subject, roll_no=roll_no, session=session, change_type="insert", endpoint_name=endpoint_name, details=f"Enrolled student: {name} with {len(emb_list)} images")
        enrolled.append({"roll_no": roll_no, "name": name, "images_processed": len(emb_list)})

    shutil.rmtree(temp_dir)
    result = {"enrolled_students": enrolled, "school_name": school_name, "session": session, "class_name": class_name, "section": section, "subject": subject, "endpoint": endpoint_name}
    if skipped:
        result["skipped"] = skipped
    return result


async def update_embedding_via_period(school_name: str, session: str, alpha: float, class_name: Optional[str], section: Optional[str], subject: Optional[str], faces_zip: UploadFile):
    if alpha >= 1:
        return {"error": "alpha must be less than 1"}
    if alpha < 0:
        return {"error": "alpha must be non-negative"}
    temp_dir = tempfile.mkdtemp(dir=app_config.temp_dir)
    zip_path = os.path.join(temp_dir, "upload.zip")
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(faces_zip.file, f)
    extract_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    updated, added, skipped, processed_roll_nos = [], [], [], set()
    for student_dir in os.listdir(extract_dir):
        full_student_path = os.path.join(extract_dir, student_dir)
        if not os.path.isdir(full_student_path):
            continue
        roll_no, name = parse_student_folder_name(student_dir)
        if not roll_no:
            skipped.append({"folder": student_dir, "reason": "Invalid folder name format"})
            continue
        if roll_no in processed_roll_nos:
            skipped.append({"folder": student_dir, "reason": f"Duplicate roll number: {roll_no}"})
            continue
        processed_roll_nos.add(roll_no)
        emb_list = []
        for img_file in os.listdir(full_student_path):
            if not img_file.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            img = cv2.imread(os.path.join(full_student_path, img_file))
            if img is None:
                continue
            faces = get_face_app().get(img)
            if not faces:
                continue
            face = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
            emb_list.append(l2_normalize(face.embedding))
        if not emb_list:
            skipped.append({"folder": student_dir, "reason": "No valid face embeddings found"})
            continue
        new_emb = l2_normalize(np.mean(np.stack([np.array(e, dtype=np.float32) for e in emb_list], axis=0), axis=0))
        existing = repo.get_student_embedding(school_name, roll_no, session)
        if existing:
            updated_emb = l2_normalize((existing["embedding"] * alpha) + (new_emb * (1 - alpha)))
            repo.update_student_embedding(school_name, roll_no, session, updated_emb)
            repo.log_database_change(school_name=school_name, class_name=existing.get("class_name"), section=existing.get("section"), subject=existing.get("subject"), roll_no=roll_no, session=session, change_type="embedding_update", endpoint_name="/update-embedding-via-period/", details=f"Updated embedding for {existing['name']} with alpha={alpha}, {len(emb_list)} images")
            updated.append({"roll_no": roll_no, "name": existing["name"], "images_processed": len(emb_list), "action": "updated"})
        else:
            student_class = class_name if class_name else "Unknown"
            student_section = section if section else "Unknown"
            repo.save_student(school_name, roll_no, session, name, student_class, student_section, subject, full_student_path, new_emb)
            repo.log_database_change(school_name=school_name, class_name=student_class, section=student_section, subject=subject, roll_no=roll_no, session=session, change_type="insert", endpoint_name="/update-embedding-via-period/", details=f"Added new student: {name} with {len(emb_list)} images")
            added.append({"roll_no": roll_no, "name": name, "images_processed": len(emb_list), "action": "added"})
    shutil.rmtree(temp_dir)
    result = {"school_name": school_name, "session": session, "alpha": alpha, "updated_count": len(updated), "added_count": len(added), "updated_students": updated, "added_students": added}
    if skipped:
        result["skipped"] = skipped
    return result


async def mark_attendance(school_name: str, class_name: str, section: str, subject: Optional[str], photos_zip: UploadFile, threshold: float):
    temp_dir = tempfile.mkdtemp(dir=app_config.temp_dir)
    zip_path = os.path.join(temp_dir, "photos.zip")
    photos_dir = os.path.join(temp_dir, "extracted")
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(photos_zip.file, f)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(photos_dir)

    roll_nos, names, known_encodings = repo.get_students(school_name, class_name, section, subject)
    all_students = repo.get_all_students_for_attendance(school_name, class_name, section, subject)
    if not all_students:
        shutil.rmtree(temp_dir)
        return {"error": "No students enrolled for this class/section", "school_name": school_name}

    present_students, absent_students = [], []
    present_roll_nos = set()
    for root, _, files in os.walk(photos_dir):
        for photo_name in files:
            if not photo_name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            img = cv2.imread(os.path.join(root, photo_name))
            if img is None:
                continue
            faces = get_face_app().get(img)
            for face in faces:
                emb = l2_normalize(np.array(face.embedding, dtype=np.float32))
                scores = np.array([np.dot(emb, k) for k in known_encodings]) if known_encodings else np.array([])
                if len(scores) == 0:
                    continue
                best_idx = np.argmax(scores)
                best_score = scores[best_idx]
                if best_score >= threshold:
                    roll_no = roll_nos[best_idx]
                    student_name = names[best_idx]
                    if roll_no in present_roll_nos:
                        continue
                    present_students.append({"roll_no": roll_no, "name": student_name, "similarity": float(best_score), "status": "P"})
                    crops_dir, timestamp = get_attendance_crop_path(school_name, class_name, section, subject)
                    bbox = face.bbox.astype(int)
                    face_crop = img[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                    cv2.imwrite(os.path.join(crops_dir, f"{roll_no}_{student_name}_{timestamp}.jpg"), face_crop)
                    present_roll_nos.add(roll_no)
    dt = get_current_datetime()
    for student in present_students:
        repo.save_attendance(school_name, student["roll_no"], app_config.default_session, student["name"], class_name, section, subject, student["similarity"], "P", dt["date"], dt["time"])
    for roll_no, name in all_students.items():
        if roll_no not in present_roll_nos:
            absent_students.append({"roll_no": roll_no, "name": name, "status": "A"})
            repo.save_attendance(school_name, roll_no, app_config.default_session, name, class_name, section, subject, 0.0, "A", dt["date"], dt["time"])
    shutil.rmtree(temp_dir)
    return {"school_name": school_name, "class_name": class_name, "section": section, "subject": subject, "date": dt["date"], "time": dt["time"], "total_enrolled": len(all_students), "present_count": len(present_students), "absent_count": len(absent_students), "present_students": present_students, "absent_students": absent_students}


def convert_date_format(date_str: str, from_format: str, to_format: str) -> Optional[str]:
    try:
        return datetime.strptime(date_str, from_format).strftime(to_format)
    except ValueError:
        return None


def validate_date_format(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        return False


def students_csv(students):
    import csv

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["school", "roll_number", "name", "class", "section", "subject"])
    for student in students:
        school, roll_no, name, cls, sec, subj = student
        writer.writerow([school, roll_no, name, cls, sec, subj if subj else ""])
    output.seek(0)
    return output.getvalue()
