# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

"""
Integration module to connect the new dynamic document generation system
with the existing documents.py implementation.

This module provides backward-compatible functions that can replace
the hardcoded template logic in documents.py.
"""

import frappe
from frappe import _
import json
from frappe.utils import nowdate
from lms.lms.doctype.document_template_registry.document_template_registry import DocumentTemplateRegistry
from lms.lms.doctype.country_template_mapping.country_template_mapping import CountryTemplateMapping
from lms.lms.doctype.document_generation_log.document_generation_log import DocumentGenerationLog


def get_employee_declaration_template_dynamic(employee_doc, course_name=None, course_title=None):
    """
    Dynamic replacement for get_employee_declaration_template function.
    Returns template metadata from the database instead of hardcoded values.

    Args:
        employee_doc: Employee document
        course_name: Course name (optional)
        course_title: Course title (optional)

    Returns:
        Dictionary with template information
    """
    # Get employee country
    country_raw = (getattr(employee_doc, "custom_country", None) or
                  getattr(employee_doc, "country", None) or "").strip()

    # Get course identifier
    course = course_title or course_name or ""

    # Get applicable templates from registry
    templates = DocumentTemplateRegistry.get_applicable_templates(
        user_type="employee",
        user_id=employee_doc.name,
        course=course,
        country=country_raw
    )

    # Try to get country-specific mapping first
    mapped_template_name = CountryTemplateMapping.get_template_for_country(
        country=country_raw,
        template_type="Employee Declaration",
        course=course
    )

    template = None

    if mapped_template_name:
        # Use the mapped template
        template = frappe.get_doc("Document Template Registry", mapped_template_name)
    elif templates:
        # Use the highest priority template
        template = frappe.get_doc("Document Template Registry", templates[0]["name"])
    else:
        # No template found, return default structure
        return {
            "display_name": "Default Employee Declaration",
            "company": "Meril Life Sciences Pvt. Ltd.",
            "relationship_company": "Meril Life Sciences Pvt. Ltd.",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        }

    # Build response in the expected format
    response = {
        "display_name": template.template_name,
        "company": template.company_name or "Meril Life Sciences Pvt. Ltd.",
        "relationship_company": template.relationship_company or template.company_name or "Meril Life Sciences Pvt. Ltd.",
        "bullets": []
    }

    # Add compliance bullets
    if template.template_compliance_bullets:
        bullets = sorted(template.template_compliance_bullets, key=lambda x: x.display_order)
        response["bullets"] = [bullet.bullet_text for bullet in bullets]

    # Add template metadata for tracking
    response["_template_id"] = template.name
    response["_template_version"] = template.template_version

    return response


def get_employee_completion_certificate_name_dynamic(employee_doc, course_name=None, course_title=None):
    """
    Dynamic replacement for get_employee_completion_certificate_name function.
    Returns the appropriate completion certificate print format from the database.

    Args:
        employee_doc: Employee document
        course_name: Course name (optional)
        course_title: Course title (optional)

    Returns:
        String: Name of the print format to use
    """
    # Get employee country
    country = (getattr(employee_doc, "custom_country", None) or
              getattr(employee_doc, "country", None) or "").strip()

    # Get course identifier
    course = course_title or course_name or ""

    # Check for ROW courses first
    normalized_course = "".join(course.lower().split())
    if normalized_course.startswith("row1") or normalized_course.startswith("row2"):
        # For ROW courses, check if specific template exists
        templates = DocumentTemplateRegistry.get_applicable_templates(
            user_type="employee",
            user_id=employee_doc.name,
            course=course,
            country=country
        )

        for template_data in templates:
            template = frappe.get_doc("Document Template Registry", template_data["name"])
            if template.course_filter:
                try:
                    filter_config = json.loads(template.course_filter)
                    if "include" in filter_config:
                        for pattern in filter_config["include"]:
                            if pattern.lower() in normalized_course:
                                return template.print_format
                except json.JSONDecodeError:
                    pass

        # Default for ROW courses
        return "International Completion Certificate"

    # Try to get country-specific mapping
    mapped_template_name = CountryTemplateMapping.get_template_for_country(
        country=country,
        template_type="Employee Certificate",
        course=course
    )

    if mapped_template_name:
        template = frappe.get_doc("Document Template Registry", mapped_template_name)
        return template.print_format

    # Get applicable templates
    templates = DocumentTemplateRegistry.get_applicable_templates(
        user_type="employee",
        user_id=employee_doc.name,
        course=course,
        country=country
    )

    # Find certificate templates
    for template_data in templates:
        if template_data["template_type"] == "Employee Certificate":
            template = frappe.get_doc("Document Template Registry", template_data["name"])
            return template.print_format

    # Default fallback based on country
    if country and country.lower() == "india":
        return "Employee Completion Certificate"

    return "International Completion Certificate"


def log_document_generation(user, user_type, template_id, course, status="Success", **kwargs):
    """
    Log document generation activity to the database.

    Args:
        user: User generating the document
        user_type: Type of user (employee/distributor)
        template_id: ID of the template used
        course: Course name
        status: Generation status
        **kwargs: Additional parameters to log

    Returns:
        Document Generation Log entry
    """
    log_entry = DocumentGenerationLog.create_log(
        user=user,
        role_type=user_type.capitalize(),
        template=template_id,
        generation_type="Manual",
        course=course,
        **kwargs
    )

    if status != "Pending":
        DocumentGenerationLog.update_status(
            log_id=log_entry.name,
            status=status
        )

    return log_entry


def get_distributor_declaration_template_dynamic(distributor_doc, course_name=None):
    """
    Dynamic replacement for distributor declaration template selection.

    Args:
        distributor_doc: Distributor document
        course_name: Course name (optional)

    Returns:
        Dictionary with template information
    """
    # Get distributor country
    country = getattr(distributor_doc, "country", "")

    # Get applicable templates from registry
    templates = DocumentTemplateRegistry.get_applicable_templates(
        user_type="distributor",
        user_id=distributor_doc.name,
        course=course_name,
        country=country
    )

    # Try to get country-specific mapping first
    mapped_template_name = CountryTemplateMapping.get_template_for_country(
        country=country,
        template_type="Distributor Declaration",
        course=course_name
    )

    template = None

    if mapped_template_name:
        template = frappe.get_doc("Document Template Registry", mapped_template_name)
    elif templates:
        template = frappe.get_doc("Document Template Registry", templates[0]["name"])
    else:
        # Return default structure
        return {
            "display_name": "Default Distributor Declaration",
            "company": "Meril Life Sciences Pvt. Ltd.",
            "relationship_company": "Meril Life Sciences Pvt. Ltd.",
            "bullets": []
        }

    # Build response
    response = {
        "display_name": template.template_name,
        "company": template.company_name or "Meril Life Sciences Pvt. Ltd.",
        "relationship_company": template.relationship_company or template.company_name,
        "bullets": []
    }

    # Add compliance bullets
    if template.template_compliance_bullets:
        bullets = sorted(template.template_compliance_bullets, key=lambda x: x.display_order)
        response["bullets"] = [bullet.bullet_text for bullet in bullets]

    response["_template_id"] = template.name
    response["_template_version"] = template.template_version

    return response


def update_employee_course_document_with_template(employee_id, course, template_id, options=None):
    """
    Update Employee Course Documents with selected template information.

    Args:
        employee_id: Employee ID
        course: Course name
        template_id: Selected template ID
        options: Optional document options

    Returns:
        Updated Employee Course Documents record
    """
    # Get or create the document
    doc_name = frappe.db.get_value(
        "Employee Course Documents",
        {"employee": employee_id, "course": course},
        "name"
    )

    if doc_name:
        doc = frappe.get_doc("Employee Course Documents", doc_name)
    else:
        doc = frappe.new_doc("Employee Course Documents")
        doc.employee = employee_id
        doc.course = course

    # Update template information
    doc.selected_template = template_id

    template = frappe.get_doc("Document Template Registry", template_id)
    doc.template_version_used = template.template_version

    if options:
        doc.document_options_json = json.dumps(options) if not isinstance(options, str) else options

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return doc


# Monkey-patch functions for backward compatibility
def enable_dynamic_templates():
    """
    Enable dynamic template system by replacing hardcoded functions.
    Call this function during app initialization.
    """
    try:
        from lms.overrides import documents

        # Replace the hardcoded functions with dynamic ones
        documents.get_employee_declaration_template = get_employee_declaration_template_dynamic
        documents.get_employee_completion_certificate_name = get_employee_completion_certificate_name_dynamic

        # Add new functions
        documents.get_distributor_declaration_template_dynamic = get_distributor_declaration_template_dynamic
        documents.log_document_generation = log_document_generation
        documents.update_employee_course_document_with_template = update_employee_course_document_with_template

        frappe.log_error("Dynamic document templates enabled successfully", "Template System")
        return True

    except Exception as e:
        frappe.log_error(f"Failed to enable dynamic templates: {str(e)}", "Template System")
        return False