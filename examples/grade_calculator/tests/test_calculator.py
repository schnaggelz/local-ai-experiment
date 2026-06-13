import pytest
from src.calculator import calculate_average_grade, GradeCalculationError

def test_calculate_average_grade_success():
    """Tests standard functionality with valid input."""
    input_data = {
        "Alice": [85, 90, 78],
        "Bob": [100, 92],
        "Charlie": [60, 70, 65, 80]
    }
    expected_output = {
        "Alice": 84.3,
        "Bob": 96.0,
        "Charlie": 68.8
    }
    assert calculate_average_grade(input_data) == expected_output

def test_calculate_average_grade_single_student():
    """Tests calculation for a single student."""
    input_data = {"Alice": [100]}
    expected_output = {"Alice": 100.0}
    assert calculate_average_grade(input_data) == expected_output

def test_calculate_average_grade_empty_list_raises_error():
    """Tests that an empty list of grades raises a GradeCalculationError."""
    input_data = {"Alice": []}
    with pytest.raises(GradeCalculationError, match="No grades found for student"):
        calculate_average_grade(input_data)

def test_calculate_average_grade_invalid_type_raises_error():
    """Tests that non-list values raise a GradeCalculationError."""
    input_data = {"Alice": "not a list"}
    with pytest.raises(GradeCalculationError, match="must be provided as a list"):
        calculate_average_grade(input_data)

def test_calculate_average_grade_non_numeric_values():
    """Tests that non-numeric grades within the list raise an error."""
    input_data = {"Alice": [90, "invalid", 80]}
    with pytest.raises(GradeCalculationError):
        calculate_average_grade(input_data)
        