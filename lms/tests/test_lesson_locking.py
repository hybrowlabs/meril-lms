# Copyright (c) 2026, FOSS United and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from lms.lms.permissions import enforces_lesson_completion, get_locked_lessons
from lms.lms.test_helpers import BaseTestUtils
from lms.lms.utils import compute_locked_lessons


class TestComputeLockedLessons(FrappeTestCase):
	def test_nothing_complete_leaves_only_the_first_lesson_open(self):
		locked = compute_locked_lessons(["L1", "L2", "L3"], set())
		self.assertEqual(locked, {"L2", "L3"})

	def test_completing_the_first_opens_the_second(self):
		locked = compute_locked_lessons(["L1", "L2", "L3"], {"L1"})
		self.assertEqual(locked, {"L3"})

	def test_all_complete_locks_nothing(self):
		locked = compute_locked_lessons(["L1", "L2"], {"L1", "L2"})
		self.assertEqual(locked, set())

	def test_a_lesson_completed_out_of_order_stays_open(self):
		# Flag switched on mid-cohort: L3 was already finished, so it must not lock.
		locked = compute_locked_lessons(["L1", "L2", "L3", "L4"], {"L3"})
		self.assertEqual(locked, {"L2", "L4"})

	def test_empty_course_locks_nothing(self):
		self.assertEqual(compute_locked_lessons([], set()), set())


class TestLessonLockingIntegration(BaseTestUtils):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# The worktree's field reaches the test site's schema only via reload_doctype;
		# bench migrate cannot see this worktree.
		frappe.reload_doctype("LMS Course")

	def setUp(self):
		super().setUp()
		self.student = self._create_user("locking-student@example.com", "Lock", "Student", ["LMS Student"])
		self.author = self._create_user(
			"locking-author@example.com", "Lock", "Author", ["Course Creator", "Moderator"]
		)
		self.course = self._create_course(title="Locking Course", instructor=self.author.email)
		self.chapter = self._create_chapter("Locking Chapter", self.course.name)
		self._create_chapter_reference(self.course.name, self.chapter.name, idx=1)

		self.lessons = []
		for idx in range(1, 4):
			lesson = self._create_lesson(f"Locking Lesson {idx}", self.chapter.name, self.course.name)
			self.lessons.append(lesson)

		chapter_doc = frappe.get_doc("Course Chapter", self.chapter.name)
		for lesson in self.lessons:
			chapter_doc.append("lessons", {"lesson": lesson.name})
		chapter_doc.save()

		self._create_enrollment(self.student.email, self.course.name)
		frappe.set_user(self.student.email)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def _enable(self):
		frappe.db.set_value("LMS Course", self.course.name, "enforce_lesson_completion", 1)

	def test_flag_off_locks_nothing(self):
		self.assertFalse(enforces_lesson_completion(self.course.name))
		self.assertEqual(get_locked_lessons(self.course.name), set())

	def test_flag_on_locks_everything_past_the_first_lesson(self):
		self._enable()
		self.assertTrue(enforces_lesson_completion(self.course.name))
		self.assertEqual(
			get_locked_lessons(self.course.name),
			{self.lessons[1].name, self.lessons[2].name},
		)

	def test_completing_the_first_lesson_unlocks_the_second(self):
		self._enable()
		frappe.set_user("Administrator")
		progress = self._create_progress(self.student.email, self.course.name, self.lessons[0].name)
		frappe.db.set_value("LMS Course Progress", progress.name, "status", "Complete")
		frappe.set_user(self.student.email)
		self.assertEqual(get_locked_lessons(self.course.name), {self.lessons[2].name})

	def test_partially_complete_does_not_unlock(self):
		self._enable()
		frappe.set_user("Administrator")
		progress = self._create_progress(self.student.email, self.course.name, self.lessons[0].name)
		frappe.db.set_value("LMS Course Progress", progress.name, "status", "Partially Complete")
		frappe.set_user(self.student.email)
		self.assertEqual(
			get_locked_lessons(self.course.name),
			{self.lessons[1].name, self.lessons[2].name},
		)

	def test_course_author_is_exempt(self):
		self._enable()
		frappe.set_user(self.author.email)
		self.assertFalse(enforces_lesson_completion(self.course.name))
		self.assertEqual(get_locked_lessons(self.course.name), set())

	def test_unenrolled_user_is_not_gated_by_sequencing(self):
		self._enable()
		frappe.set_user("Guest")
		self.assertFalse(enforces_lesson_completion(self.course.name))

	def test_malformed_course_argument_locks_nothing(self):
		self.assertEqual(get_locked_lessons(None), set())
		self.assertEqual(get_locked_lessons(["!=", ""]), set())
