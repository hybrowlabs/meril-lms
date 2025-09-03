import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def update_video_progress(course_id, lesson_id, video_file, current_time, duration, progress_percentage, max_watched_time, timestamp):
    """
    API endpoint to update course lesson progress in LMS Course Progress doctype.
    Stores video progress in the current_videos_progress JSON field.
    """

    
    user = frappe.session.user

    # Resolve enrollment for this user and course
    enrollment_name = frappe.db.get_value(
        "LMS Enrollment",
        {"member": user, "course": course_id},
        "name",
    )

    # Find existing progress record using actual field names
    progress_doc = frappe.get_all(
        "LMS Course Progress",
        filters={
            "course": course_id,
            "lesson": lesson_id,
            "member": user,
        },
        fields=["name"],
        limit=1,
    )

    if progress_doc:
        doc = frappe.get_doc("LMS Course Progress", progress_doc[0].name)
    else:
        doc = frappe.new_doc("LMS Course Progress")
        doc.course = course_id
        doc.lesson = lesson_id
        doc.member = user
        if enrollment_name:
            doc.enrollment = enrollment_name
        doc.current_videos_progress = {}

    # Load or initialize current_videos_progress; handle cases where it's stored as a JSON string
    current_videos_progress = doc.current_videos_progress or {}
    if isinstance(current_videos_progress, str):
        try:
            current_videos_progress = frappe.parse_json(current_videos_progress) or {}
        except Exception:
            current_videos_progress = {}

    # Update progress for the specific video_file
    current_videos_progress[video_file] = {
        "current_time": current_time,
        "duration": duration,
        "progress_percentage": progress_percentage,
        "max_watched_time": max_watched_time,
        "timestamp": timestamp
    }

    doc.current_videos_progress = current_videos_progress

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success",
        "message": _("Course progress updated successfully."),
        "progress_name": doc.name
    }


@frappe.whitelist(allow_guest=False)
def get_video_progress(course_id, lesson_id, video_file):
    """
    API endpoint to fetch saved video progress for a user/course/lesson/video.
    Returns the JSON stored in current_videos_progress[video_file] if present.
    """

    user = frappe.session.user

    progress_doc = frappe.get_all(
        "LMS Course Progress",
        filters={
            "course": course_id,
            "lesson": lesson_id,
            "member": user,
        },
        fields=["name", "current_videos_progress"],
        limit=1,
    )

    if not progress_doc:
        return {
            "status": "success",
            "progress": None
        }

    # If we have a doc, fetch the JSON and return the entry for the video_file
    doc = frappe.get_doc("LMS Course Progress", progress_doc[0].name)
    current_videos_progress = doc.current_videos_progress or {}
    if isinstance(current_videos_progress, str):
        try:
            current_videos_progress = frappe.parse_json(current_videos_progress) or {}
        except Exception:
            current_videos_progress = {}
    progress = current_videos_progress.get(video_file)

    return {
        "status": "success",
        "progress": progress
    }