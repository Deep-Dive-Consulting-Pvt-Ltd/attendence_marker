from services.attendance_service import convert_date_format, parse_student_folder_name, validate_date_format


def test_parse_student_folder_name_valid():
    roll_no, name = parse_student_folder_name("21045001_aman_meena")
    assert roll_no == "21045001"
    assert name == "aman_meena"


def test_parse_student_folder_name_invalid():
    roll_no, name = parse_student_folder_name("invalidfolder")
    assert roll_no is None
    assert name is None


def test_date_validation_and_conversion():
    assert validate_date_format("29-03-2026")
    assert convert_date_format("29-03-2026", "%d-%m-%Y", "%Y-%m-%d") == "2026-03-29"
