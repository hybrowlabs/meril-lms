# Copyright (c) 2026, FOSS United and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from lms.command_palette import (
	CATEGORY_DOCTYPES,
	COURSE_SCOPED_DOCTYPES,
	DOCTYPE_GROUPS,
	PERMISSION_CHECKED_DOCTYPES,
	get_grouped_results,
	get_permitted_names,
	is_visible,
	prepare_search_results,
	search_sqlite,
)
from lms.lms.test_helpers import BaseTestUtils


def row(doctype, name, **extra):
	return {"doctype": doctype, "name": name, **extra}


class TestSearchCategoryValidation(FrappeTestCase):
	"""The category names a doctype for the index's SQL, so it can only ever come
	from CATEGORY_DOCTYPES — a caller's own string must not reach the query."""

	def test_every_category_maps_to_a_grouped_doctype(self):
		for doctype in CATEGORY_DOCTYPES.values():
			self.assertIn(doctype, DOCTYPE_GROUPS)

	def test_unknown_category_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			search_sqlite("kubernetes", category="doctype = 'User' --")

	# Frappe coerces annotated arguments before the body runs, so a wrongly typed
	# argument dies as FrappeTypeError and never reaches the isinstance guard.
	# That guard is the backstop for the day the annotation goes away — dropping
	# it would silently hand a list to the search.
	def test_non_string_category_is_rejected(self):
		with self.assertRaises((frappe.exceptions.FrappeTypeError, frappe.ValidationError)):
			search_sqlite("kubernetes", category=["courses"])

	def test_non_string_query_is_rejected(self):
		with self.assertRaises((frappe.exceptions.FrappeTypeError, frappe.ValidationError)):
			search_sqlite(["kubernetes"])


class TestIndexSchema(FrappeTestCase):
	"""SQLiteSearch validates its schema when the class is instantiated, so a
	doctype missing a content field fails here rather than at the next reindex."""

	def test_every_searchable_category_is_indexed(self):
		from lms.sqlite import LearningSearch

		configs = LearningSearch().doc_configs
		for doctype in CATEGORY_DOCTYPES.values():
			with self.subTest(doctype=doctype):
				self.assertIn(doctype, configs)


class TestTitleOnlySearch(FrappeTestCase):
	def test_the_search_is_restricted_to_titles(self):
		from unittest.mock import patch

		with patch("lms.sqlite.LearningSearch.search") as search:
			search.return_value = {"results": []}
			search_sqlite("cour")

		self.assertTrue(search.call_args.kwargs["title_only"])


class TestResultVisibility(FrappeTestCase):
	def test_unmapped_doctype_is_dropped(self):
		groups = get_grouped_results({"results": [row("User", "someone@example.com")]})
		self.assertEqual(groups, {})

	def test_a_published_course_is_visible_to_a_student(self):
		course = row("LMS Course", "published-course", published=1)
		self.assertTrue(is_visible(course, "LMS Course", ["LMS Student"], {}))

	def test_an_unpublished_course_is_hidden_from_a_student(self):
		course = row("LMS Course", "draft-course", published=0)
		self.assertFalse(is_visible(course, "LMS Course", ["LMS Student"], {}))

	def test_a_closed_job_is_hidden_from_a_student(self):
		job = row("Job Opportunity", "JOB-0001", status="Closed")
		self.assertFalse(is_visible(job, "Job Opportunity", ["LMS Student"], {}))

	# The doctypes added for the palette are gated by frappe.get_list, so what
	# reaches `permitted` is the whole of their visibility rule.
	def test_a_permission_checked_row_needs_its_name_permitted(self):
		quiz = row("LMS Quiz", "quiz-1")
		self.assertFalse(is_visible(quiz, "LMS Quiz", ["LMS Student"], {}))
		self.assertTrue(is_visible(quiz, "LMS Quiz", ["LMS Student"], {"LMS Quiz": {"quiz-1"}}))

	def test_permitted_names_are_not_collected_for_hand_checked_doctypes(self):
		permitted = get_permitted_names([row("LMS Course", "a-course")])
		self.assertNotIn("LMS Course", permitted)

	def test_a_user_without_read_access_gets_an_empty_set_rather_than_an_error(self):
		for doctype in PERMISSION_CHECKED_DOCTYPES:
			with self.subTest(doctype=doctype):
				frappe.set_user("Guest")
				try:
					permitted = get_permitted_names([row(doctype, "does-not-matter")])
				finally:
					frappe.set_user("Administrator")
				self.assertEqual(permitted.get(doctype), set())


class TestQuizAndAssignmentScope(BaseTestUtils):
	"""LMS Quiz and LMS Assignment grant read to LMS Student and register no
	permission_query_conditions hook, so get_list alone handed a student every
	row on the site."""

	def setUp(self):
		super().setUp()
		self.student = self._create_user("palette-student@example.com", "Pal", "Ette", ["LMS Student"])
		self.questions = self._create_quiz_questions()
		self.quiz = self._create_quiz(title="Palette Scope Quiz")
		self.assignment = self._create_assignment(title="Palette Scope Assignment")

	def test_a_student_is_given_no_quiz_or_assignment(self):
		frappe.set_user(self.student.email)
		try:
			for doctype, name in (
				("LMS Quiz", self.quiz.name),
				("LMS Assignment", self.assignment.name),
			):
				with self.subTest(doctype=doctype):
					permitted = get_permitted_names([row(doctype, name)])
					self.assertEqual(permitted[doctype], set())
		finally:
			frappe.set_user("Administrator")

	def test_a_student_can_read_these_doctypes_directly(self):
		"""Pins why the hand-written scope is needed: frappe itself allows it."""
		frappe.set_user(self.student.email)
		try:
			readable = frappe.get_list("LMS Quiz", pluck="name", limit_page_length=0)
		finally:
			frappe.set_user("Administrator")
		self.assertIn(self.quiz.name, readable)

	def test_a_moderator_is_given_them(self):
		permitted = get_permitted_names([row("LMS Quiz", self.quiz.name)])
		self.assertEqual(permitted["LMS Quiz"], {self.quiz.name})

	def test_every_course_scoped_doctype_is_permission_checked(self):
		for doctype in COURSE_SCOPED_DOCTYPES:
			self.assertIn(doctype, PERMISSION_CHECKED_DOCTYPES)


class TestGroupOrder(FrappeTestCase):
	def test_groups_come_back_in_the_documented_order(self):
		result = {
			"results": [
				row("LMS Batch", "b1", published=1, start_date="2999-01-01", modified=2),
				row("LMS Course", "c1", published=1, modified=1),
			]
		}
		titles = [group["title"] for group in prepare_search_results(result)]
		self.assertEqual(titles, ["Courses", "Batches"])


class TestProgramScope(BaseTestUtils):
	"""LMS Program is registered in permission_query_conditions (hooks.py), unlike
	LMS Quiz and LMS Assignment, so get_list is expected to constrain it. This
	pins that, because the palette relies on it rather than scoping by hand."""

	def setUp(self):
		super().setUp()
		self.student = self._create_user("prog-student@example.com", "Prog", "Student", ["LMS Student"])
		self.hidden = frappe.new_doc("LMS Program")
		self.hidden.update({"title": "Palette Unpublished Program", "published": 0})
		self.hidden.save()
		self.cleanup_items.append(("LMS Program", self.hidden.name))

	def test_a_student_is_not_given_an_unpublished_program(self):
		frappe.set_user(self.student.email)
		try:
			permitted = get_permitted_names([row("LMS Program", self.hidden.name)])
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(permitted["LMS Program"], set())
