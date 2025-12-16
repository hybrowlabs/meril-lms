# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, nowdate


class CountryTemplateMapping(Document):
    def validate(self):
        self.validate_templates()
        self.validate_dates()
        self.validate_uniqueness()

    def validate_templates(self):
        """Validate that primary and fallback templates exist and are of correct type"""
        if self.primary_template:
            template_type = frappe.db.get_value("Document Template Registry", self.primary_template, "template_type")
            if template_type != self.template_type:
                frappe.throw(_("Primary template type must match the mapping template type"))

        if self.fallback_template:
            template_type = frappe.db.get_value("Document Template Registry", self.fallback_template, "template_type")
            if template_type != self.template_type:
                frappe.throw(_("Fallback template type must match the mapping template type"))

            if self.fallback_template == self.primary_template:
                frappe.throw(_("Fallback template cannot be the same as primary template"))

    def validate_dates(self):
        """Validate effective dates"""
        if self.effective_to and getdate(self.effective_to) <= getdate(self.effective_from):
            frappe.throw(_("Effective To date must be after Effective From date"))

    def validate_uniqueness(self):
        """Validate no overlapping active mappings for same country and template type"""
        if self.is_active:
            existing = frappe.db.sql("""
                SELECT name
                FROM `tabCountry Template Mapping`
                WHERE country = %s
                AND template_type = %s
                AND is_active = 1
                AND name != %s
                AND (
                    (effective_from <= %s AND (effective_to IS NULL OR effective_to >= %s))
                    OR (effective_from <= %s AND (effective_to IS NULL OR effective_to >= %s))
                )
            """, (
                self.country,
                self.template_type,
                self.name or "",
                self.effective_from,
                self.effective_from,
                self.effective_to or "9999-12-31",
                self.effective_to or "9999-12-31"
            ))

            if existing:
                frappe.throw(_("An active mapping already exists for {0} in {1} for the specified date range").format(
                    self.template_type, self.country
                ))

    @staticmethod
    def get_template_for_country(country, template_type, course=None):
        """Get the appropriate template for a country and type

        Args:
            country: Country name
            template_type: Type of template
            course: Course name (optional, for exception handling)

        Returns:
            Template name or None
        """
        # First, check for active country mapping
        mapping = frappe.db.sql("""
            SELECT name, primary_template, fallback_template
            FROM `tabCountry Template Mapping`
            WHERE country = %s
            AND template_type = %s
            AND is_active = 1
            AND effective_from <= %s
            AND (effective_to IS NULL OR effective_to >= %s)
            ORDER BY priority DESC
            LIMIT 1
        """, (country, template_type, nowdate(), nowdate()), as_dict=1)

        if not mapping:
            return None

        mapping_doc = frappe.get_doc("Country Template Mapping", mapping[0].name)

        # Check for course exceptions
        if course and mapping_doc.course_exceptions:
            for exception in mapping_doc.course_exceptions:
                if exception.course == course and exception.override_template:
                    # Verify override template is active
                    if frappe.db.get_value("Document Template Registry", exception.override_template, "is_active"):
                        return exception.override_template

        # Return primary template if active, otherwise fallback
        if frappe.db.get_value("Document Template Registry", mapping_doc.primary_template, "is_active"):
            return mapping_doc.primary_template
        elif mapping_doc.fallback_template and frappe.db.get_value("Document Template Registry", mapping_doc.fallback_template, "is_active"):
            return mapping_doc.fallback_template

        return None