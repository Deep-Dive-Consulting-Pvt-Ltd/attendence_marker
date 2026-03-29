"""
Compatibility database module.

This module preserves the historical function surface while delegating
storage to MongoDB repository implementations.
"""

from db.mongo import close_db as close_pool
from db.mongo import init_collections as init_db
from repositories.mongo_repository import (
    delete_bulk_from_attendance,
    delete_bulk_from_both_tables,
    delete_bulk_from_database,
    delete_class_data,
    delete_student_by_roll_no,
    delete_student_from_attendance_only,
    delete_student_from_both,
    delete_student_from_database_only,
    get_all_students_for_attendance,
    get_attendance_in_range,
    get_attendance_on_date,
    get_change_log_as_csv,
    get_database_change_log,
    get_enrollment_stats,
    get_student_embedding,
    get_students,
    get_students_by_filters,
    get_students_for_export,
    log_database_change,
    save_attendance,
    save_student,
    update_student_embedding,
)

