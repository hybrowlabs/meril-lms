# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import json
from frappe.utils import nowdate, getdate


class DocumentTemplateRegistry(Document):
    def validate(self):
        self.validate_dates()
        self.validate_country()
        self.validate_template_type()
        self.validate_course_filter()
        self.validate_print_format()
        self.set_defaults()
        self.validate_unique_template()

    def validate_dates(self):
        """Validate that effective dates are logical"""
        if self.effective_to and getdate(self.effective_to) <= getdate(self.effective_from):
            frappe.throw(_("Effective To date must be after Effective From date"))

        if getdate(self.effective_from) > getdate(nowdate()):
            frappe.msgprint(_("Warning: Effective From date is in the future. This template will not be active until {0}").format(self.effective_from))

    def validate_country(self):
        """Validate country if specified"""
        if self.country and not frappe.db.exists("Country", self.country):
            frappe.throw(_("Invalid country: {0}").format(self.country))

    def validate_template_type(self):
        """Validate template type is valid"""
        valid_types = [
            "Employee Declaration",
            "Employee Certificate",
            "Distributor Declaration",
            "Distributor Certificate"
        ]
        if self.template_type not in valid_types:
            frappe.throw(_("Invalid template type: {0}").format(self.template_type))

    def validate_course_filter(self):
        """Validate course filter JSON if provided"""
        if self.course_filter:
            try:
                json.loads(self.course_filter)
            except json.JSONDecodeError as e:
                frappe.throw(_("Invalid JSON in Course Filter: {0}").format(str(e)))

    def validate_print_format(self):
        """Validate print format exists"""
        if self.print_format and not frappe.db.exists("Print Format", self.print_format):
            frappe.throw(_("Invalid Print Format: {0}").format(self.print_format))

    def set_defaults(self):
        """Set default values"""
        if not self.priority:
            self.priority = 0
        if not self.template_version:
            self.template_version = "1.0.0"

    def validate_unique_template(self):
        """Validate template uniqueness for active templates"""
        if self.is_active and not self.is_default:
            existing = frappe.db.sql("""
                SELECT name
                FROM `tabDocument Template Registry`
                WHERE template_type = %s
                AND country = %s
                AND is_active = 1
                AND is_default = 0
                AND name != %s
                AND (
                    (effective_from <= %s AND (effective_to IS NULL OR effective_to >= %s))
                    OR (effective_from <= %s AND (effective_to IS NULL OR effective_to >= %s))
                )
            """, (
                self.template_type,
                self.country,
                self.name or "",
                self.effective_from,
                self.effective_from,
                self.effective_to or "9999-12-31",
                self.effective_to or "9999-12-31"
            ))

            if existing:
                frappe.throw(_("An active template already exists for {0} in {1} for the specified date range").format(
                    self.template_type, self.country
                ))

    def on_update(self):
        """Clear cache on template update"""
        self.clear_template_cache()

    def on_trash(self):
        """Prevent deletion if template is in use"""
        if frappe.db.exists("Document Generation Log", {"template_used": self.name}):
            frappe.throw(_("Cannot delete template that has been used for document generation"))

    def clear_template_cache(self):
        """Clear all template-related cache entries"""
        # Clear Redis cache patterns
        cache_patterns = [
            f"templates:*:{self.name}:*",
            f"template_list:*",
            f"applicable_templates:*"
        ]

        for pattern in cache_patterns:
            frappe.cache().delete_keys(pattern)

    @staticmethod
    def get_applicable_templates(user_type, user_id, course, country=None):
        """Get applicable templates for a given context

        Args:
            user_type: 'employee' or 'distributor'
            user_id: ID of the user
            course: Course name
            country: Country name (optional)

        Returns:
            List of applicable templates sorted by priority
        """
        # Get user country if not provided
        if not country:
            if user_type == 'employee':
                country = frappe.db.get_value("Employee", user_id, "custom_country") or \
                         frappe.db.get_value("Employee", user_id, "country")
            else:
                country = frappe.db.get_value("Distributor", user_id, "country")

        # Build template type pattern
        type_pattern = f"{user_type.capitalize()}%"

        # Query for applicable templates
        templates = frappe.db.sql("""
            SELECT
                name,
                template_name,
                template_type,
                country,
                priority,
                is_default,
                print_format,
                company_name,
                relationship_company,
                template_version,
                metadata_json
            FROM `tabDocument Template Registry`
            WHERE
                is_active = 1
                AND effective_from <= %(today)s
                AND (effective_to IS NULL OR effective_to >= %(today)s)
                AND template_type LIKE %(type_pattern)s
                AND (
                    country = %(country)s
                    OR is_default = 1
                    OR country IS NULL
                )
            ORDER BY
                CASE WHEN country = %(country)s THEN 0 ELSE 1 END,
                priority DESC,
                template_name
        """, {
            'today': nowdate(),
            'type_pattern': type_pattern,
            'country': country
        }, as_dict=1)

        # Apply course filters
        filtered_templates = []
        for template in templates:
            doc = frappe.get_doc("Document Template Registry", template.name)
            if doc.course_filter:
                try:
                    filter_config = json.loads(doc.course_filter)
                    if DocumentTemplateRegistry._matches_course_filter(course, filter_config):
                        filtered_templates.append(template)
                except json.JSONDecodeError:
                    continue
            else:
                # No filter means template applies to all courses
                filtered_templates.append(template)

        return filtered_templates

    @staticmethod
    def _matches_course_filter(course, filter_config):
        """Check if course matches filter configuration

        Args:
            course: Course name
            filter_config: Filter configuration dict

        Returns:
            Boolean indicating if course matches filter
        """
        if not filter_config:
            return True

        # Check include patterns
        if "include" in filter_config:
            for pattern in filter_config["include"]:
                if pattern.lower() in course.lower():
                    return True

        # Check exclude patterns
        if "exclude" in filter_config:
            for pattern in filter_config["exclude"]:
                if pattern.lower() in course.lower():
                    return False

        # Check exact matches
        if "exact" in filter_config:
            return course in filter_config["exact"]

        return "include" not in filter_config  # If no include specified, default to True