from datetime import datetime
from typing import Any, Optional

import numpy as np

from db.mongo import get_db
from utils import l2_normalize


def _students_collection():
    return get_db().students


def _attendance_collection():
    return get_db().attendance


def _change_log_collection():
    return get_db().change_logs


def save_student(school_name, roll_no, session, name, class_name, section, subject, face_path, face_encoding):
    embedding = l2_normalize(np.array(face_encoding, dtype=np.float32)).tolist()
    _students_collection().update_one(
        {"school_name": school_name, "roll_no": roll_no, "session": session},
        {"$set": {
            "school_name": school_name,
            "roll_no": roll_no,
            "session": session,
            "name": name,
            "class_name": class_name,
            "section": section,
            "subject": subject,
            "face_path": face_path,
            "embedding": embedding,
            "updated_at": datetime.utcnow(),
        }, "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True,
    )


def get_students(school_name, class_name, section, subject=None):
    query = {"school_name": school_name, "class_name": class_name, "section": section}
    if subject:
        query["subject"] = subject
    rows = list(_students_collection().find(query, {"roll_no": 1, "name": 1, "embedding": 1, "_id": 0}))
    return [r["roll_no"] for r in rows], [r.get("name") for r in rows], [l2_normalize(np.array(r["embedding"], dtype=np.float32)) for r in rows]


def get_all_students_for_attendance(school_name, class_name, section, subject=None):
    query = {"school_name": school_name, "class_name": class_name, "section": section}
    if subject:
        query["subject"] = subject
    rows = _students_collection().find(query, {"roll_no": 1, "name": 1, "_id": 0})
    return {row["roll_no"]: row.get("name") for row in rows}


def get_student_embedding(school_name, roll_no, session):
    row = _students_collection().find_one(
        {"school_name": school_name, "roll_no": roll_no, "session": session},
        {"embedding": 1, "name": 1, "class_name": 1, "section": 1, "subject": 1, "_id": 0},
    )
    if not row:
        return None
    row["embedding"] = np.array(row["embedding"], dtype=np.float32)
    return row


def update_student_embedding(school_name, roll_no, session, new_embedding):
    emb = l2_normalize(np.array(new_embedding, dtype=np.float32)).tolist()
    result = _students_collection().update_one(
        {"school_name": school_name, "roll_no": roll_no, "session": session},
        {"$set": {"embedding": emb, "updated_at": datetime.utcnow()}},
    )
    return result.modified_count > 0


def get_students_by_filters(school_name, session, class_name=None, section=None, subject=None):
    query: dict[str, Any] = {"school_name": school_name, "session": session}
    if class_name:
        query["class_name"] = class_name
    if section:
        query["section"] = section
    if subject:
        query["subject"] = subject
    rows = _students_collection().find(query, {"_id": 0})
    out = []
    for row in rows:
        row["embedding"] = np.array(row["embedding"], dtype=np.float32) if row.get("embedding") else None
        out.append(row)
    return out


def get_students_for_export(school_name, class_name=None, section=None, subject=None):
    query: dict[str, Any] = {"school_name": school_name}
    if class_name:
        query["class_name"] = class_name
    if section:
        query["section"] = section
    if subject:
        query["subject"] = subject
    cursor = _students_collection().find(query, {"school_name": 1, "roll_no": 1, "name": 1, "class_name": 1, "section": 1, "subject": 1, "_id": 0}).sort(
        [("school_name", 1), ("class_name", 1), ("section", 1), ("roll_no", 1)]
    )
    return [(r.get("school_name"), r.get("roll_no"), r.get("name"), r.get("class_name"), r.get("section"), r.get("subject")) for r in cursor]


def save_attendance(school_name, roll_no, session, student_name, class_name, section, subject, similarity_score, status, date, time):
    _attendance_collection().insert_one({
        "school_name": school_name,
        "roll_no": roll_no,
        "session": session,
        "student_name": student_name,
        "class_name": class_name,
        "section": section,
        "subject": subject,
        "similarity_score": similarity_score,
        "status": status,
        "date": date,
        "time": time,
        "created_at": datetime.utcnow(),
    })


def get_attendance_on_date(school_name, date, roll_no=None, class_name=None, section=None, subject=None):
    query: dict[str, Any] = {"school_name": school_name, "date": date}
    if roll_no:
        query["roll_no"] = roll_no
    if class_name:
        query["class_name"] = class_name
    if section:
        query["section"] = section
    if subject:
        query["subject"] = subject
    rows = _attendance_collection().find(query, {"_id": 0}).sort([("school_name", 1), ("class_name", 1), ("section", 1), ("roll_no", 1)])
    return [(r.get("school_name"), r.get("roll_no"), r.get("student_name"), r.get("class_name"), r.get("section"), r.get("subject"), r.get("status"), r.get("date")) for r in rows]


def get_attendance_in_range(school_name, start_date, end_date, roll_no=None, class_name=None, section=None, subject=None):
    query: dict[str, Any] = {"school_name": school_name, "date": {"$gte": start_date, "$lte": end_date}}
    if roll_no:
        query["roll_no"] = roll_no
    if class_name:
        query["class_name"] = class_name
    if section:
        query["section"] = section
    if subject:
        query["subject"] = subject
    rows = _attendance_collection().find(query, {"_id": 0}).sort([("roll_no", 1), ("date", 1)])
    return [(r.get("school_name"), r.get("roll_no"), r.get("student_name"), r.get("class_name"), r.get("section"), r.get("subject"), r.get("status"), r.get("date")) for r in rows]


def delete_student_by_roll_no(school_name, roll_no, session):
    students_deleted = _students_collection().delete_one({"school_name": school_name, "roll_no": roll_no, "session": session}).deleted_count
    attendance_deleted = _attendance_collection().delete_many({"school_name": school_name, "roll_no": roll_no, "session": session}).deleted_count
    return students_deleted > 0 or attendance_deleted > 0


def delete_class_data(school_name, class_name, session, section=None, subject=None):
    query: dict[str, Any] = {"school_name": school_name, "class_name": class_name, "session": session}
    if section:
        query["section"] = section
    if subject:
        query["subject"] = subject
    students_deleted = _students_collection().delete_many(query).deleted_count
    attendance_deleted = _attendance_collection().delete_many(query).deleted_count
    return students_deleted > 0 or attendance_deleted > 0


def delete_student_from_database_only(school_name, roll_no, session):
    query = {"school_name": school_name, "roll_no": roll_no, "session": session}
    student = _students_collection().find_one(query, {"_id": 0, "embedding": 0, "face_path": 0})
    if not student:
        return None
    _students_collection().delete_one(query)
    return student


def delete_student_from_attendance_only(school_name, roll_no, session):
    query = {"school_name": school_name, "roll_no": roll_no, "session": session}
    student = _students_collection().find_one(query, {"_id": 0, "embedding": 0, "face_path": 0}) or {}
    attendance_count = _attendance_collection().count_documents(query)
    if attendance_count == 0:
        return None
    _attendance_collection().delete_many(query)
    return {
        "roll_no": roll_no,
        "school_name": school_name,
        "session": session,
        "attendance_records_deleted": attendance_count,
        "name": student.get("name"),
        "class_name": student.get("class_name"),
        "section": student.get("section"),
        "subject": student.get("subject"),
    }


def delete_student_from_both(school_name, roll_no, session):
    query = {"school_name": school_name, "roll_no": roll_no, "session": session}
    student = _students_collection().find_one(query, {"_id": 0, "embedding": 0, "face_path": 0})
    attendance_count = _attendance_collection().count_documents(query)
    if not student and attendance_count == 0:
        return None
    deleted_from_database = _students_collection().delete_one(query).deleted_count > 0
    _attendance_collection().delete_many(query)
    return {
        "roll_no": roll_no,
        "school_name": school_name,
        "session": session,
        "deleted_from_database": deleted_from_database,
        "attendance_records_deleted": attendance_count,
        "name": student.get("name") if student else None,
        "class_name": student.get("class_name") if student else None,
        "section": student.get("section") if student else None,
        "subject": student.get("subject") if student else None,
    }


def delete_bulk_from_database(school_name, class_name, section, session, subject=None):
    query: dict[str, Any] = {"school_name": school_name, "class_name": class_name, "section": section, "session": session}
    if subject:
        query["subject"] = subject
    count = _students_collection().count_documents(query)
    _students_collection().delete_many(query)
    return count


def delete_bulk_from_attendance(school_name, class_name, section, session, subject=None):
    query: dict[str, Any] = {"school_name": school_name, "class_name": class_name, "section": section, "session": session}
    if subject:
        query["subject"] = subject
    count = _attendance_collection().count_documents(query)
    _attendance_collection().delete_many(query)
    return count


def delete_bulk_from_both_tables(school_name, class_name, section, session, subject=None):
    query: dict[str, Any] = {"school_name": school_name, "class_name": class_name, "section": section, "session": session}
    if subject:
        query["subject"] = subject
    students_count = _students_collection().count_documents(query)
    attendance_count = _attendance_collection().count_documents(query)
    _students_collection().delete_many(query)
    _attendance_collection().delete_many(query)
    return {"students_deleted": students_count, "attendance_records_deleted": attendance_count}


def get_enrollment_stats():
    total_students = _students_collection().count_documents({})
    pipeline = [
        {"$group": {"_id": {"school_name": "$school_name", "class_name": "$class_name", "section": "$section", "subject": "$subject"}, "count": {"$sum": 1}}},
        {"$sort": {"_id.school_name": 1, "_id.class_name": 1, "_id.section": 1, "_id.subject": 1}},
    ]
    rows = list(_students_collection().aggregate(pipeline))
    stats = {"total_students": total_students, "by_school": []}
    school_dict: dict[str, Any] = {}
    for row in rows:
        school_name = row["_id"].get("school_name")
        class_name = row["_id"].get("class_name")
        section = row["_id"].get("section")
        subject = row["_id"].get("subject") or "No Subject"
        count = row["count"]
        school_entry = school_dict.setdefault(school_name, {"school_name": school_name, "total": 0, "by_class": {}})
        school_entry["total"] += count
        class_entry = school_entry["by_class"].setdefault(class_name, {"class_name": class_name, "total": 0, "by_section": {}})
        class_entry["total"] += count
        section_entry = class_entry["by_section"].setdefault(section, {"section": section, "total": 0, "by_subject": []})
        section_entry["total"] += count
        section_entry["by_subject"].append({"subject": subject, "count": count})
    for school_data in school_dict.values():
        item = {"school_name": school_data["school_name"], "total": school_data["total"], "by_class": []}
        for class_data in school_data["by_class"].values():
            item["by_class"].append({"class_name": class_data["class_name"], "total": class_data["total"], "by_section": list(class_data["by_section"].values())})
        stats["by_school"].append(item)
    return stats


def log_database_change(school_name=None, class_name=None, section=None, subject=None, roll_no=None, session=None, change_type=None, endpoint_name=None, details=None):
    _change_log_collection().insert_one({
        "school_name": school_name,
        "class_name": class_name,
        "section": section,
        "subject": subject,
        "roll_no": roll_no,
        "session": session,
        "change_type": change_type,
        "endpoint_name": endpoint_name,
        "details": details,
        "timestamp": datetime.utcnow(),
    })


def get_database_change_log(school_name=None, roll_no=None, session=None, class_name=None, section=None, subject=None, change_type=None, start_date=None, end_date=None):
    query: dict[str, Any] = {}
    for key, value in [("school_name", school_name), ("roll_no", roll_no), ("session", session), ("class_name", class_name), ("section", section), ("subject", subject), ("change_type", change_type)]:
        if value:
            query[key] = value
    if start_date or end_date:
        ts: dict[str, Any] = {}
        if start_date:
            ts["$gte"] = datetime.fromisoformat(start_date)
        if end_date:
            ts["$lte"] = datetime.fromisoformat(f"{end_date}T23:59:59.999")
        query["timestamp"] = ts
    rows = _change_log_collection().find(query, {"_id": 0}).sort([("timestamp", -1)])
    out = []
    for row in rows:
        row["timestamp"] = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if row.get("timestamp") else None
        out.append(row)
    return out


def get_change_log_as_csv(school_name=None, roll_no=None, session=None, class_name=None, section=None, subject=None, change_type=None, start_date=None, end_date=None):
    import csv
    import io

    logs = get_database_change_log(school_name, roll_no, session, class_name, section, subject, change_type, start_date, end_date)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["school_name", "class_name", "section", "subject", "roll_no", "session", "change_type", "endpoint_name", "details", "timestamp"])
    for log in logs:
        writer.writerow([log.get("school_name") or "", log.get("class_name") or "", log.get("section") or "", log.get("subject") or "", log.get("roll_no") or "", log.get("session") or "", log.get("change_type") or "", log.get("endpoint_name") or "", log.get("details") or "", log.get("timestamp") or ""])
    output.seek(0)
    return output.getvalue()
