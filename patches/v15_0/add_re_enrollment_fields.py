"""
Migration patch to add re-enrollment fields to existing course documents
"""

import frappe
from frappe.utils import now


def execute():
    """Add enrollment versioning fields to course document DocTypes"""

    # Add fields to Distributor Course Documents if they don't exist
    add_fields_to_doctype("Distributor Course Documents", [
        {
            "fieldname": "enrollment",
            "fieldtype": "Link",
            "label": "Enrollment",
            "options": "LMS Enrollment",
            "insert_after": "course"
        },
        {
            "fieldname": "enrollment_version",
            "fieldtype": "Int",
            "label": "Enrollment Version",
            "default": "1",
            "read_only": 1,
            "insert_after": "enrollment"
        },
        {
            "fieldname": "is_current_enrollment",
            "fieldtype": "Check",
            "label": "Is Current Enrollment",
            "default": "1",
            "insert_after": "enrollment_version"
        }
    ])

    # Add fields to Employee Course Documents if they don't exist
    add_fields_to_doctype("Employee Course Documents", [
        {
            "fieldname": "enrollment",
            "fieldtype": "Link",
            "label": "Enrollment",
            "options": "LMS Enrollment",
            "insert_after": "course"
        },
        {
            "fieldname": "enrollment_version",
            "fieldtype": "Int",
            "label": "Enrollment Version",
            "default": "1",
            "read_only": 1,
            "insert_after": "enrollment"
        },
        {
            "fieldname": "is_current_enrollment",
            "fieldtype": "Check",
            "label": "Is Current Enrollment",
            "default": "1",
            "insert_after": "enrollment_version"
        }
    ])

    # Update existing records
    update_existing_course_documents()

    frappe.db.commit()
    print("✓ Re-enrollment fields migration completed")


def add_fields_to_doctype(doctype_name, fields):
    """Add fields to a DocType if they don't already exist"""

    if not frappe.db.exists("DocType", doctype_name):
        print(f"⚠️  DocType '{doctype_name}' not found, skipping...")
        return

    try:
        doctype = frappe.get_doc("DocType", doctype_name)
        existing_fields = [f.fieldname for f in doctype.fields]

        fields_added = []
        for field_def in fields:
            if field_def["fieldname"] not in existing_fields:
                # Find the insert_after field position
                insert_after_idx = None
                if "insert_after" in field_def:
                    for idx, f in enumerate(doctype.fields):
                        if f.fieldname == field_def["insert_after"]:
                            insert_after_idx = idx + 1
                            break

                # Create new field
                new_field = frappe.new_doc("DocField")
                new_field.parent = doctype_name
                new_field.parenttype = "DocType"
                new_field.parentfield = "fields"

                # Set field properties
                for key, value in field_def.items():
                    if key != "insert_after" and hasattr(new_field, key):
                        setattr(new_field, key, value)

                # Insert field at position
                if insert_after_idx is not None:
                    doctype.fields.insert(insert_after_idx, new_field)
                else:
                    doctype.fields.append(new_field)

                fields_added.append(field_def["fieldname"])

        if fields_added:
            doctype.save()
            print(f"✓ Added fields to {doctype_name}: {', '.join(fields_added)}")
        else:
            print(f"  All fields already exist in {doctype_name}")

    except Exception as e:
        print(f"❌ Error adding fields to {doctype_name}: {str(e)}")


def update_existing_course_documents():
    """Update existing course documents with enrollment links"""

    # Update Distributor Course Documents
    dist_docs = frappe.get_all(
        "Distributor Course Documents",
        fields=["name", "distributor", "course"]
    )

    for doc_data in dist_docs:
        try:
            # Find the distributor's user
            user_id = frappe.db.get_value("Distributor", doc_data.distributor, "user_id")
            if user_id:
                # Find the most recent enrollment
                enrollment = frappe.get_all(
                    "LMS Enrollment",
                    filters={"member": user_id, "course": doc_data.course},
                    fields=["name", "enrollment_version"],
                    order_by="enrollment_version desc",
                    limit=1
                )

                if enrollment:
                    frappe.db.set_value(
                        "Distributor Course Documents",
                        doc_data.name,
                        {
                            "enrollment": enrollment[0].name,
                            "enrollment_version": enrollment[0].enrollment_version or 1,
                            "is_current_enrollment": 1
                        },
                        update_modified=False
                    )
        except Exception as e:
            print(f"  Warning: Could not update distributor doc {doc_data.name}: {str(e)}")

    # Update Employee Course Documents
    emp_docs = frappe.get_all(
        "Employee Course Documents",
        fields=["name", "employee", "course"]
    )

    for doc_data in emp_docs:
        try:
            # Find the employee's user
            user_id = frappe.db.get_value("Employee", doc_data.employee, "user_id")
            if user_id:
                # Find the most recent enrollment
                enrollment = frappe.get_all(
                    "LMS Enrollment",
                    filters={"member": user_id, "course": doc_data.course},
                    fields=["name", "enrollment_version"],
                    order_by="enrollment_version desc",
                    limit=1
                )

                if enrollment:
                    frappe.db.set_value(
                        "Employee Course Documents",
                        doc_data.name,
                        {
                            "enrollment": enrollment[0].name,
                            "enrollment_version": enrollment[0].enrollment_version or 1,
                            "is_current_enrollment": 1
                        },
                        update_modified=False
                    )
        except Exception as e:
            print(f"  Warning: Could not update employee doc {doc_data.name}: {str(e)}")

    print(f"✓ Updated {len(dist_docs)} distributor and {len(emp_docs)} employee course documents")