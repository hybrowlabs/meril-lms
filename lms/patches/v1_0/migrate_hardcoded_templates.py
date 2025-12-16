# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate


def execute():
    """Migrate hardcoded templates from documents.py to database"""

    # Template configurations based on existing hardcoded logic
    template_configs = [
        # Italy Templates
        {
            "template_name": "Italy Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "Italy",
            "country_code": "IT",
            "company_name": "Meril Italy Srl",
            "relationship_company": "Meril Italy Srl",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Medtech Europe-Code of ethical business practices",
                "Codice etico (Decree 231/2001)",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering",
            ]
        },
        # Germany Templates
        {
            "template_name": "Germany Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "Germany",
            "country_code": "DE",
            "company_name": "Meril GmbH",
            "relationship_company": "Meril GmbH",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Medtech Europe-Code of ethical business practices",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        },
        # Poland Templates
        {
            "template_name": "Poland Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "Poland",
            "country_code": "PL",
            "company_name": "Meril Polska Sp. z o.o.",
            "relationship_company": "Meril Polska Sp. z o.o.",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Medtech Europe-Code of ethical business practices",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        },
        # Spain Templates
        {
            "template_name": "Spain Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "Spain",
            "country_code": "ES",
            "company_name": "Meril Ibérica S.A.",
            "relationship_company": "Meril Ibérica S.A.",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Medtech Europe-Code of ethical business practices",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering",
                "Spanish Criminal Code"
            ]
        },
        # Brazil Templates
        {
            "template_name": "Brazil Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "Brazil",
            "country_code": "BR",
            "company_name": "Meril Endo Brasil",
            "relationship_company": "Meril Endo Brasil",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Brazilian Clean Company Act (Law No. 12,846/2013)",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        },
        # Turkey Templates
        {
            "template_name": "Turkey Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "Turkey",
            "country_code": "TR",
            "company_name": "Meril Medikal",
            "relationship_company": "Meril Medikal",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Turkish Criminal Code",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        },
        # South Africa Templates
        {
            "template_name": "South Africa Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "South Africa",
            "country_code": "ZA",
            "company_name": "Meril South Africa (Pty) Ltd",
            "relationship_company": "Meril South Africa (Pty) Ltd",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Prevention and Combating of Corrupt Activities Act",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        },
        # Sweden Templates
        {
            "template_name": "Sweden Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "Sweden",
            "country_code": "SE",
            "company_name": "Meril Nordic AB",
            "relationship_company": "Meril Nordic AB",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Medtech Europe-Code of ethical business practices",
                "Swedish Criminal Code",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        },
        # UK Templates
        {
            "template_name": "UK Employee Declaration",
            "template_type": "Employee Declaration",
            "country": "United Kingdom",
            "country_code": "GB",
            "company_name": "Meril UK Limited",
            "relationship_company": "Meril UK Limited",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "Medtech Europe-Code of ethical business practices",
                "UK Bribery Act 2010",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        },
        # Default Template
        {
            "template_name": "Default Employee Declaration",
            "template_type": "Employee Declaration",
            "country": None,
            "country_code": None,
            "company_name": "Meril Life Sciences Pvt. Ltd.",
            "relationship_company": "Meril Life Sciences Pvt. Ltd.",
            "priority": 50,
            "is_active": 1,
            "is_default": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form International",
            "bullets": [
                "Anti Bribery and Anti Corruption Policy",
                "Export Controls and Trade Sanctions Policy",
                "HCP & HCO Compliance framework",
                "FCPA (Foreign Corrupt Practices Act)",
                "Prevention of Money Laundering"
            ]
        },
        # ROW Templates (Rest of World)
        {
            "template_name": "ROW Employee Declaration",
            "template_type": "Employee Declaration",
            "country": None,
            "country_code": None,
            "company_name": "Meril Life Sciences Pvt. Ltd.",
            "relationship_company": "Meril Life Sciences Pvt. Ltd.",
            "priority": 60,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Declaration Form",
            "course_filter": '{"include": ["row1", "row2"]}',
            "bullets": []
        },
        # Employee Completion Certificate Templates
        {
            "template_name": "Employee Completion Certificate",
            "template_type": "Employee Certificate",
            "country": "India",
            "country_code": "IN",
            "company_name": "Meril Life Sciences Pvt. Ltd.",
            "relationship_company": "Meril Life Sciences Pvt. Ltd.",
            "priority": 100,
            "is_active": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "Employee Completion Certificate",
            "bullets": []
        },
        {
            "template_name": "International Completion Certificate",
            "template_type": "Employee Certificate",
            "country": None,
            "country_code": None,
            "company_name": "Meril Life Sciences Pvt. Ltd.",
            "relationship_company": "Meril Life Sciences Pvt. Ltd.",
            "priority": 50,
            "is_active": 1,
            "is_default": 1,
            "effective_from": "2024-01-01",
            "template_version": "1.0.0",
            "print_format": "International Completion Certificate",
            "bullets": []
        }
    ]

    # Counter for migrated templates
    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for config in template_configs:
        try:
            # Extract bullets for later insertion
            bullets = config.pop("bullets", [])

            # Check if template already exists
            existing = frappe.db.exists("Document Template Registry", {
                "template_name": config["template_name"]
            })

            if existing:
                print(f"Template '{config['template_name']}' already exists, skipping...")
                skipped_count += 1
                continue

            # Check if the country exists (if specified)
            if config.get("country"):
                if not frappe.db.exists("Country", config["country"]):
                    print(f"Country '{config['country']}' does not exist, creating...")
                    country_doc = frappe.new_doc("Country")
                    country_doc.country_name = config["country"]
                    country_doc.code = config.get("country_code", "")
                    country_doc.insert(ignore_permissions=True)

            # Check if print format exists
            if not frappe.db.exists("Print Format", config["print_format"]):
                print(f"Warning: Print Format '{config['print_format']}' does not exist")
                # You may want to create a placeholder or use a default print format
                config["print_format"] = frappe.db.get_value("Print Format", {"doc_type": "Employee Course Documents"}, "name") or "Standard"

            # Create the template
            template = frappe.new_doc("Document Template Registry")
            template.update(config)

            # Add compliance bullets
            for idx, bullet_text in enumerate(bullets):
                template.append("template_compliance_bullets", {
                    "bullet_text": bullet_text,
                    "display_order": idx + 1,
                    "is_mandatory": 1,
                    "applies_to_role": "Employee"
                })

            template.insert(ignore_permissions=True)
            print(f"Successfully migrated template: {template.template_name}")
            migrated_count += 1

            # Create country mapping if country is specified
            if config.get("country") and config["template_type"] in ["Employee Declaration", "Employee Certificate"]:
                mapping_exists = frappe.db.exists("Country Template Mapping", {
                    "country": config["country"],
                    "template_type": config["template_type"]
                })

                if not mapping_exists:
                    mapping = frappe.new_doc("Country Template Mapping")
                    mapping.country = config["country"]
                    mapping.country_code = config.get("country_code", "")
                    mapping.template_type = config["template_type"]
                    mapping.primary_template = template.name
                    mapping.priority = config.get("priority", 0)
                    mapping.is_active = 1
                    mapping.effective_from = config["effective_from"]
                    mapping.insert(ignore_permissions=True)
                    print(f"Created country mapping for {config['country']} -> {template.name}")

        except Exception as e:
            print(f"Error migrating template '{config.get('template_name', 'Unknown')}': {str(e)}")
            error_count += 1
            frappe.log_error(f"Template migration error: {str(e)}", "Migrate Templates")

    # Commit changes
    frappe.db.commit()

    # Print summary
    print(f"\n=== Migration Summary ===")
    print(f"Successfully migrated: {migrated_count} templates")
    print(f"Skipped (already exist): {skipped_count} templates")
    print(f"Errors: {error_count} templates")
    print(f"Total processed: {len(template_configs)} templates")

    return f"Migration completed: {migrated_count} migrated, {skipped_count} skipped, {error_count} errors"