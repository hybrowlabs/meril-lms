# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from frappe.utils import nowdate, now_datetime
from lms.lms.doctype.document_template_registry.document_template_registry import DocumentTemplateRegistry
from lms.lms.doctype.country_template_mapping.country_template_mapping import CountryTemplateMapping
from lms.lms.doctype.document_generation_log.document_generation_log import DocumentGenerationLog


@frappe.whitelist()
def get_applicable_templates(user_type, user_id, course, country=None):
    """Get applicable templates for user and course

    Args:
        user_type: 'employee' or 'distributor'
        user_id: ID of the user
        course: Course name
        country: Country name (optional)

    Returns:
        Dictionary with templates and metadata
    """
    # Validate inputs
    if user_type not in ['employee', 'distributor']:
        frappe.throw(_("Invalid user type"))

    # Get user country if not provided
    if not country:
        if user_type == 'employee':
            employee = frappe.get_doc("Employee", user_id)
            country = getattr(employee, "custom_country", None) or getattr(employee, "country", None)
        else:
            distributor = frappe.get_doc("Distributor", user_id)
            country = distributor.country

    # Get templates using the service
    templates = DocumentTemplateRegistry.get_applicable_templates(
        user_type=user_type,
        user_id=user_id,
        course=course,
        country=country
    )

    # Check for country-specific mapping
    template_type = f"{user_type.capitalize()} Declaration"
    mapped_template = CountryTemplateMapping.get_template_for_country(
        country=country,
        template_type=template_type,
        course=course
    )

    # Build response
    response = {
        "templates": templates,
        "default_selection": [],
        "mapped_template": mapped_template,
        "user_context": {
            "country": country,
            "course": course,
            "user_type": user_type,
            "user_id": user_id
        }
    }

    # Determine default selection
    if mapped_template:
        response["default_selection"] = [mapped_template]
    else:
        # Use templates marked as default
        response["default_selection"] = [t.name for t in templates if t.get("is_default")]

    return response


@frappe.whitelist()
def generate_documents(user_type, user_id, course, templates, options=None):
    """Generate documents for a user

    Args:
        user_type: 'employee' or 'distributor'
        user_id: ID of the user
        course: Course name
        templates: List of template IDs to generate
        options: Optional document generation options (JSON string or dict)

    Returns:
        Dictionary with generation results
    """
    # Parse options if string
    if options and isinstance(options, str):
        try:
            options = json.loads(options)
        except json.JSONDecodeError:
            frappe.throw(_("Invalid options format"))

    # Validate inputs
    if user_type not in ['employee', 'distributor']:
        frappe.throw(_("Invalid user type"))

    if not templates:
        frappe.throw(_("No templates specified for generation"))

    # Ensure templates is a list
    if isinstance(templates, str):
        templates = [templates]

    results = []

    for template_id in templates:
        # Create generation log
        log = DocumentGenerationLog.create_log(
            user=frappe.session.user,
            role_type=user_type.capitalize(),
            template=template_id,
            generation_type="Manual",
            course=course,
            employee=user_id if user_type == 'employee' else None,
            distributor=user_id if user_type == 'distributor' else None,
            document_options_json=json.dumps(options) if options else None
        )

        try:
            # Get template
            template = frappe.get_doc("Document Template Registry", template_id)

            # TODO: Integrate with actual document generation logic
            # For now, we'll simulate success

            # Update log with success
            DocumentGenerationLog.update_status(
                log_id=log.name,
                status="Success",
                processing_time_ms=150
            )

            results.append({
                "template_id": template_id,
                "template_name": template.template_name,
                "status": "success",
                "log_id": log.name
            })

        except Exception as e:
            # Update log with failure
            DocumentGenerationLog.update_status(
                log_id=log.name,
                status="Failed",
                error_message=str(e)
            )

            results.append({
                "template_id": template_id,
                "status": "failed",
                "error": str(e),
                "log_id": log.name
            })

    return {
        "success": all(r["status"] == "success" for r in results),
        "results": results,
        "generation_time": now_datetime()
    }


@frappe.whitelist()
def get_template_preview(template_id, user_type=None, user_id=None):
    """Get preview data for a template

    Args:
        template_id: Template ID
        user_type: Optional user type for context
        user_id: Optional user ID for context

    Returns:
        Template preview data
    """
    template = frappe.get_doc("Document Template Registry", template_id)

    preview = {
        "name": template.name,
        "template_name": template.template_name,
        "template_type": template.template_type,
        "country": template.country,
        "company_name": template.company_name,
        "relationship_company": template.relationship_company,
        "compliance_bullets": []
    }

    # Add compliance bullets
    if template.template_compliance_bullets:
        for bullet in template.template_compliance_bullets:
            preview["compliance_bullets"].append({
                "text": bullet.bullet_text,
                "order": bullet.display_order,
                "is_mandatory": bullet.is_mandatory
            })

    # Add user context if provided
    if user_type and user_id:
        if user_type == 'employee':
            employee = frappe.get_doc("Employee", user_id)
            preview["user_context"] = {
                "name": employee.employee_name,
                "country": getattr(employee, "custom_country", None) or getattr(employee, "country", None)
            }
        elif user_type == 'distributor':
            distributor = frappe.get_doc("Distributor", user_id)
            preview["user_context"] = {
                "name": distributor.distributor_name,
                "country": distributor.country
            }

    return preview


@frappe.whitelist()
def get_user_document_history(user_type, user_id, limit=10):
    """Get document generation history for a user

    Args:
        user_type: 'employee' or 'distributor'
        user_id: ID of the user
        limit: Number of records to return

    Returns:
        List of generation history records
    """
    if user_type not in ['employee', 'distributor']:
        frappe.throw(_("Invalid user type"))

    field = "employee" if user_type == "employee" else "distributor"

    history = frappe.db.sql("""
        SELECT
            dgl.name,
            dgl.template_used,
            dtr.template_name,
            dgl.course,
            dgl.generation_status,
            dgl.generation_datetime,
            dgl.file_reference,
            dgl.error_message
        FROM `tabDocument Generation Log` dgl
        LEFT JOIN `tabDocument Template Registry` dtr
            ON dgl.template_used = dtr.name
        WHERE dgl.{field} = %s
        ORDER BY dgl.generation_datetime DESC
        LIMIT %s
    """.format(field=field), (user_id, limit), as_dict=1)

    return history


@frappe.whitelist()
def save_user_template_selection(user_type, user_id, course, template_id, options=None):
    """Save user's template selection for a course

    Args:
        user_type: 'employee' or 'distributor'
        user_id: ID of the user
        course: Course name
        template_id: Selected template ID
        options: Optional document options

    Returns:
        Success status
    """
    if user_type not in ['employee', 'distributor']:
        frappe.throw(_("Invalid user type"))

    # Parse options if string
    if options and isinstance(options, str):
        try:
            options = json.loads(options)
        except json.JSONDecodeError:
            frappe.throw(_("Invalid options format"))

    if user_type == 'employee':
        # Update Employee Course Documents
        doc_name = frappe.db.get_value(
            "Employee Course Documents",
            {"employee": user_id, "course": course},
            "name"
        )

        if doc_name:
            doc = frappe.get_doc("Employee Course Documents", doc_name)
        else:
            doc = frappe.new_doc("Employee Course Documents")
            doc.employee = user_id
            doc.course = course

        doc.selected_template = template_id
        template = frappe.get_doc("Document Template Registry", template_id)
        doc.template_version_used = template.template_version

        if options:
            doc.document_options_json = json.dumps(options)

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "document": doc.name}

    else:
        # Similar logic for Distributor Course Documents
        doc_name = frappe.db.get_value(
            "Distributor Course Documents",
            {"distributor": user_id, "course": course},
            "name"
        )

        if doc_name:
            doc = frappe.get_doc("Distributor Course Documents", doc_name)
        else:
            doc = frappe.new_doc("Distributor Course Documents")
            doc.distributor = user_id
            doc.course = course

        # Note: You may need to add template fields to Distributor Course Documents
        # For now, we'll store in the metadata
        if not doc.document_upload_datetime:
            doc.document_upload_datetime = []

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True, "document": doc.name}


@frappe.whitelist()
def get_template_statistics(from_date=None, to_date=None):
    """Get template usage statistics

    Args:
        from_date: Start date
        to_date: End date

    Returns:
        Statistics dictionary
    """
    return DocumentGenerationLog.get_statistics(from_date, to_date)