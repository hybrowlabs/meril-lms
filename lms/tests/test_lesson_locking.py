# Copyright (c) 2026, FOSS United and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase

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
