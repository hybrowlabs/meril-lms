# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime
import json


class DocumentGenerationLog(Document):
    def validate(self):
        self.validate_user_type()
        self.set_defaults()

    def validate_user_type(self):
        """Validate that employee or distributor is set based on role type"""
        if self.role_type == "Employee" and not self.employee:
            frappe.throw("Employee must be specified for Employee role type")
        elif self.role_type == "Distributor" and not self.distributor:
            frappe.throw("Distributor must be specified for Distributor role type")

    def set_defaults(self):
        """Set default values"""
        if not self.generation_datetime:
            self.generation_datetime = now_datetime()

        if not self.generation_status:
            self.generation_status = "Pending"

    @staticmethod
    def create_log(user, role_type, template, generation_type="Manual", **kwargs):
        """Create a new document generation log entry

        Args:
            user: User ID
            role_type: Type of user role
            template: Template name or ID
            generation_type: Type of generation
            **kwargs: Additional fields

        Returns:
            Created log document
        """
        log = frappe.new_doc("Document Generation Log")
        log.user = user
        log.role_type = role_type
        log.template_used = template
        log.generation_type = generation_type
        log.generation_status = "Pending"
        log.generation_datetime = now_datetime()

        # Set additional fields from kwargs
        for key, value in kwargs.items():
            if hasattr(log, key):
                setattr(log, key, value)

        log.insert(ignore_permissions=True)
        frappe.db.commit()

        return log

    @staticmethod
    def update_status(log_id, status, error_message=None, file_reference=None, processing_time_ms=None):
        """Update the status of a generation log

        Args:
            log_id: Log document name
            status: New status
            error_message: Error message if failed
            file_reference: File reference if successful
            processing_time_ms: Processing time in milliseconds
        """
        log = frappe.get_doc("Document Generation Log", log_id)
        log.generation_status = status

        if error_message:
            log.error_message = error_message

        if file_reference:
            log.file_reference = file_reference

        if processing_time_ms:
            log.processing_time_ms = processing_time_ms

        log.save(ignore_permissions=True)
        frappe.db.commit()

    @staticmethod
    def get_user_logs(user, limit=10):
        """Get recent generation logs for a user

        Args:
            user: User ID
            limit: Number of logs to return

        Returns:
            List of log entries
        """
        return frappe.db.sql("""
            SELECT
                name,
                template_used,
                generation_status,
                generation_datetime,
                file_reference,
                error_message
            FROM `tabDocument Generation Log`
            WHERE user = %s
            ORDER BY generation_datetime DESC
            LIMIT %s
        """, (user, limit), as_dict=1)

    @staticmethod
    def get_statistics(from_date=None, to_date=None):
        """Get generation statistics

        Args:
            from_date: Start date for statistics
            to_date: End date for statistics

        Returns:
            Dictionary with statistics
        """
        conditions = []
        params = []

        if from_date:
            conditions.append("generation_datetime >= %s")
            params.append(from_date)

        if to_date:
            conditions.append("generation_datetime <= %s")
            params.append(to_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        stats = frappe.db.sql(f"""
            SELECT
                COUNT(*) as total_generations,
                SUM(CASE WHEN generation_status = 'Success' THEN 1 ELSE 0 END) as successful_generations,
                SUM(CASE WHEN generation_status = 'Failed' THEN 1 ELSE 0 END) as failed_generations,
                AVG(CASE WHEN processing_time_ms > 0 THEN processing_time_ms ELSE NULL END) as avg_processing_time,
                COUNT(DISTINCT user) as unique_users,
                COUNT(DISTINCT template_used) as templates_used
            FROM `tabDocument Generation Log`
            WHERE {where_clause}
        """, params, as_dict=1)[0]

        # Get top templates
        top_templates = frappe.db.sql(f"""
            SELECT
                template_used,
                COUNT(*) as usage_count
            FROM `tabDocument Generation Log`
            WHERE {where_clause}
            AND template_used IS NOT NULL
            GROUP BY template_used
            ORDER BY usage_count DESC
            LIMIT 5
        """, params, as_dict=1)

        stats["top_templates"] = top_templates

        return stats