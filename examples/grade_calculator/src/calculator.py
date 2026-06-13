from typing import Dict, List

class GradeCalculationError(Exception):
    """Custom exception for errors during grade calculation."""
    pass

def calculate_average_grade(student_grades: Dict[str, List[float]]) -> Dict[str, float]:
    """
    Calculates the average grade for each student.

    Args:
        student_grades: A dictionary mapping student names to a list of numerical grades.

    Returns:
        A dictionary mapping student names to their average grades, 
        rounded to one decimal place.

    Raises:
        GradeCalculationError: If the input contains empty grade lists or invalid data types.
    """
    if not isinstance(student_grades, dict):
        raise GradeCalculationError("Input must be a dictionary.")

    averages: Dict[str, float] = {}

    for student, grades in student_grades.items():
        if not isinstance(grades, list):
            raise GradeCalculationError(f"Grades for {student} must be provided as a list.")
        
        if not grades:
            # We decide to treat empty lists as 0.0 average or raise error.
            # Here we raise error to ensure data integrity.
            raise GradeCalculationError(f"No grades found for student: {student}")

        try:
            average = sum(grades) / len(grades)
            averages[student] = round(float(average), 1)
        except TypeError as e:
            raise GradeCalculationError(f"Invalid grade value encountered for {student}: {e}")

    return averages