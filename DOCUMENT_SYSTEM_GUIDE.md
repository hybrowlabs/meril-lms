# Enhanced Document Generation System Guide

## Overview
The enhanced document generation system automatically selects the correct print formats and content based on employee country and course type. No user selection is required.

## How Country-Based Declaration Form Selection Works

### Automatic Selection Logic
When an employee generates documents, the system:

1. **Reads Employee Country**: Gets country from `employee.custom_country` or `employee.country`
2. **Normalizes Country Name**: Converts to lowercase, removes spaces and special characters
3. **Maps to Region**: Assigns employee to one of these regions:
   - `default` (India and unknown countries)
   - `germany`, `italy`, `poland`, `spain`, `brazil`, `turkey`, `south_africa`, `sweden`, `uk`
   - `row1_2` (for ROW1/ROW2 courses regardless of country)

### Print Format Selection
- **India/Unknown Countries**: Uses `Employee Declaration Form` (domestic version)
- **All Other Countries**: Uses `Employee Declaration Form International`
- **ROW1/ROW2 Courses**: Always uses `Employee Declaration Form International`

### Certificate Selection
- **India**: Uses `Employee Completion Certificate` (domestic version)
- **ROW1/ROW2 Courses**: Uses `Employee Completion Certificate` (domestic version)
- **All Other Countries**: Uses `International Completion Certificate` (Nordic design)

## Bullet Points System

### How Template-Based Bullets Work

#### 1. **Automatic Template Selection**
```python
# System calls this function automatically
template = frappe.call("lms.overrides.documents.get_employee_declaration_template",
                      employee_doc=employee,
                      course_name=doc.course,
                      course_title=course_title)
```

#### 2. **Region-Specific Content**
Each region has customized content:

**Default (India)**:
- Company: Uses employee's company name
- Relationship Company: "Meril Life Sciences Pvt. Ltd."
- Bullets: 5 standard compliance points

**Germany**:
- Company: "Meril GmbH"
- Relationship Company: "Meril GmbH"
- Bullets: 4 Germany-specific compliance points

**Italy**:
- Company: "Meril Italia S.r.l."
- Relationship Company: "Meril Italia S.r.l."
- Bullets: 4 Italy-specific compliance points

**And so on for each region...**

#### 3. **Template Data Structure**
```python
template_info = {
    "region": "germany",
    "display_name": "Employee Declaration Form International - Germany",
    "print_format": "Employee Declaration Form International",
    "country": "Germany",
    "company": "Meril GmbH",
    "relationship_company": "Meril GmbH",
    "bullets": [
        "Anti-Corruption and Bribery Code of Conduct specific to German regulations",
        "Healthcare Professional Interaction Guidelines under German law",
        "Data Protection and Privacy Code compliant with GDPR",
        "Competitive Practices and Antitrust Guidelines for German market"
    ],
    "auto_selected": True,
    "timestamp": "2025-10-23 18:30:00"
}
```

#### 4. **Bullet Points in Print Format**
The print format uses this template data:
```html
{% set bullets = template['bullets'] %}
<ol>
{% for point in bullets %}
  <li>{{ point }}</li>
{% endfor %}
</ol>
```

### Step-by-Step Process

#### Step 1: Employee Document Generation Request
- Employee clicks "Generate Declaration" or "Generate Certificate"
- System captures: employee record, course information

#### Step 2: Automatic Region Detection
```
Employee Country: "Germany"
↓
Normalized: "germany"
↓
Region Mapping: "germany"
↓
Template Selection: Germany-specific content
```

#### Step 3: Template Assembly
- **Company Name**: "Meril GmbH"
- **Relationship Company**: "Meril GmbH"
- **Bullet Points**: 4 Germany-specific compliance bullets
- **Print Format**: "Employee Declaration Form International"

#### Step 4: Document Generation
- Print format renders with Germany-specific content
- Bullet points automatically populate from template
- Company names appear correctly throughout document

#### Step 5: Automatic Logging
- System logs the automatic selection for audit trail
- Records: employee, region, template used, timestamp

## Key Features

### ✅ **Automatic Selection**
- No user input required
- System detects country and selects appropriate content

### ✅ **Region-Specific Content**
- Each country gets customized bullet points
- Local company names used correctly
- Compliance requirements match local regulations

### ✅ **ROW1/ROW2 Special Handling**
- ROW courses override country-based selection
- Use special bullet points for ROW regulations
- Always use international declaration format

### ✅ **Backward Compatibility**
- Works with existing employee records
- Graceful fallback for missing country data
- Maintains existing document workflow

### ✅ **Comprehensive Logging**
- Tracks all automatic selections
- Audit trail for compliance
- Debugging information available

## Examples

### Example 1: German Employee
```
Input: Employee from Germany taking "Ethics & Compliance Training"
Output:
- Declaration: "Employee Declaration Form International" with German bullets
- Certificate: "International Completion Certificate" with Nordic design
- Company: "Meril GmbH"
```

### Example 2: Indian Employee
```
Input: Employee from India taking "Ethics & Compliance Training"
Output:
- Declaration: "Employee Declaration Form" with standard bullets
- Certificate: "Employee Completion Certificate" with standard design
- Company: Employee's actual company
```

### Example 3: Brazilian Employee with ROW Course
```
Input: Employee from Brazil taking "ROW1 Ethics Training"
Output:
- Declaration: "Employee Declaration Form International" with ROW bullets
- Certificate: "Employee Completion Certificate" (ROW uses domestic certificate)
- Company: Based on ROW region settings
```

## Technical Implementation

### Files Modified
- `lms/overrides/documents.py`: Enhanced automatic selection logic
- `lms/lms/print_format/employee_declaration_form_international/`: Fixed path and integration
- `lms/lms/print_format/international_completion_certificate/`: Nordic design implementation

### API Methods
- `get_employee_declaration_template()`: Returns region-specific template data
- `get_employee_completion_certificate_name()`: Returns correct certificate format name

### Database Integration
- Uses existing Employee and LMS Course DocTypes
- No new database tables required
- Leverages Frappe's built-in print format system

## Conclusion

The system now automatically handles all document generation based on employee country and course type, providing:
- Correct compliance content for each region
- Appropriate company names and relationships
- Proper print format selection
- Comprehensive audit trail
- Zero user intervention required