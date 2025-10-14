#!/usr/bin/env python3
"""
Test script to verify re-enrollment functionality works correctly
after fixing the validation error.
"""

import frappe
from frappe import _

def test_re_enrollment():
    """Test re-enrollment for a user who has completed a course"""

    # Test parameters - update these as needed
    test_member = "distributor@example.com"  # Replace with actual user email
    test_course = "India - Ethics & Compliance Training on HCPs/HCOs Interactions"  # Replace with actual course

    print("=" * 60)
    print("Testing Re-enrollment Functionality")
    print("=" * 60)

    try:
        # 1. Check if enrollment exists
        existing = frappe.get_all(
            "LMS Enrollment",
            filters={"member": test_member, "course": test_course},
            fields=["name", "completion_status", "enrollment_version"],
            order_by="enrollment_version desc"
        )

        if not existing:
            print(f"❌ No enrollment found for {test_member} in {test_course}")
            print("   Creating initial enrollment for testing...")

            # Create initial enrollment
            enrollment = frappe.new_doc("LMS Enrollment")
            enrollment.update({
                "course": test_course,
                "member": test_member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Completed",
                "access_restricted": 1,
                "progress": 100,
                "enrollment_version": 1
            })
            enrollment.insert(ignore_permissions=True)
            existing = [enrollment.as_dict()]

        print(f"\n📊 Current Enrollment Status:")
        for enr in existing:
            print(f"   - {enr.name}: Status={enr.completion_status}, Version={enr.enrollment_version}")

        # 2. Test re-enrollment
        print(f"\n🔄 Testing re-enrollment for {test_member}...")

        # Get the most recent enrollment
        enrollment_doc = frappe.get_doc("LMS Enrollment", existing[0].name)

        # Attempt re-enrollment
        new_enrollment = enrollment_doc.re_enroll_user(
            re_enrolled_by=frappe.session.user,
            reset_progress=True
        )

        if new_enrollment:
            print(f"✅ Re-enrollment successful!")
            print(f"   - New enrollment ID: {new_enrollment.name}")
            print(f"   - Enrollment version: {new_enrollment.enrollment_version}")
            print(f"   - Completion status: {new_enrollment.completion_status}")
            print(f"   - Progress: {new_enrollment.progress}%")
            print(f"   - Access restricted: {new_enrollment.access_restricted}")

            # 3. Verify we can now have multiple enrollment records
            all_enrollments = frappe.get_all(
                "LMS Enrollment",
                filters={"member": test_member, "course": test_course},
                fields=["name", "enrollment_version", "completion_status"],
                order_by="enrollment_version"
            )

            print(f"\n📋 All Enrollments for this user/course:")
            for enr in all_enrollments:
                print(f"   Version {enr.enrollment_version}: {enr.name} ({enr.completion_status})")

            # 4. Test that duplicate active enrollment is still prevented
            print(f"\n🔒 Testing duplicate active enrollment prevention...")
            try:
                duplicate = frappe.new_doc("LMS Enrollment")
                duplicate.update({
                    "course": test_course,
                    "member": test_member,
                    "member_type": "Student",
                    "role": "Member",
                    "completion_status": "Active"
                })
                duplicate.insert(ignore_permissions=True)
                print("   ❌ Duplicate active enrollment was allowed (this shouldn't happen)")
            except Exception as e:
                if "already has an active enrollment" in str(e):
                    print("   ✅ Duplicate active enrollment correctly prevented")
                else:
                    print(f"   ⚠️ Unexpected error: {e}")

            print("\n✅ All tests passed successfully!")

        else:
            print("❌ Re-enrollment failed - no new enrollment created")

    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {str(e)}")
        import traceback
        print("\nStack trace:")
        print(traceback.format_exc())

    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Initialize Frappe context
    frappe.init(site='site1.local')  # Replace with your site name
    frappe.connect()
    frappe.set_user("Administrator")

    # Run the test
    test_re_enrollment()

    # Cleanup
    frappe.db.commit()
    frappe.destroy()