#!/usr/bin/env python3

import frappe

def test_employee_completion_certificate():
    try:
        # Get the specific Employee Course Documents record
        doc_name = "gmgae5o7t4"

        print(f"Testing print format generation for document: {doc_name}")

        # Try to generate the PDF
        pdf_content = frappe.get_print(
            doctype="Employee Course Documents",
            name=doc_name,
            print_format="Employee Completion Certificate",
            as_pdf=True,
            no_letterhead=1
        )

        print(f"PDF generation successful! Content length: {len(pdf_content)} bytes")
        return True

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    frappe.init(site="lms.localhost")
    frappe.connect()
    test_employee_completion_certificate()