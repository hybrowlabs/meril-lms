import unittest
import unittest.mock

import frappe
from .utils import slugify, apply_role_based_course_filtering, apply_country_based_course_filtering


class TestUtils(unittest.TestCase):
	def test_simple(self):
		self.assertEqual(slugify("hello-world"), "hello-world")
		self.assertEqual(slugify("Hello World"), "hello-world")
		self.assertEqual(slugify("Hello, World!"), "hello-world")

	def test_duplicates(self):
		self.assertEqual(slugify("Hello World", ["hello-world"]), "hello-world-2")

		self.assertEqual(
			slugify("Hello World", ["hello-world", "hello-world-2"]), "hello-world-3"
		)

	def test_role_based_filtering_with_no_filters(self):
		"""Test role-based filtering with empty filters"""
		# Mock frappe.session.user and roles
		with unittest.mock.patch('frappe.session.user', 'test@example.com'):
			with unittest.mock.patch('frappe.get_roles', return_value=['Distributor']):
				with unittest.mock.patch('lms.lms.utils.has_privileged_role', return_value=False):
					with unittest.mock.patch('frappe.db.sql', return_value=[('course1',), ('course2',)]):
						filters = apply_role_based_course_filtering(None)
						self.assertIn('name', filters)
						self.assertEqual(filters['name'][0], 'in')
						self.assertIn('course1', filters['name'][1])
						self.assertIn('course2', filters['name'][1])

	def test_role_based_filtering_privileged_user(self):
		"""Test that privileged users bypass role filtering"""
		with unittest.mock.patch('lms.lms.utils.has_privileged_role', return_value=True):
			filters = {}
			result = apply_role_based_course_filtering(filters)
			# Should return the same filters unchanged
			self.assertEqual(result, filters)

	def test_country_based_filtering_with_no_country(self):
		"""Test country-based filtering when user has no country set"""
		with unittest.mock.patch('lms.lms.utils.has_privileged_role', return_value=False):
			with unittest.mock.patch('lms.lms.utils.get_user_country', return_value=None):
				filters = apply_country_based_course_filtering({})
				self.assertIn('name', filters)
				self.assertEqual(filters['name'], ['in', []])  # Empty list means no courses

	def test_country_based_filtering_with_country(self):
		"""Test country-based filtering with valid country"""
		with unittest.mock.patch('lms.lms.utils.has_privileged_role', return_value=False):
			with unittest.mock.patch('lms.lms.utils.get_user_country', return_value='India'):
				with unittest.mock.patch('frappe.db.sql', return_value=[('course1',), ('course3',)]):
					filters = apply_country_based_course_filtering({})
					self.assertIn('name', filters)
					self.assertEqual(filters['name'][0], 'in')
					self.assertIn('course1', filters['name'][1])
					self.assertIn('course3', filters['name'][1])
