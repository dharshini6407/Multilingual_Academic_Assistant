import pytest
from services.attendance_service import calculate_attendance_metrics

def test_attendance_basic_calculation():
    # 36 attended out of 42 conducted = 85.71%
    metrics = calculate_attendance_metrics(conducted=42, attended=36, target_percentage=75.0)
    assert metrics['percentage'] == 85.71
    assert metrics['target_met'] is True
    assert metrics['classes_needed'] == 0
    assert metrics['classes_can_miss'] > 0
    assert metrics['status'] == 'SAFE'

def test_consecutive_classes_needed_formula():
    # Conducted = 40, Attended = 27 -> current = 67.5%, Target = 75%
    # Needed = ceil((0.75 * 40 - 27) / (1 - 0.75)) = ceil(3 / 0.25) = 12
    metrics = calculate_attendance_metrics(conducted=40, attended=27, target_percentage=75.0)
    assert metrics['percentage'] == 67.5
    assert metrics['target_met'] is False
    assert metrics['classes_needed'] == 12
    
    # Mathematical proof check:
    new_attended = 27 + metrics['classes_needed']
    new_conducted = 40 + metrics['classes_needed']
    assert (new_attended / new_conducted) * 100 >= 75.0

def test_attendance_zero_classes_edge_case():
    # Conducted = 0, Attended = 0
    metrics = calculate_attendance_metrics(conducted=0, attended=0, target_percentage=75.0)
    assert metrics['conducted'] == 0
    assert metrics['attended'] == 0
    assert metrics['percentage'] == 100.0
    assert metrics['classes_needed'] == 0
    assert metrics['status'] == 'NO_CLASSES_HELD'

def test_attendance_impossible_target_edge_case():
    # If 1 class is missed, achieving 100% is mathematically impossible
    metrics = calculate_attendance_metrics(conducted=10, attended=9, target_percentage=100.0)
    assert metrics['target_met'] is False
    assert metrics['classes_needed'] == -1

def test_invalid_target_percentage():
    # Target > 100 or <= 0
    metrics = calculate_attendance_metrics(conducted=20, attended=15, target_percentage=120.0)
    assert metrics['is_target_valid'] is False
    assert metrics['target_percentage'] == 75.0 # Graceful fallback to default

def test_attendance_api_endpoints(client, student_headers):
    # 1. Update target
    res_target = client.put('/api/attendance/target', json={
        'subject_id': 1,
        'target_percentage': 80.0
    }, headers=student_headers)
    assert res_target.status_code == 200
    assert res_target.get_json()['record']['target_percentage'] == 80.0

    # 2. Test Simulation
    res_sim = client.post('/api/attendance/simulate', json={
        'conducted': 30,
        'attended': 21,
        'target': 75.0,
        'future_classes_attend': 9,
        'future_classes_miss': 0
    }, headers=student_headers)
    assert res_sim.status_code == 200
    sim_data = res_sim.get_json()
    assert sim_data['current']['percentage'] == 70.0
    assert sim_data['simulated']['percentage'] == 76.92
    assert sim_data['simulated']['target_met'] is True
