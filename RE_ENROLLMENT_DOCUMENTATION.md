# Enhanced Re-enrollment Backend Documentation

## Overview
The enhanced re-enrollment system for the LMS creates new enrollment records instead of modifying existing ones, preserving complete historical data and enabling proper tracking of multiple enrollment attempts.

## Key Features

### 1. New Enrollment Record Creation
- Each re-enrollment creates a brand new `LMS Enrollment` record
- Previous enrollment is marked as "Completed" with `access_restricted = 1`
- New enrollment starts with fresh progress (0%) and status "Re-enrolled"

### 2. Version Tracking
- `enrollment_version`: Incremental version number for each enrollment attempt
- `re_enrollment_count`: Total number of re-enrollments (version - 1)
- `original_enrollment_date`: Preserved from the first enrollment

### 3. Historical Data Preservation
- All previous enrollments remain in the database
- Complete audit trail of all enrollment attempts
- Progress, completion dates, and timer data preserved for each version

### 4. Fresh Course Documents
- New `Distributor/Employee Course Documents` created for each re-enrollment
- Previous documents marked with `is_current_enrollment = 0`
- Document submission flags reset for new attempt

### 5. Timer Management
- Lesson timer data stored in JSON field `lesson_timer_data`
- Timer progress tracked per lesson with duration and completion status
- Timer data reset on re-enrollment for fresh tracking

## Implementation Details

### Core Methods

#### `create_re_enrollment_record(self, re_enrolled_by)`
Creates a new enrollment record with:
- Incremented `enrollment_version`
- Reset progress and lesson data
- Link to original enrollment date
- Proper status and access settings

#### `create_fresh_course_documents(self)`
- Marks previous course documents as not current
- Creates new document records linked to new enrollment
- Resets all submission and certification flags

#### `get_enrollment_history(self)`
Returns complete enrollment history including:
- All versions for a member/course combination
- Enrollment dates and completion status
- Progress for each attempt

#### Timer Management Methods
- `save_timer_progress()`: Save lesson timing data
- `get_timer_progress()`: Retrieve timer data for lessons
- `reset_all_timers()`: Clear all timer data

### API Endpoints

#### Re-enrollment
```python
POST /api/method/lms.lms.doctype.lms_enrollment.lms_enrollment.re_enroll_user_in_course
{
    "course": "course-name",
    "member": "user@example.com",
    "reset_progress": true
}

Response:
{
    "success": true,
    "enrollment_id": "new-enrollment-id",
    "enrollment_version": 2,
    "message": "User successfully re-enrolled"
}
```

#### Get Current Enrollment
```python
GET /api/method/lms.lms.doctype.lms_enrollment.lms_enrollment.get_current_enrollment
{
    "course": "course-name",
    "member": "user@example.com"  // optional, defaults to current user
}

Response:
{
    "success": true,
    "enrollment": {
        "name": "enrollment-id",
        "enrollment_version": 2,
        "completion_status": "Re-enrolled",
        "progress": 0
    }
}
```

#### Get Enrollment History
```python
GET /api/method/lms.lms.doctype.lms_enrollment.lms_enrollment.get_enrollment_history
{
    "course": "course-name",
    "member": "user@example.com"  // optional
}

Response:
{
    "success": true,
    "history": [
        {
            "name": "enrollment-1",
            "enrollment_version": 1,
            "completion_status": "Completed",
            "progress": 100,
            "completed_on": "2024-01-15"
        },
        {
            "name": "enrollment-2",
            "enrollment_version": 2,
            "completion_status": "Re-enrolled",
            "progress": 0,
            "re_enrolled_on": "2024-02-01"
        }
    ]
}
```

#### Timer Management
```python
POST /api/method/lms.lms.doctype.lms_enrollment.lms_enrollment.save_lesson_timer_progress
{
    "enrollment_id": "enrollment-id",
    "lesson_id": "lesson-001",
    "current_time": 120,
    "duration": 300,
    "completed": false
}

GET /api/method/lms.lms.doctype.lms_enrollment.lms_enrollment.get_lesson_timer_progress
{
    "enrollment_id": "enrollment-id",
    "lesson_id": "lesson-001"  // optional, returns all if not specified
}
```

### Database Schema Updates

#### LMS Enrollment Fields
- `enrollment_version` (Int): Version number of this enrollment
- `re_enrollment_count` (Int): Number of times re-enrolled
- `original_enrollment_date` (Datetime): Date of first enrollment
- `lesson_timer_data` (JSON): Timer progress for lessons

#### Distributor/Employee Course Documents Fields
- `enrollment` (Link to LMS Enrollment): Associated enrollment record
- `enrollment_version` (Int): Enrollment version number
- `is_current_enrollment` (Check): Flag for current enrollment

## Migration Strategy

### For Existing Enrollments
1. Set `enrollment_version = 1` for all existing records
2. Set `original_enrollment_date = creation` if not already set
3. Set `re_enrollment_count = 0` for first enrollments

### For Existing Course Documents
1. Link to most recent enrollment for the user/course
2. Set `enrollment_version` based on linked enrollment
3. Mark as `is_current_enrollment = 1`

### Migration Script
Run the migration with:
```bash
bench execute lms.lms.doctype.lms_enrollment.lms_enrollment.migrate_existing_enrollments
```

Or apply the patch:
```bash
bench execute lms.patches.v15_0.add_re_enrollment_fields.execute
```

## Testing

### Test Script
A comprehensive test script is available at `test_re_enrollment.py`:
```bash
bench execute lms.test_re_enrollment.test_re_enrollment
```

This tests:
- New enrollment creation
- Re-enrollment process
- Timer management
- Enrollment history
- API endpoints

## Best Practices

### Frontend Integration
1. Always use `get_current_enrollment` to get the active enrollment
2. Check `enrollment_version` to display attempt number
3. Use `get_enrollment_history` for showing previous attempts
4. Save timer progress periodically to prevent data loss

### Permission Handling
- System Manager and Administrator can re-enroll anyone
- Moderators can re-enroll distributors and employees
- Implement custom hierarchy logic in `is_senior_of_member()`

### Data Integrity
- Never modify historical enrollment records
- Always create new records for re-enrollment
- Preserve all progress and completion data
- Maintain referential integrity with course documents

## Troubleshooting

### Common Issues

1. **Re-enrollment not creating new record**
   - Check if user has proper permissions
   - Verify current enrollment status is "Completed"
   - Ensure `can_re_enroll()` returns True

2. **Course documents not linking**
   - Run migration script to update existing documents
   - Check if enrollment field exists in DocType
   - Verify user role (Distributor/Employee)

3. **Timer data not persisting**
   - Ensure `lesson_timer_data` field exists
   - Check JSON formatting in timer data
   - Verify enrollment has save permissions

## API Compatibility

The enhanced system maintains backward compatibility:
- Existing API endpoints continue to work
- New version-aware endpoints added alongside
- Frontend can gradually migrate to new endpoints
- No breaking changes to existing interfaces