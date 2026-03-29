from typing import Optional

from fastapi import APIRouter, File, Form, Query, UploadFile

from controllers import attendance_controller as controller

router = APIRouter()


@router.post("/enroll/")
async def enroll_students(school_name: str = Form(...), session: str = Form(...), class_name: Optional[str] = Form(None), section: Optional[str] = Form(None), subject: Optional[str] = Form(None), faces_zip: UploadFile = File(...)):
    return await controller.enroll_students_controller(school_name, session, class_name, section, subject, faces_zip)


@router.post("/enroll-new-student/")
async def enroll_new_student(school_name: str = Form(...), session: str = Form(...), class_name: Optional[str] = Form(None), section: Optional[str] = Form(None), subject: Optional[str] = Form(None), faces_zip: UploadFile = File(...)):
    return await controller.enroll_new_student_controller(school_name, session, class_name, section, subject, faces_zip)


@router.post("/enroll-new-batch-with-replacement/")
async def enroll_new_batch_with_replacement(school_name: str = Form(...), session: str = Form(...), class_name: Optional[str] = Form(None), section: Optional[str] = Form(None), subject: Optional[str] = Form(None), faces_zip: UploadFile = File(...)):
    return await controller.enroll_new_batch_with_replacement_controller(school_name, session, class_name, section, subject, faces_zip)


@router.post("/update-embedding-via-period/")
async def update_embedding_via_period(school_name: str = Form(...), session: str = Form(...), alpha: float = Form(...), class_name: Optional[str] = Form(None), section: Optional[str] = Form(None), subject: Optional[str] = Form(None), faces_zip: UploadFile = File(...)):
    return await controller.update_embedding_controller(school_name, session, alpha, class_name, section, subject, faces_zip)


@router.post("/mark-attendance/")
async def mark_attendance(school_name: str = Form(...), class_name: str = Form(...), section: str = Form(...), subject: Optional[str] = Form(None), photos_zip: UploadFile = File(...), threshold: float = Form(0.3)):
    return await controller.mark_attendance_controller(school_name, class_name, section, subject, photos_zip, threshold)


@router.delete("/delete-student/")
async def delete_student(school_name: str = Query(...), roll_no: str = Query(...), session: str = Query(...)):
    return controller.delete_student_controller(school_name, roll_no, session)


@router.delete("/delete-class/")
async def delete_class(school_name: str = Query(...), class_name: str = Query(...), session: str = Query(...), section: Optional[str] = Query(None), subject: Optional[str] = Query(None)):
    return controller.delete_class_controller(school_name, class_name, session, section, subject)


@router.delete("/delete-student-from-database/")
async def delete_student_from_database(school_name: str = Query(...), roll_no: str = Query(...), session: str = Query(...)):
    return controller.delete_student_database_only_controller(school_name, roll_no, session)


@router.delete("/delete-student-from-attendance/")
async def delete_student_from_attendance(school_name: str = Query(...), roll_no: str = Query(...), session: str = Query(...)):
    return controller.delete_student_attendance_only_controller(school_name, roll_no, session)


@router.delete("/delete-student-from-both/")
async def delete_student_from_both(school_name: str = Query(...), roll_no: str = Query(...), session: str = Query(...)):
    return controller.delete_student_both_controller(school_name, roll_no, session)


@router.delete("/delete-bulk-from-database/")
async def delete_bulk_from_database(school_name: str = Query(...), class_name: str = Query(...), section: str = Query(...), session: str = Query(...), subject: Optional[str] = Query(None)):
    return controller.delete_bulk_database_controller(school_name, class_name, section, session, subject)


@router.delete("/delete-bulk-from-attendance/")
async def delete_bulk_from_attendance(school_name: str = Query(...), class_name: str = Query(...), section: str = Query(...), session: str = Query(...), subject: Optional[str] = Query(None)):
    return controller.delete_bulk_attendance_controller(school_name, class_name, section, session, subject)


@router.delete("/delete-bulk-from-both/")
async def delete_bulk_from_both(school_name: str = Query(...), class_name: str = Query(...), section: str = Query(...), session: str = Query(...), subject: Optional[str] = Query(None)):
    return controller.delete_bulk_both_controller(school_name, class_name, section, session, subject)


@router.get("/enrollment-stats/")
async def enrollment_stats():
    return controller.enrollment_stats_controller()


@router.get("/view-students/")
async def view_students(school_name: str = Query(...), class_name: Optional[str] = Query(None), section: Optional[str] = Query(None), subject: Optional[str] = Query(None)):
    return controller.view_students_controller(school_name, class_name, section, subject)


@router.get("/view-attendance-on-date/")
async def view_attendance_on_date(school_name: str = Query(...), date: str = Query(...), roll_no: Optional[str] = Query(None), class_name: Optional[str] = Query(None), section: Optional[str] = Query(None), subject: Optional[str] = Query(None)):
    return controller.view_attendance_on_date_controller(school_name, date, roll_no, class_name, section, subject)


@router.get("/view-attendance-range/")
async def view_attendance_range(school_name: str = Query(...), start_date: str = Query(...), end_date: str = Query(...), roll_no: Optional[str] = Query(None), class_name: Optional[str] = Query(None), section: Optional[str] = Query(None), subject: Optional[str] = Query(None)):
    return controller.view_attendance_range_controller(school_name, start_date, end_date, roll_no, class_name, section, subject)


@router.get("/database-change-log/")
async def database_change_log(school_name: Optional[str] = Query(None), roll_no: Optional[str] = Query(None), session: Optional[str] = Query(None), class_name: Optional[str] = Query(None), section: Optional[str] = Query(None), subject: Optional[str] = Query(None), change_type: Optional[str] = Query(None), start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), format: Optional[str] = Query("json")):
    return controller.database_change_log_controller(school_name, roll_no, session, class_name, section, subject, change_type, start_date, end_date, format)
