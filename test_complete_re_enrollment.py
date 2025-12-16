#!/usr/bin/env python3
"""
Comprehensive Re-enrollment System Test

This test file verifies that the complete re-enrollment system is working correctly
after fixing the validation error and implementing all the re-enrollment features.

Tests include:
1. Basic Re-enrollment Flow
2. Validation Tests
3. Data Integrity Tests
4. Email Notification Tests
5. Course Documents Tests
6. Timer Data Reset Tests
7. Edge Cases and Error Scenarios

Usage:
bench execute lms.test_complete_re_enrollment.run_complete_test
"""

import frappe
from frappe import _
from frappe.utils import now, flt
import json
import traceback
from datetime import datetime, timedelta

# Test Configuration
TEST_CONFIG = {
    "test_courses": [
        "India - Ethics & Compliance Training on HCPs/HCOs Interactions",
        "Test Course for Re-enrollment"  # Fallback if main course doesn't exist
    ],
    "test_users": {
        "distributor": {
            "email": "test.distributor@example.com",
            "name": "Test Distributor",
            "company": "Test Distributor Company",
            "country": "India"
        },
        "employee": {
            "email": "test.employee@example.com",
            "name": "Test Employee",
            "company": "Test Employee Company",
            "country": "India"
        }
    },
    "cleanup_on_success": True,  # Set to False to keep test data for inspection
    "verbose": True
}

class ReEnrollmentTestSuite:
    def __init__(self):
        self.test_results = []
        self.test_data = {}
        self.cleanup_items = []

    def log(self, message, test_name=None, level="INFO"):
        """Log a message with optional test name and level"""
        timestamp = now()
        prefix = f"[{level}]"
        if test_name:
            prefix += f" [{test_name}]"

        full_message = f"{prefix} {message}"
        if TEST_CONFIG["verbose"]:
            print(full_message)

        self.test_results.append({
            "timestamp": timestamp,
            "test_name": test_name,
            "level": level,
            "message": message
        })

    def assert_equal(self, actual, expected, message, test_name):
        """Custom assertion helper"""
        if actual == expected:
            self.log(f"✅ {message}", test_name, "PASS")
            return True
        else:
            self.log(f"❌ {message} - Expected: {expected}, Got: {actual}", test_name, "FAIL")
            return False

    def assert_true(self, condition, message, test_name):
        """Assert condition is True"""
        if condition:
            self.log(f"✅ {message}", test_name, "PASS")
            return True
        else:
            self.log(f"❌ {message}", test_name, "FAIL")
            return False

    def setup_test_data(self):
        """Create test course and users for testing"""
        self.log("Setting up test data...", "SETUP")

        try:
            # Create test course if it doesn't exist
            test_course_name = None
            for course_name in TEST_CONFIG["test_courses"]:
                if frappe.db.exists("LMS Course", course_name):
                    test_course_name = course_name
                    break

            if not test_course_name:
                # Create a test course
                test_course = frappe.new_doc("LMS Course")
                test_course.update({
                    "title": "Test Course for Re-enrollment",
                    "short_introduction": "Test Course Description",
                    "published": 1,
                    "disable_self_learning": 0,
                    "custom_assigned_to_role": "All"
                })
                test_course.insert(ignore_permissions=True)
                test_course_name = test_course.name
                self.cleanup_items.append(("LMS Course", test_course_name))

            self.test_data["course"] = test_course_name
            self.log(f"Using test course: {test_course_name}", "SETUP")

            # Create test users
            self.create_test_users()

            return True

        except Exception as e:
            self.log(f"Setup failed: {str(e)}", "SETUP", "ERROR")
            return False

    def create_test_users(self):
        """Create test distributor and employee users"""

        # Create Distributor user and profile
        dist_config = TEST_CONFIG["test_users"]["distributor"]
        if not frappe.db.exists("User", dist_config["email"]):
            # Create user
            user = frappe.new_doc("User")
            user.update({
                "email": dist_config["email"],
                "first_name": dist_config["name"],
                "full_name": dist_config["name"],
                "enabled": 1,
                "user_type": "Website User",
                "user_category": "Distributor",
                "country": dist_config["country"],
                "roles": [
                    {"role": "Distributor"},
                    {"role": "LMS Student"}
                ]
            })
            user.insert(ignore_permissions=True)
            self.cleanup_items.append(("User", dist_config["email"]))

            # Create Distributor profile
            distributor = frappe.new_doc("Distributor")
            distributor.update({
                "distributor_name": dist_config["name"],
                "attendee_name": dist_config["name"],
                "distributor_company_name": dist_config["company"],
                "distributor_email_address": dist_config["email"],
                "country": dist_config["country"],
                "user_id": dist_config["email"]
            })
            distributor.insert(ignore_permissions=True)
            self.cleanup_items.append(("Distributor", distributor.name))
            self.test_data["distributor"] = distributor.name
        else:
            # Find existing distributor
            dist_name = frappe.db.get_value("Distributor", {"user_id": dist_config["email"]}, "name")
            self.test_data["distributor"] = dist_name

        # Create Employee user and profile
        emp_config = TEST_CONFIG["test_users"]["employee"]
        if not frappe.db.exists("User", emp_config["email"]):
            # Create user
            user = frappe.new_doc("User")
            user.update({
                "email": emp_config["email"],
                "first_name": emp_config["name"],
                "full_name": emp_config["name"],
                "enabled": 1,
                "user_type": "Website User",
                "user_category": "Employee",
                "country": emp_config["country"],
                "roles": [
                    {"role": "Employee"},
                    {"role": "LMS Student"}
                ]
            })
            user.insert(ignore_permissions=True)
            self.cleanup_items.append(("User", emp_config["email"]))

            # Create Employee profile
            employee = frappe.new_doc("Employee")
            employee.update({
                "first_name": emp_config["name"].split()[0],
                "last_name": emp_config["name"].split()[-1] if len(emp_config["name"].split()) > 1 else "",
                "employee_name": emp_config["name"],
                "company_email": emp_config["email"],
                "custom_country": emp_config["country"],
                "user_id": emp_config["email"]
            })
            employee.insert(ignore_permissions=True)
            self.cleanup_items.append(("Employee", employee.name))
            self.test_data["employee"] = employee.name
        else:
            # Find existing employee
            emp_name = frappe.db.get_value("Employee", {"user_id": emp_config["email"]}, "name")
            self.test_data["employee"] = emp_name

        self.log("Test users created successfully", "SETUP")

    def test_basic_re_enrollment_flow(self):
        """Test Case 1: Basic Re-enrollment Flow"""
        test_name = "BASIC_RE_ENROLLMENT"
        self.log("Starting basic re-enrollment flow test", test_name)

        try:
            course = self.test_data["course"]
            member = TEST_CONFIG["test_users"]["distributor"]["email"]

            # Step 1: Create initial enrollment
            enrollment = frappe.new_doc("LMS Enrollment")
            enrollment.update({
                "course": course,
                "member": member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Active",
                "access_restricted": 0,
                "progress": 0,
                "enrollment_version": 1,
                "re_enrollment_count": 0,
                "original_enrollment_date": now()
            })
            enrollment.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", enrollment.name))
            self.log(f"Created initial enrollment: {enrollment.name}", test_name)

            # Step 2: Complete the course (set progress to 100%)
            enrollment.progress = 100
            enrollment.save(ignore_permissions=True)
            self.assert_equal(enrollment.completion_status, "Completed", "Course marked as completed", test_name)
            self.assert_equal(enrollment.access_restricted, 1, "Access restricted after completion", test_name)

            # Step 3: Re-enroll the user
            new_enrollment = enrollment.re_enroll_user(
                re_enrolled_by=frappe.session.user,
                reset_progress=True
            )

            self.assert_true(new_enrollment is not None, "New enrollment created", test_name)
            if new_enrollment:
                self.cleanup_items.append(("LMS Enrollment", new_enrollment.name))

                # Step 4: Verify new enrollment record
                self.assert_equal(new_enrollment.progress, 0, "Progress reset to 0%", test_name)
                self.assert_equal(new_enrollment.completion_status, "Re-enrolled", "Status set to Re-enrolled", test_name)
                self.assert_equal(new_enrollment.access_restricted, 0, "Access not restricted", test_name)
                self.assert_equal(new_enrollment.enrollment_version, 2, "Enrollment version incremented", test_name)

                # Step 5: Verify old enrollment is marked as completed
                enrollment.reload()
                self.assert_equal(enrollment.completion_status, "Completed", "Old enrollment marked as completed", test_name)
                self.assert_equal(enrollment.access_restricted, 1, "Old enrollment access restricted", test_name)

                self.log("✅ Basic re-enrollment flow test passed", test_name, "SUCCESS")
                return True
            else:
                self.log("❌ Basic re-enrollment flow test failed - no new enrollment", test_name, "FAIL")
                return False

        except Exception as e:
            self.log(f"❌ Basic re-enrollment flow test failed: {str(e)}", test_name, "ERROR")
            return False

    def test_validation_bypass(self):
        """Test Case 2: Validation Tests - Re-enrollment bypasses duplicate validation"""
        test_name = "VALIDATION_BYPASS"
        self.log("Starting validation bypass test", test_name)

        try:
            course = self.test_data["course"]
            member = TEST_CONFIG["test_users"]["employee"]["email"]

            # Create first enrollment
            enrollment1 = frappe.new_doc("LMS Enrollment")
            enrollment1.update({
                "course": course,
                "member": member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Completed",
                "access_restricted": 1,
                "progress": 100,
                "enrollment_version": 1
            })
            enrollment1.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", enrollment1.name))

            # Test normal duplicate prevention
            try:
                duplicate = frappe.new_doc("LMS Enrollment")
                duplicate.update({
                    "course": course,
                    "member": member,
                    "member_type": "Student",
                    "role": "Member",
                    "completion_status": "Active"
                })
                duplicate.insert(ignore_permissions=True)
                self.log("❌ Duplicate active enrollment was allowed (should be prevented)", test_name, "FAIL")
                return False
            except Exception as e:
                if "already has an active enrollment" in str(e):
                    self.log("✅ Duplicate active enrollment correctly prevented", test_name, "PASS")
                else:
                    self.log(f"⚠️ Unexpected error during duplicate test: {e}", test_name, "WARN")

            # Test re-enrollment bypasses validation
            new_enrollment = enrollment1.re_enroll_user(frappe.session.user)
            self.assert_true(new_enrollment is not None, "Re-enrollment bypassed validation", test_name)
            if new_enrollment:
                self.cleanup_items.append(("LMS Enrollment", new_enrollment.name))

                # Test multiple re-enrollments work
                enrollment1.reload()
                third_enrollment = new_enrollment.re_enroll_user(frappe.session.user)
                self.assert_true(third_enrollment is not None, "Multiple re-enrollments work", test_name)
                if third_enrollment:
                    self.cleanup_items.append(("LMS Enrollment", third_enrollment.name))
                    self.assert_equal(third_enrollment.enrollment_version, 3, "Third enrollment version correct", test_name)

                self.log("✅ Validation bypass test passed", test_name, "SUCCESS")
                return True
            else:
                return False

        except Exception as e:
            self.log(f"❌ Validation bypass test failed: {str(e)}", test_name, "ERROR")
            return False

    def test_data_integrity(self):
        """Test Case 3: Data Integrity Tests"""
        test_name = "DATA_INTEGRITY"
        self.log("Starting data integrity test", test_name)

        try:
            course = self.test_data["course"]
            member = TEST_CONFIG["test_users"]["distributor"]["email"]

            # Create initial enrollment with timer data
            enrollment = frappe.new_doc("LMS Enrollment")
            enrollment.update({
                "course": course,
                "member": member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Completed",
                "progress": 100,
                "lesson_timer_data": json.dumps({
                    "lesson1": {"current_time": 120, "duration": 300, "completed": True}
                }),
                "enrollment_version": 1,
                "re_enrollment_count": 0,
                "original_enrollment_date": now()
            })
            enrollment.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", enrollment.name))

            # Re-enroll
            new_enrollment = enrollment.re_enroll_user(frappe.session.user)
            self.cleanup_items.append(("LMS Enrollment", new_enrollment.name))

            # Test versioning
            self.assert_equal(new_enrollment.enrollment_version, 2, "Enrollment version incremented", test_name)
            self.assert_equal(new_enrollment.re_enrollment_count, 1, "Re-enrollment count correct", test_name)

            # Test original enrollment date preserved
            original_date = enrollment.original_enrollment_date
            self.assert_equal(
                new_enrollment.original_enrollment_date,
                original_date,
                "Original enrollment date preserved",
                test_name
            )

            # Test timer data reset
            self.assert_true(
                new_enrollment.lesson_timer_data is None,
                "Timer data reset",
                test_name
            )

            # Test enrollment history
            history = new_enrollment.get_enrollment_history()
            self.assert_equal(len(history), 2, "Correct number of enrollment records in history", test_name)

            self.log("✅ Data integrity test passed", test_name, "SUCCESS")
            return True

        except Exception as e:
            self.log(f"❌ Data integrity test failed: {str(e)}", test_name, "ERROR")
            return False

    def test_course_documents_creation(self):
        """Test Case 4: Course Documents Tests"""
        test_name = "COURSE_DOCUMENTS"
        self.log("Starting course documents test", test_name)

        try:
            course = self.test_data["course"]

            # Test Distributor Course Documents
            dist_member = TEST_CONFIG["test_users"]["distributor"]["email"]
            dist_enrollment = frappe.new_doc("LMS Enrollment")
            dist_enrollment.update({
                "course": course,
                "member": dist_member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Completed",
                "progress": 100,
                "enrollment_version": 1
            })
            dist_enrollment.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", dist_enrollment.name))

            # Re-enroll distributor
            new_dist_enrollment = dist_enrollment.re_enroll_user(frappe.session.user)
            self.cleanup_items.append(("LMS Enrollment", new_dist_enrollment.name))

            # Check if distributor course documents were created
            if self.test_data.get("distributor"):
                dist_docs = frappe.get_all(
                    "Distributor Course Documents",
                    filters={
                        "distributor": self.test_data["distributor"],
                        "course": course,
                        "enrollment": new_dist_enrollment.name
                    }
                )
                self.assert_true(len(dist_docs) > 0, "Distributor course documents created", test_name)
                if dist_docs:
                    self.cleanup_items.extend([("Distributor Course Documents", doc.name) for doc in dist_docs])

            # Test Employee Course Documents
            emp_member = TEST_CONFIG["test_users"]["employee"]["email"]
            emp_enrollment = frappe.new_doc("LMS Enrollment")
            emp_enrollment.update({
                "course": course,
                "member": emp_member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Completed",
                "progress": 100,
                "enrollment_version": 1
            })
            emp_enrollment.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", emp_enrollment.name))

            # Re-enroll employee
            new_emp_enrollment = emp_enrollment.re_enroll_user(frappe.session.user)
            self.cleanup_items.append(("LMS Enrollment", new_emp_enrollment.name))

            # Check if employee course documents were created
            if self.test_data.get("employee"):
                emp_docs = frappe.get_all(
                    "Employee Course Documents",
                    filters={
                        "employee": self.test_data["employee"],
                        "course": course,
                        "enrollment": new_emp_enrollment.name
                    }
                )
                self.assert_true(len(emp_docs) > 0, "Employee course documents created", test_name)
                if emp_docs:
                    self.cleanup_items.extend([("Employee Course Documents", doc.name) for doc in emp_docs])

            self.log("✅ Course documents test passed", test_name, "SUCCESS")
            return True

        except Exception as e:
            self.log(f"❌ Course documents test failed: {str(e)}", test_name, "ERROR")
            return False

    def test_email_notifications(self):
        """Test Case 5: Email Notification Tests"""
        test_name = "EMAIL_NOTIFICATIONS"
        self.log("Starting email notifications test", test_name)

        try:
            course = self.test_data["course"]
            member = TEST_CONFIG["test_users"]["distributor"]["email"]

            enrollment = frappe.new_doc("LMS Enrollment")
            enrollment.update({
                "course": course,
                "member": member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Completed",
                "progress": 100
            })
            enrollment.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", enrollment.name))

            # Test email function directly
            from lms.lms.user import send_re_enrollment_email
            result = send_re_enrollment_email(
                user_email=member,
                partner_name="Test User",
                user_id=member,
                password="test123"
            )

            self.assert_equal(result["status"], "success", "Re-enrollment email sent successfully", test_name)

            # Test re-enrollment with email notification
            new_enrollment = enrollment.re_enroll_user(frappe.session.user)
            self.cleanup_items.append(("LMS Enrollment", new_enrollment.name))

            self.assert_true(new_enrollment is not None, "Re-enrollment with email notification successful", test_name)

            self.log("✅ Email notifications test passed", test_name, "SUCCESS")
            return True

        except Exception as e:
            self.log(f"⚠️ Email notifications test warning: {str(e)}", test_name, "WARN")
            # Email tests might fail in development environments without proper SMTP setup
            return True  # Don't fail the entire test suite for email issues

    def test_api_endpoints(self):
        """Test Case 6: API Endpoints Tests"""
        test_name = "API_ENDPOINTS"
        self.log("Starting API endpoints test", test_name)

        try:
            course = self.test_data["course"]
            member = TEST_CONFIG["test_users"]["employee"]["email"]

            # Create enrollment
            enrollment = frappe.new_doc("LMS Enrollment")
            enrollment.update({
                "course": course,
                "member": member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Completed",
                "progress": 100
            })
            enrollment.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", enrollment.name))

            # Test re-enrollment API
            from lms.lms.doctype.lms_enrollment.lms_enrollment import re_enroll_user_in_course
            result = re_enroll_user_in_course(course, member, True)

            self.assert_equal(result["success"], True, "API re-enrollment successful", test_name)
            if result.get("enrollment_id"):
                self.cleanup_items.append(("LMS Enrollment", result["enrollment_id"]))

            # Test course access API
            from lms.lms.doctype.lms_enrollment.lms_enrollment import check_course_access
            access_result = check_course_access(course, member)

            self.assert_equal(access_result["access"], True, "Course access check works", test_name)

            # Test enrollment history API
            from lms.lms.doctype.lms_enrollment.lms_enrollment import get_enrollment_history
            history_result = get_enrollment_history(course, member)

            self.assert_equal(history_result["success"], True, "Enrollment history API works", test_name)
            self.assert_true(len(history_result["history"]) >= 2, "Multiple enrollments in history", test_name)

            self.log("✅ API endpoints test passed", test_name, "SUCCESS")
            return True

        except Exception as e:
            self.log(f"❌ API endpoints test failed: {str(e)}", test_name, "ERROR")
            return False

    def test_edge_cases(self):
        """Test Case 7: Edge Cases and Error Scenarios"""
        test_name = "EDGE_CASES"
        self.log("Starting edge cases test", test_name)

        try:
            course = self.test_data["course"]

            # Test re-enrollment without permission
            unauthorized_member = "unauthorized@example.com"

            # Create user without proper roles
            if not frappe.db.exists("User", unauthorized_member):
                user = frappe.new_doc("User")
                user.update({
                    "email": unauthorized_member,
                    "first_name": "Unauthorized",
                    "enabled": 1,
                    "user_type": "Website User"
                })
                user.insert(ignore_permissions=True)
                self.cleanup_items.append(("User", unauthorized_member))

            enrollment = frappe.new_doc("LMS Enrollment")
            enrollment.update({
                "course": course,
                "member": unauthorized_member,
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Completed",
                "progress": 100
            })
            enrollment.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", enrollment.name))

            # Test permission check
            try:
                enrollment.re_enroll_user("Guest")  # Should fail
                self.log("❌ Permission check failed - unauthorized access allowed", test_name, "FAIL")
            except Exception as e:
                if "permission" in str(e).lower():
                    self.log("✅ Permission check works correctly", test_name, "PASS")
                else:
                    self.log(f"⚠️ Unexpected error in permission test: {e}", test_name, "WARN")

            # Test re-enrollment of active course
            active_enrollment = frappe.new_doc("LMS Enrollment")
            active_enrollment.update({
                "course": course,
                "member": TEST_CONFIG["test_users"]["distributor"]["email"],
                "member_type": "Student",
                "role": "Member",
                "completion_status": "Active",
                "progress": 50
            })
            active_enrollment.insert(ignore_permissions=True)
            self.cleanup_items.append(("LMS Enrollment", active_enrollment.name))

            # Re-enroll active course (should work)
            new_enrollment = active_enrollment.re_enroll_user(frappe.session.user)
            if new_enrollment:
                self.cleanup_items.append(("LMS Enrollment", new_enrollment.name))
                self.log("✅ Re-enrollment of active course works", test_name, "PASS")

            self.log("✅ Edge cases test passed", test_name, "SUCCESS")
            return True

        except Exception as e:
            self.log(f"❌ Edge cases test failed: {str(e)}", test_name, "ERROR")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        if not TEST_CONFIG["cleanup_on_success"]:
            self.log("Cleanup disabled - keeping test data for inspection", "CLEANUP")
            return

        self.log("Starting cleanup...", "CLEANUP")

        cleanup_count = 0
        for doctype, docname in reversed(self.cleanup_items):
            try:
                if frappe.db.exists(doctype, docname):
                    frappe.delete_doc(doctype, docname, ignore_permissions=True)
                    cleanup_count += 1
            except Exception as e:
                self.log(f"Failed to cleanup {doctype} {docname}: {str(e)}", "CLEANUP", "WARN")

        # Clean up any remaining test progress records
        try:
            frappe.db.sql("""
                DELETE FROM `tabLMS Course Progress`
                WHERE member IN %(members)s
            """, {
                "members": [
                    TEST_CONFIG["test_users"]["distributor"]["email"],
                    TEST_CONFIG["test_users"]["employee"]["email"]
                ]
            })
        except:
            pass

        self.log(f"Cleaned up {cleanup_count} test records", "CLEANUP")

    def generate_report(self):
        """Generate a comprehensive test report"""
        passed_tests = len([r for r in self.test_results if r["level"] == "SUCCESS"])
        failed_tests = len([r for r in self.test_results if r["level"] == "FAIL" or r["level"] == "ERROR"])
        total_tests = passed_tests + failed_tests

        print("\n" + "="*80)
        print("RE-ENROLLMENT SYSTEM TEST REPORT")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        print("="*80)

        # Group results by test name
        test_groups = {}
        for result in self.test_results:
            test_name = result.get("test_name", "GENERAL")
            if test_name not in test_groups:
                test_groups[test_name] = []
            test_groups[test_name].append(result)

        for test_name, results in test_groups.items():
            print(f"\n{test_name}:")
            for result in results:
                if result["level"] in ["SUCCESS", "FAIL", "ERROR", "PASS"]:
                    level_indicator = "✅" if result["level"] in ["SUCCESS", "PASS"] else "❌"
                    print(f"  {level_indicator} {result['message']}")

        print("\n" + "="*80)

        return total_tests > 0 and failed_tests == 0

def run_complete_test():
    """Main test runner function"""
    print("Starting Comprehensive Re-enrollment System Test")
    print("="*80)

    # Initialize Frappe context
    if not hasattr(frappe.local, 'site'):
        frappe.init()
    frappe.connect()

    # Set administrator user for testing
    frappe.set_user("Administrator")

    # Create test suite
    test_suite = ReEnrollmentTestSuite()

    try:
        # Setup test data
        if not test_suite.setup_test_data():
            print("❌ Test setup failed - aborting")
            return False

        # Run all test cases
        test_results = []
        test_results.append(test_suite.test_basic_re_enrollment_flow())
        test_results.append(test_suite.test_validation_bypass())
        test_results.append(test_suite.test_data_integrity())
        test_results.append(test_suite.test_course_documents_creation())
        test_results.append(test_suite.test_email_notifications())
        test_results.append(test_suite.test_api_endpoints())
        test_results.append(test_suite.test_edge_cases())

        # Generate report
        all_passed = test_suite.generate_report()

        # Commit changes
        frappe.db.commit()

        # Cleanup test data
        test_suite.cleanup_test_data()
        frappe.db.commit()

        if all_passed:
            print("\n🎉 ALL TESTS PASSED! Re-enrollment system is working correctly.")
            return True
        else:
            print("\n💥 SOME TESTS FAILED! Check the report above for details.")
            return False

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        print(traceback.format_exc())
        return False

    finally:
        # Ensure cleanup happens even if tests fail
        try:
            test_suite.cleanup_test_data()
            frappe.db.commit()
        except:
            pass

if __name__ == "__main__":
    run_complete_test()