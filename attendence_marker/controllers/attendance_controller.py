import io
from datetime import datetime
from typing import Optional

from fastapi.responses import StreamingResponse

from repositories import mongo_repository as repo
from services import attendance_service as service


async def enroll_students_controller(school_name: str, session: str, class_name: Optional[str], section: Optional[str], subject: Optional[str], faces_zip):
    return await service.process_enrollment(school_name, session, class_name, section, subject, faces_zip, "/enroll/")


async def enroll_new_student_controller(school_name: str, session: str, class_name: Optional[str], section: Optional[str], subject: Optional[str], faces_zip):
    return await service.process_enrollment(school_name, session, class_name, section, subject, faces_zip, "/enroll-new-student/")


async def enroll_new_batch_with_replacement_controller(school_name: str, session: str, class_name: Optional[str], section: Optional[str], subject: Optional[str], faces_zip):
    return await service.process_enrollment(school_name, session, class_name, section, subject, faces_zip, "/enroll-new-batch-with-replacement/")


async def update_embedding_controller(school_name: str, session: str, alpha: float, class_name: Optional[str], section: Optional[str], subject: Optional[str], faces_zip):
    return await service.update_embedding_via_period(school_name, session, alpha, class_name, section, subject, faces_zip)


async def mark_attendance_controller(school_name: str, class_name: str, section: str, subject: Optional[str], photos_zip, threshold: float):
    return await service.mark_attendance(school_name, class_name, section, subject, photos_zip, threshold)


def delete_student_controller(school_name: str, roll_no: str, session: str):
    success = repo.delete_student_by_roll_no(school_name, roll_no, session)
    if not success:
        return {"error": "Student not found", "school_name": school_name, "roll_no": roll_no, "session": session}
    repo.log_database_change(school_name=school_name, roll_no=roll_no, session=session, change_type="delete", endpoint_name="/delete-student/", details=f"Deleted student with roll_no {roll_no}, session {session} from both students and attendance tables")
    return {"message": f"Student with roll number {roll_no} from school {school_name}, session {session} deleted successfully", "school_name": school_name, "roll_no": roll_no, "session": session}


def delete_class_controller(school_name: str, class_name: str, session: str, section: Optional[str], subject: Optional[str]):
    success = repo.delete_class_data(school_name, class_name, session, section, subject)
    if not success:
        return {"error": "No matching data found to delete"}
    repo.log_database_change(school_name=school_name, class_name=class_name, section=section, subject=subject, session=session, change_type="delete", endpoint_name="/delete-class/", details=f"Deleted class data for {class_name}, session {session}")
    message = f"Deleted data for school {school_name}, class {class_name}, session {session}"
    if section:
        message += f", section {section}"
    if subject:
        message += f", subject {subject}"
    return {"message": message, "school_name": school_name, "class_name": class_name, "session": session, "section": section, "subject": subject}


def delete_student_database_only_controller(school_name: str, roll_no: str, session: str):
    result = repo.delete_student_from_database_only(school_name, roll_no, session)
    if not result:
        return {"error": f"Student with roll number {roll_no}, session {session} not found in school {school_name}"}
    repo.log_database_change(school_name=school_name, roll_no=roll_no, session=session, class_name=result.get("class_name"), section=result.get("section"), subject=result.get("subject"), change_type="delete", endpoint_name="/delete-student-from-database/", details=f"Deleted student {result.get('name')} from database only (attendance records preserved)")
    return {"message": "Student deleted from database successfully", "deleted_student": result}


def delete_student_attendance_only_controller(school_name: str, roll_no: str, session: str):
    result = repo.delete_student_from_attendance_only(school_name, roll_no, session)
    if not result:
        return {"error": f"No attendance records found for roll number {roll_no}, session {session} in school {school_name}"}
    repo.log_database_change(school_name=school_name, roll_no=roll_no, session=session, class_name=result.get("class_name"), section=result.get("section"), subject=result.get("subject"), change_type="delete", endpoint_name="/delete-student-from-attendance/", details=f"Deleted {result.get('attendance_records_deleted', 0)} attendance records (student database record preserved)")
    return {"message": "Student attendance records deleted successfully", "deleted_info": result}


def delete_student_both_controller(school_name: str, roll_no: str, session: str):
    result = repo.delete_student_from_both(school_name, roll_no, session)
    if not result:
        return {"error": f"Student with roll number {roll_no}, session {session} not found in school {school_name}"}
    repo.log_database_change(school_name=school_name, roll_no=roll_no, session=session, class_name=result.get("class_name"), section=result.get("section"), subject=result.get("subject"), change_type="delete", endpoint_name="/delete-student-from-both/", details=f"Deleted student {result.get('name')} from both database and attendance ({result.get('attendance_records_deleted', 0)} records)")
    return {"message": "Student deleted from both database and attendance records", "deleted_info": result}


def delete_bulk_database_controller(school_name: str, class_name: str, section: str, session: str, subject: Optional[str]):
    count = repo.delete_bulk_from_database(school_name, class_name, section, session, subject)
    if count <= 0:
        return {"error": "No students found matching the criteria"}
    filter_info = f"school={school_name}, class={class_name}, section={section}, session={session}"
    if subject:
        filter_info += f", subject={subject}"
    repo.log_database_change(school_name=school_name, class_name=class_name, section=section, subject=subject, session=session, change_type="delete", endpoint_name="/delete-bulk-from-database/", details=f"Bulk deleted {count} students from database only (attendance records preserved)")
    return {"message": "Bulk delete from database successful", "filter": filter_info, "students_deleted": count}


def delete_bulk_attendance_controller(school_name: str, class_name: str, section: str, session: str, subject: Optional[str]):
    count = repo.delete_bulk_from_attendance(school_name, class_name, section, session, subject)
    if count <= 0:
        return {"error": "No attendance records found matching the criteria"}
    filter_info = f"school={school_name}, class={class_name}, section={section}, session={session}"
    if subject:
        filter_info += f", subject={subject}"
    repo.log_database_change(school_name=school_name, class_name=class_name, section=section, subject=subject, session=session, change_type="delete", endpoint_name="/delete-bulk-from-attendance/", details=f"Bulk deleted {count} attendance records (student database records preserved)")
    return {"message": "Bulk delete from attendance successful", "filter": filter_info, "attendance_records_deleted": count}


def delete_bulk_both_controller(school_name: str, class_name: str, section: str, session: str, subject: Optional[str]):
    result = repo.delete_bulk_from_both_tables(school_name, class_name, section, session, subject)
    if result["students_deleted"] <= 0 and result["attendance_records_deleted"] <= 0:
        return {"error": "No data found matching the criteria"}
    filter_info = f"school={school_name}, class={class_name}, section={section}, session={session}"
    if subject:
        filter_info += f", subject={subject}"
    repo.log_database_change(school_name=school_name, class_name=class_name, section=section, subject=subject, session=session, change_type="delete", endpoint_name="/delete-bulk-from-both/", details=f"Bulk deleted {result['students_deleted']} students and {result['attendance_records_deleted']} attendance records")
    return {"message": "Bulk delete from both database and attendance successful", "filter": filter_info, "students_deleted": result["students_deleted"], "attendance_records_deleted": result["attendance_records_deleted"]}


def enrollment_stats_controller():
    return repo.get_enrollment_stats()


def view_students_controller(school_name: str, class_name: Optional[str], section: Optional[str], subject: Optional[str]):
    students = repo.get_students_for_export(school_name, class_name, section, subject)
    if not students:
        return {"error": "No students found matching the criteria"}
    output = service.students_csv(students)
    filename_parts = [school_name]
    if class_name:
        filename_parts.append(class_name)
    if section:
        filename_parts.append(section)
    if subject:
        filename_parts.append(subject)
    filename = "_".join(filename_parts) + "_students.csv"
    return StreamingResponse(iter([output]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})


def view_attendance_on_date_controller(school_name: str, date: str, roll_no: Optional[str], class_name: Optional[str], section: Optional[str], subject: Optional[str]):
    if not service.validate_date_format(date):
        return {"error": "Invalid date format. Please use DD-MM-YYYY format (e.g., 25-02-2026)"}
    db_date = service.convert_date_format(date, "%d-%m-%Y", "%Y-%m-%d")
    records = repo.get_attendance_on_date(school_name, db_date, roll_no, class_name, section, subject)
    if not records:
        return {"error": "No attendance records found matching the criteria", "date": date}
    attendance_data = []
    for record in records:
        school, roll, name, cls, sec, subj, status, rec_date = record
        display_date = service.convert_date_format(rec_date, "%Y-%m-%d", "%d-%m-%Y")
        attendance_data.append({"date": display_date, "school": school, "roll_number": roll, "name": name, "class": cls, "subject": subj if subj else "", "section": sec, "attendance_record": status})
    return {"total_records": len(attendance_data), "date": date, "school_name": school_name, "data": attendance_data}


def view_attendance_range_controller(school_name: str, start_date: str, end_date: str, roll_no: Optional[str], class_name: Optional[str], section: Optional[str], subject: Optional[str]):
    if not service.validate_date_format(start_date):
        return {"error": "Invalid start_date format. Please use DD-MM-YYYY format (e.g., 25-02-2026)"}
    if not service.validate_date_format(end_date):
        return {"error": "Invalid end_date format. Please use DD-MM-YYYY format (e.g., 27-02-2026)"}
    db_start = service.convert_date_format(start_date, "%d-%m-%Y", "%Y-%m-%d")
    db_end = service.convert_date_format(end_date, "%d-%m-%Y", "%Y-%m-%d")
    if db_start > db_end:
        return {"error": "start_date must be before or equal to end_date"}
    records = repo.get_attendance_in_range(school_name, db_start, db_end, roll_no, class_name, section, subject)
    if not records:
        return {"error": "No attendance records found matching the criteria", "start_date": start_date, "end_date": end_date}
    students_data = {}
    all_dates = set()
    for record in records:
        school, roll, name, cls, sec, subj, status, rec_date = record
        display_date = service.convert_date_format(rec_date, "%Y-%m-%d", "%d-%m-%Y")
        all_dates.add(display_date)
        if roll not in students_data:
            students_data[roll] = {"info": {"school": school, "roll_number": roll, "name": name, "class": cls, "subject": subj if subj else "", "section": sec}, "dates": {}}
        students_data[roll]["dates"][display_date] = status
    sorted_dates = sorted(all_dates, key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
    attendance_data = []
    for roll, student_info in students_data.items():
        rec = student_info["info"].copy()
        total_present = 0
        total_absent = 0
        for date in sorted_dates:
            status = student_info["dates"].get(date, "-")
            rec[date] = status
            if status == "P":
                total_present += 1
            elif status == "A":
                total_absent += 1
        total_days = len(sorted_dates)
        rec["total_days"] = total_days
        rec["total_present"] = total_present
        rec["total_absent"] = total_absent
        rec["attendance_percentage"] = round((total_present / total_days) * 100, 2) if total_days > 0 else 0
        rec["below_75_percent"] = "Yes" if rec["attendance_percentage"] < 75 else "No"
        attendance_data.append(rec)
    attendance_data.sort(key=lambda x: x["roll_number"])
    return {"total_students": len(attendance_data), "date_range": {"start_date": start_date, "end_date": end_date, "total_days": len(sorted_dates)}, "dates": sorted_dates, "school_name": school_name, "data": attendance_data}


def database_change_log_controller(school_name: Optional[str], roll_no: Optional[str], session: Optional[str], class_name: Optional[str], section: Optional[str], subject: Optional[str], change_type: Optional[str], start_date: Optional[str], end_date: Optional[str], fmt: str):
    if not school_name and not roll_no and not session:
        return {"error": "At least one of school_name, roll_no, or session is required"}
    if fmt.lower() == "csv":
        csv_content = repo.get_change_log_as_csv(school_name=school_name, roll_no=roll_no, session=session, class_name=class_name, section=section, subject=subject, change_type=change_type, start_date=start_date, end_date=end_date)
        filename_parts = ["database_change_log"]
        if school_name:
            filename_parts.append(school_name)
        if session:
            filename_parts.append(session)
        filename = "_".join(filename_parts) + ".csv"
        return StreamingResponse(iter([csv_content]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})
    logs = repo.get_database_change_log(school_name=school_name, roll_no=roll_no, session=session, class_name=class_name, section=section, subject=subject, change_type=change_type, start_date=start_date, end_date=end_date)
    if not logs:
        return {"error": "No change log entries found matching the criteria", "total_records": 0}
    return {"total_records": len(logs), "filters": {"school_name": school_name, "roll_no": roll_no, "session": session, "class_name": class_name, "section": section, "subject": subject, "change_type": change_type, "start_date": start_date, "end_date": end_date}, "data": logs}
