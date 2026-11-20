import math
from typing import Dict, Any

def calculate_attendance_metrics(conducted: int, attended: int, target_percentage: float = 75.0) -> Dict[str, Any]:
    """
    Calculate comprehensive attendance metrics including:
    - Current percentage: (attended / conducted) * 100
    - Consecutive classes required to reach target
    - Classes that can safely be missed
    - Warning status and actionable advice
    - Robust edge case handling (0 classes, attended > conducted, invalid target)
    """
    # Defensive normalization
    conducted = max(0, int(conducted))
    attended = max(0, int(attended))
    
    if attended > conducted:
        conducted = attended # Sanitize impossible state
    
    # Target validation
    is_target_valid = True
    target_error = None
    if target_percentage <= 0 or target_percentage > 100:
        is_target_valid = False
        target_error = f"Target percentage must be between 1 and 100. Provided: {target_percentage}"
        target_percentage = 75.0 # Fallback to standard 75%
        
    target_ratio = target_percentage / 100.0

    # Case 1: No classes conducted yet
    if conducted == 0:
        return {
            'conducted': 0,
            'attended': 0,
            'percentage': 100.0,
            'target_percentage': target_percentage,
            'classes_needed': 0,
            'classes_can_miss': 0,
            'status': 'NO_CLASSES_HELD',
            'status_level': 'neutral',
            'warning_message': 'No classes have been conducted yet for this subject.',
            'target_met': True,
            'is_target_valid': is_target_valid,
            'target_error': target_error
        }

    # Current percentage
    current_pct = (attended / conducted) * 100.0
    rounded_pct = round(current_pct, 2)
    target_met = rounded_pct >= target_percentage

    classes_needed = 0
    classes_can_miss = 0

    if target_met:
        classes_needed = 0
        if target_ratio > 0:
            margin = attended - (target_ratio * conducted)
            classes_can_miss = max(0, math.floor(margin / target_ratio))
    else:
        classes_can_miss = 0
        if target_percentage >= 100.0:
            # If target is 100% and a class has been missed, 100% is mathematically unattainable
            classes_needed = -1 # Special code for mathematically impossible
        else:
            numerator = (target_ratio * conducted) - attended
            denominator = 1.0 - target_ratio
            if denominator > 0:
                classes_needed = max(0, math.ceil(numerator / denominator))
            else:
                classes_needed = -1

    # Warning status and messages
    if rounded_pct < 65.0:
        status = 'DEBARRED_WARNING'
        status_level = 'danger'
        if classes_needed == -1:
            msg = f"Critical shortage ({rounded_pct}%). Target of {target_percentage}% cannot be mathematically achieved."
        else:
            msg = f"Severe attendance shortage ({rounded_pct}%). You must attend the next {classes_needed} consecutive classes to reach {target_percentage}%!"
    elif rounded_pct < target_percentage:
        status = 'BELOW_TARGET'
        status_level = 'warning'
        if classes_needed == -1:
            msg = f"Attendance is {rounded_pct}%, below target {target_percentage}%."
        else:
            msg = f"Attendance is {rounded_pct}%. Attend {classes_needed} more consecutive class{'es' if classes_needed > 1 else ''} to reach {target_percentage}%."
    elif rounded_pct < 80.0:
        status = 'ON_BORDER'
        status_level = 'info'
        msg = f"Attendance is {rounded_pct}%. Target met! You can miss at most {classes_can_miss} class{'es' if classes_can_miss != 1 else ''} without falling below {target_percentage}%."
    else:
        status = 'SAFE'
        status_level = 'success'
        msg = f"Excellent attendance ({rounded_pct}%). You have a safety cushion of {classes_can_miss} class{'es' if classes_can_miss != 1 else ''}."

    return {
        'conducted': conducted,
        'attended': attended,
        'percentage': rounded_pct,
        'target_percentage': target_percentage,
        'classes_needed': classes_needed,
        'classes_can_miss': classes_can_miss,
        'status': status,
        'status_level': status_level,
        'warning_message': msg,
        'target_met': target_met,
        'is_target_valid': is_target_valid,
        'target_error': target_error
    }
