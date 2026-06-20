import pytest

from src.calculator import GradeCalculationError
from src.calculator import calculate_average_grade
from src.calculator import calculate_median_grade

def test_calculate_average_grade_success():
    """Tests standard functionality with valid input."""
    input_data = {
        "Alice": [85, 0, 78],
        "Bob": [100, 92],
        "Charlie": [60, 70, 65, 80]
    }
    expected_output = {
        "Alice": 54.3,
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
        
def test_calculate_median_grade_single_student():
    """Tests the median calculation for a single student."""
    input_data = {"Alice": [85]}
    # The median of a single element is the element itself.
    expected_output = {"Alice": 85.0}
    assert calculate_median_grade(input_data) == expected_output

def test_calculate_median_grade_success():
    """Tests median calculation with even and odd number of grades."""
    input_data = {
        "Alice": [80, 90, 100],  # Odd: 90
        "Bob": [70, 80, 90, 100] # Even: (80+90)/2 = 85
    }
    expected_output = {
        "Alice": 90.0,
        "Bob": 85.0
    }
    assert calculate_median_grade(input_data) == expected_output

def test_calculate_median_grade_empty_list_raises_error():
    """Tests that an empty list of grades raises a GradeCalculationError."""
    input_data = {"Alice": []}
    with pytest.raises(GradeCalculationError, match="No grades found for student"):
        calculate_median_grade(input_data)

def test_calculate_median_grade_invalid_type_raises_error():
    """Tests that non-list values raise a Grade_CalculationError."""
    input_data = {"Alice": "not a list"}
    with pytest.raises(GradeCalculationError, match="must be provided as a list"):
        calculate_median_grade(input_data)

def test_calculate_median_grade_non_numeric_values():
    """Tests that non-numeric grades within the list raise an error."""
    input_data = {"Alice": [90, "invalid", 80]}
    with pytest.raises(GradeCalculationError):
        calculate_median_grade(input_data)

