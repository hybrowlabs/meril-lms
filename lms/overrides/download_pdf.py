import frappe

@frappe.whitelist(allow_guest=True)
def custom_download_pdf(
    doctype: str,
    name: str,
    format=None,
    doc=None,
    no_letterhead=0,
    language=None,
    letterhead=None,
    pdf_generator=None,
    custom_filename=None,
    custom_type=None
):
    """
    Wrapper around frappe.utils.print_format.download_pdf that allows custom filename and type in response.
    """
    # Import here to avoid circular import at module level
    from frappe.utils.print_format import download_pdf as original_download_pdf

    # Call the original download_pdf to generate the PDF and set frappe.local.response
    original_download_pdf(
        doctype=doctype,
        name=name,
        format=format,
        doc=doc,
        no_letterhead=no_letterhead,
        language=language,
        letterhead=letterhead,
        pdf_generator=pdf_generator,
    )

    # Overwrite the filename and type in the response if custom values are provided
    if custom_filename:
        frappe.local.response.filename = custom_filename + ".pdf"
    if custom_type:
        frappe.local.response.type = custom_type
