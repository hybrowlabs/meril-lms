# System Architecture: Dynamic Document Generation System

## Agent Metadata
- **Agent**: Architecture Designer
- **Timestamp**: 2025-10-23T14:00:00Z
- **Input Document**: REQ_ANALYSIS_Dynamic_Document_Generation_2025-10-23T13:00:00Z.md
- **Next Agent**: DocType Developer
- **Status**: COMPLETED
- **Handoff Key**: DOCTYPE_DEV_Dynamic_Document_Generation_2025-10-23T14:00:00Z

## Executive Summary

This architecture document defines a comprehensive, scalable system for dynamic document generation within the Frappe/ERPNext ecosystem. The system replaces hardcoded country-specific templates with a flexible, database-driven architecture supporting unlimited geographical regions and document types while maintaining sub-second response times and ensuring compliance with regulatory requirements.

## System Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Presentation Layer                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Employee   │  │ Distributor  │  │  Compliance  │  │    Admin     │  │
│  │   Portal     │  │   Portal     │  │   Dashboard  │  │  Interface   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API Gateway Layer                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   REST API   │  │   WebSocket  │  │   GraphQL    │  │     RPC      │  │
│  │   Endpoints  │  │   Real-time  │  │   Queries    │  │   Methods    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Service Layer (Frappe)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     Template Management Service                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │    │
│  │  │   Template   │  │   Template   │  │   Template Version   │    │    │
│  │  │   Registry   │  │   Selection  │  │      Control        │    │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                   Document Generation Service                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │    │
│  │  │   Template   │  │      PDF     │  │    Document Queue    │    │    │
│  │  │    Engine    │  │   Generator  │  │      Processor       │    │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     Compliance & Workflow Service                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │    │
│  │  │   Workflow   │  │  Compliance  │  │    Notification     │    │    │
│  │  │    Engine    │  │   Validator  │  │      Service        │    │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Data Layer                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   MariaDB    │  │    Redis     │  │ File Storage │  │ Search Index │  │
│  │   Primary    │  │    Cache     │  │   (S3/NFS)   │  │(Elasticsearch)│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│   User   │──1──▶│   API    │──2──▶│ Template │──3──▶│  Cache   │
│          │      │ Gateway  │      │ Service  │      │  (Redis) │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
                                            │                 │
                                            4                 │
                                            ▼                 5
                                     ┌──────────┐            │
                                     │Database  │◀───────────┘
                                     │(MariaDB) │
                                     └──────────┘
                                            │
                                            6
                                            ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│   PDF    │◀──9──│ Document │◀──7──│ Template │
│Generator │      │  Queue   │      │  Engine  │
└──────────┘      └──────────┘      └──────────┘
     │                                      ▲
     10                                     8
     ▼                                      │
┌──────────┐                        ┌──────────┐
│  Storage │                        │Workflow  │
│   (S3)   │                        │ Engine   │
└──────────┘                        └──────────┘
```

## Database Architecture

### Core Schema Design

```sql
-- Primary Tables Structure
┌─────────────────────────────────────────────────────────────┐
│                Document Template Registry                    │
├─────────────────────────────────────────────────────────────┤
│ PK: name (varchar 140)                                       │
│ template_name (varchar 255) UNIQUE NOT NULL                 │
│ template_type (enum) NOT NULL INDEX                          │
│ country (varchar 140) FK INDEX                               │
│ country_code (varchar 10) INDEX                              │
│ course_filter (text)                                         │
│ priority (int) DEFAULT 0 INDEX                               │
│ is_active (tinyint) DEFAULT 1 INDEX                          │
│ is_default (tinyint) DEFAULT 0 INDEX                         │
│ effective_from (date) NOT NULL INDEX                         │
│ effective_to (date) INDEX                                    │
│ template_version (varchar 20) NOT NULL                       │
│ print_format (varchar 140) FK NOT NULL                       │
│ company_name (varchar 255)                                   │
│ relationship_company (varchar 255)                           │
│ metadata_json (json)                                         │
│ created_by (varchar 140) FK                                  │
│ modified_by (varchar 140) FK                                 │
│ creation (datetime) INDEX                                    │
│ modified (datetime) INDEX                                    │
├─────────────────────────────────────────────────────────────┤
│ Indexes:                                                     │
│ - idx_country_type_active (country, template_type, is_active)│
│ - idx_effective_dates (effective_from, effective_to)         │
│ - idx_priority_active (priority DESC, is_active)             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Document Generation Log                         │
├─────────────────────────────────────────────────────────────┤
│ PK: name (varchar 140) AUTO: DGL-.YYYY.-.#####              │
│ user (varchar 140) FK NOT NULL INDEX                         │
│ role_type (enum) NOT NULL INDEX                              │
│ template_used (varchar 140) FK INDEX                         │
│ template_version_used (varchar 20)                           │
│ course (varchar 140) FK INDEX                                │
│ employee (varchar 140) FK INDEX                              │
│ distributor (varchar 140) FK INDEX                           │
│ generation_type (enum) NOT NULL INDEX                        │
│ generation_status (enum) NOT NULL INDEX                      │
│ error_message (text)                                         │
│ file_reference (text)                                        │
│ generation_datetime (datetime) NOT NULL INDEX                │
│ ip_address (varchar 45)                                      │
│ user_agent (text)                                            │
│ processing_time_ms (int) INDEX                               │
│ creation (datetime)                                          │
├─────────────────────────────────────────────────────────────┤
│ Indexes:                                                     │
│ - idx_user_datetime (user, generation_datetime DESC)         │
│ - idx_status_datetime (generation_status, generation_datetime)│
│ - idx_template_used (template_used, generation_datetime)     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            Employee Course Documents (Enhanced)              │
├─────────────────────────────────────────────────────────────┤
│ PK: name (varchar 140)                                       │
│ employee (varchar 140) FK NOT NULL INDEX                     │
│ course (varchar 140) FK NOT NULL INDEX                       │
│ selected_template (varchar 140) FK                           │
│ template_version_used (varchar 20)                           │
│ document_options_json (json)                                 │
│ compliance_officer (varchar 140) FK INDEX                    │
│ compliance_review_status (enum) INDEX                        │
│ compliance_review_date (datetime) INDEX                      │
│ compliance_review_notes (text)                               │
│ workflow_state (varchar 50) INDEX                            │
│ creation (datetime) INDEX                                    │
│ modified (datetime) INDEX                                    │
├─────────────────────────────────────────────────────────────┤
│ Indexes:                                                     │
│ - idx_employee_course (employee, course) UNIQUE              │
│ - idx_compliance_status (compliance_review_status, modified)  │
│ - idx_workflow_state (workflow_state, modified)              │
└─────────────────────────────────────────────────────────────┘
```

### Relationship Model

```
Document Template Registry
    │
    ├──1:N──▶ Template Compliance Bullets (Child)
    │
    ├──1:N──▶ Document Generation Log
    │
    ├──1:N──▶ Employee Course Documents
    │
    └──1:N──▶ Country Template Mapping
                    │
                    └──1:N──▶ Course Template Exception (Child)

Employee Course Documents
    │
    ├──N:1──▶ Employee
    │
    ├──N:1──▶ LMS Course
    │
    ├──N:1──▶ Document Template Registry
    │
    └──1:N──▶ Generated Document Items (Child)
```

### Database Optimization Strategy

```sql
-- Partitioning Strategy for High-Volume Tables
ALTER TABLE `tabDocument Generation Log`
PARTITION BY RANGE (YEAR(generation_datetime)) (
    PARTITION p_2024 VALUES LESS THAN (2025),
    PARTITION p_2025 VALUES LESS THAN (2026),
    PARTITION p_2026 VALUES LESS THAN (2027),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- Materialized Views for Analytics
CREATE VIEW v_template_usage_stats AS
SELECT
    template_used,
    COUNT(*) as usage_count,
    AVG(processing_time_ms) as avg_processing_time,
    DATE(generation_datetime) as generation_date
FROM `tabDocument Generation Log`
WHERE generation_status = 'Success'
GROUP BY template_used, DATE(generation_datetime);

-- Function-based Indexes
CREATE INDEX idx_country_upper ON `tabDocument Template Registry`
    ((UPPER(country)));

CREATE INDEX idx_template_active_default ON `tabDocument Template Registry`
    (is_active, is_default, priority DESC);
```

## API Architecture

### RESTful API Design

```yaml
# Template Management APIs
/api/v1/templates:
  GET:
    description: List all templates with filtering
    parameters:
      - country: string (optional)
      - template_type: enum (optional)
      - is_active: boolean (default: true)
      - page: integer (default: 1)
      - limit: integer (default: 20, max: 100)
    response:
      200:
        schema:
          templates: array[Template]
          pagination: PaginationMeta
    rate_limit: 100/minute

  POST:
    description: Create new template
    required_role: [Template Administrator]
    body:
      template: TemplateCreateSchema
    response:
      201:
        schema:
          template: Template
          location: string

/api/v1/templates/{template_id}:
  GET:
    description: Get specific template details
    response:
      200:
        schema: Template
      404:
        schema: ErrorResponse

  PUT:
    description: Update template
    required_role: [Template Administrator]
    body:
      template: TemplateUpdateSchema
    response:
      200:
        schema: Template

  DELETE:
    description: Soft delete template
    required_role: [System Manager]
    response:
      204: No Content

# Document Generation APIs
/api/v1/documents/generate:
  POST:
    description: Generate documents
    authentication: required
    body:
      user_type: enum[employee, distributor]
      user_id: string
      course: string
      templates: array[string]
      options: GenerationOptions
    response:
      202:
        schema:
          job_id: string
          status_url: string
          estimated_time_seconds: integer
    rate_limit: 50/minute/user

/api/v1/documents/preview:
  POST:
    description: Preview document without saving
    body:
      template_id: string
      context: PreviewContext
    response:
      200:
        schema:
          preview_url: string
          expires_in: integer
    rate_limit: 100/minute/user

/api/v1/documents/bulk:
  POST:
    description: Bulk document generation
    required_role: [HR Manager, System Manager]
    body:
      filter_criteria: FilterCriteria
      templates: array[string]
      async: boolean (default: true)
    response:
      202:
        schema:
          batch_id: string
          estimated_documents: integer
          status_url: string

# Compliance APIs
/api/v1/compliance/review:
  GET:
    description: Get pending reviews
    required_role: [Compliance Officer]
    parameters:
      - status: enum (optional)
      - country: string (optional)
      - priority: enum (optional)
    response:
      200:
        schema:
          reviews: array[ComplianceReview]
          total_pending: integer

  POST:
    description: Submit compliance decision
    required_role: [Compliance Officer]
    body:
      document_id: string
      decision: enum[approved, rejected]
      notes: string
    response:
      200:
        schema:
          review: ComplianceReview
          workflow_state: string

# WebSocket Events
/ws/v1/documents:
  events:
    - document.generation.started
    - document.generation.progress
    - document.generation.completed
    - document.generation.failed
    - template.updated
    - compliance.review.required
```

### API Gateway Configuration

```nginx
# Nginx API Gateway Configuration
upstream frappe_backend {
    least_conn;
    server backend1.local:8000 weight=5;
    server backend2.local:8000 weight=5;
    server backend3.local:8000 weight=5;
    keepalive 32;
}

# Rate Limiting Zones
limit_req_zone $binary_remote_addr zone=api_general:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=api_generation:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api_bulk:10m rate=1r/s;

server {
    listen 443 ssl http2;
    server_name api.documentgen.example.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/api.crt;
    ssl_certificate_key /etc/ssl/private/api.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # API Endpoints
    location /api/v1/templates {
        limit_req zone=api_general burst=20 nodelay;
        proxy_pass http://frappe_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache api_cache;
        proxy_cache_valid 200 1m;
    }

    location /api/v1/documents/generate {
        limit_req zone=api_generation burst=5 nodelay;
        proxy_pass http://frappe_backend;
        proxy_read_timeout 300s;
    }

    location /api/v1/documents/bulk {
        limit_req zone=api_bulk burst=2;
        proxy_pass http://frappe_backend;
        proxy_read_timeout 900s;
    }

    # WebSocket Support
    location /ws/ {
        proxy_pass http://frappe_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
}
```

## Service Layer Architecture

### Template Management Service

```python
# template_management_service.py
class TemplateManagementService:
    """
    Core service for managing document templates
    """

    def __init__(self):
        self.cache = RedisCache()
        self.db = frappe.db
        self.validator = TemplateValidator()

    def get_applicable_templates(
        self,
        user_type: str,
        user_id: str,
        course: str,
        country: str = None
    ) -> List[Template]:
        """
        Intelligent template selection based on context
        """
        cache_key = f"templates:{user_type}:{user_id}:{course}:{country}"

        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # Build query
        query = """
            SELECT
                dtr.*,
                ctm.priority as mapping_priority
            FROM `tabDocument Template Registry` dtr
            LEFT JOIN `tabCountry Template Mapping` ctm
                ON dtr.name = ctm.primary_template
            WHERE
                dtr.is_active = 1
                AND dtr.effective_from <= CURDATE()
                AND (dtr.effective_to IS NULL OR dtr.effective_to >= CURDATE())
                AND (
                    dtr.country = %(country)s
                    OR dtr.is_default = 1
                    OR ctm.country = %(country)s
                )
                AND dtr.template_type LIKE %(type_pattern)s
            ORDER BY
                CASE WHEN dtr.country = %(country)s THEN 0 ELSE 1 END,
                dtr.priority DESC,
                ctm.priority DESC
        """

        templates = self.db.sql(query, {
            'country': country or self._get_user_country(user_type, user_id),
            'type_pattern': f"{user_type}%"
        }, as_dict=1)

        # Apply course filters
        templates = self._apply_course_filters(templates, course)

        # Cache for 1 hour
        self.cache.setex(cache_key, 3600, templates)

        return templates

    def _apply_course_filters(
        self,
        templates: List[dict],
        course: str
    ) -> List[dict]:
        """
        Apply course-specific filtering logic
        """
        filtered = []
        for template in templates:
            if template.get('course_filter'):
                try:
                    filter_config = json.loads(template['course_filter'])
                    if self._matches_course_filter(course, filter_config):
                        filtered.append(template)
                except json.JSONDecodeError:
                    # Invalid filter, skip template
                    continue
            else:
                # No filter means template applies to all courses
                filtered.append(template)

        return filtered

    def create_template_version(
        self,
        template_id: str,
        changes: dict
    ) -> str:
        """
        Create new version of template while preserving history
        """
        current = frappe.get_doc("Document Template Registry", template_id)

        # Archive current version
        archive_doc = frappe.new_doc("Template Version Archive")
        archive_doc.update({
            'original_template': template_id,
            'version': current.template_version,
            'archived_data': current.as_json(),
            'archived_by': frappe.session.user,
            'archived_on': now()
        })
        archive_doc.insert()

        # Update template with new version
        new_version = self._increment_version(current.template_version)
        current.update(changes)
        current.template_version = new_version
        current.save()

        # Clear related caches
        self.cache.delete_pattern(f"templates:*:{template_id}:*")

        return new_version
```

### Document Generation Service

```python
# document_generation_service.py
class DocumentGenerationService:
    """
    Handles document generation pipeline
    """

    def __init__(self):
        self.template_engine = JinjaTemplateEngine()
        self.pdf_generator = PDFGenerator()
        self.queue = DocumentQueue()
        self.storage = StorageService()

    async def generate_documents(
        self,
        request: GenerationRequest
    ) -> GenerationResponse:
        """
        Main document generation pipeline
        """
        # Start generation log
        log_id = self._start_generation_log(request)

        try:
            # Fetch templates
            templates = await self._fetch_templates(request.template_ids)

            # Prepare context
            context = await self._prepare_context(request)

            # Generate documents
            documents = []
            for template in templates:
                # Render template
                rendered = await self.template_engine.render(
                    template,
                    context
                )

                # Generate PDF
                pdf_data = await self.pdf_generator.generate(
                    rendered,
                    template.print_format
                )

                # Store document
                file_url = await self.storage.store(
                    pdf_data,
                    self._generate_filename(template, request)
                )

                documents.append({
                    'template_id': template.name,
                    'document_type': template.template_type,
                    'file_url': file_url,
                    'file_size': len(pdf_data),
                    'generated_at': now()
                })

                # Update generation log
                self._update_generation_progress(log_id, template.name)

            # Complete log
            self._complete_generation_log(log_id, documents)

            return GenerationResponse(
                success=True,
                documents=documents,
                generation_log_id=log_id
            )

        except Exception as e:
            self._fail_generation_log(log_id, str(e))
            raise

    async def generate_bulk(
        self,
        criteria: BulkCriteria
    ) -> str:
        """
        Queue bulk document generation
        """
        # Create batch job
        batch_id = self.queue.create_batch({
            'criteria': criteria,
            'created_by': frappe.session.user,
            'status': 'pending'
        })

        # Get affected users
        users = self._get_bulk_users(criteria)

        # Queue individual jobs
        for user in users:
            self.queue.enqueue(
                'generate_user_documents',
                user_id=user['id'],
                user_type=user['type'],
                templates=criteria.templates,
                batch_id=batch_id,
                priority='low'
            )

        return batch_id

    def _prepare_context(self, request: GenerationRequest) -> dict:
        """
        Prepare template context with all required data
        """
        context = {
            'user': self._get_user_data(request.user_type, request.user_id),
            'course': self._get_course_data(request.course),
            'company': self._get_company_data(),
            'generated_date': format_date(today()),
            'generated_time': format_time(now()),
        }

        # Add custom fields from options
        if request.options and request.options.custom_fields:
            context.update(request.options.custom_fields)

        # Add computed fields
        context.update(self._compute_dynamic_fields(context))

        return context
```

### Compliance & Workflow Service

```python
# compliance_workflow_service.py
class ComplianceWorkflowService:
    """
    Manages compliance reviews and workflow transitions
    """

    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.notification_service = NotificationService()
        self.validator = ComplianceValidator()

    def process_workflow_transition(
        self,
        document_id: str,
        action: str,
        user: str = None
    ) -> WorkflowResponse:
        """
        Handle workflow state transitions
        """
        doc = frappe.get_doc("Employee Course Documents", document_id)
        current_state = doc.workflow_state

        # Validate transition
        if not self.workflow_engine.can_transition(
            current_state,
            action,
            user or frappe.session.user
        ):
            raise WorkflowError(f"Invalid transition: {current_state} -> {action}")

        # Execute transition
        new_state = self.workflow_engine.execute_transition(
            doc,
            action
        )

        # Handle state-specific actions
        self._handle_state_actions(doc, new_state)

        # Send notifications
        self._send_workflow_notifications(doc, current_state, new_state)

        return WorkflowResponse(
            success=True,
            previous_state=current_state,
            current_state=new_state,
            available_actions=self.workflow_engine.get_available_actions(new_state)
        )

    def _handle_state_actions(self, doc, state: str):
        """
        Execute state-specific business logic
        """
        state_handlers = {
            'Compliance Review': self._initiate_compliance_review,
            'Document Generation': self._trigger_document_generation,
            'Completed': self._archive_documents,
            'Rejected': self._handle_rejection
        }

        handler = state_handlers.get(state)
        if handler:
            handler(doc)

    def _initiate_compliance_review(self, doc):
        """
        Start compliance review process
        """
        # Assign compliance officer
        officer = self._assign_compliance_officer(doc)
        doc.compliance_officer = officer
        doc.compliance_review_status = 'Pending'
        doc.save()

        # Create review task
        task = frappe.new_doc("Compliance Review Task")
        task.update({
            'document': doc.name,
            'assigned_to': officer,
            'priority': self._calculate_priority(doc),
            'due_date': add_days(today(), 2)
        })
        task.insert()

        # Send notification
        self.notification_service.send(
            recipient=officer,
            subject="New Compliance Review Required",
            template="compliance_review_assignment",
            context={'document': doc, 'task': task}
        )
```

## Template Engine Architecture

### Template Processing Pipeline

```python
# template_engine.py
class JinjaTemplateEngine:
    """
    Jinja2-based template engine with Frappe integration
    """

    def __init__(self):
        self.env = self._create_jinja_environment()
        self.cache = TemplateCache()
        self.validator = TemplateValidator()

    def _create_jinja_environment(self) -> Environment:
        """
        Configure Jinja2 environment with custom filters
        """
        loader = DatabaseTemplateLoader()
        env = Environment(
            loader=loader,
            autoescape=True,
            cache_size=1000,
            extensions=['jinja2.ext.do', 'jinja2.ext.loopcontrols']
        )

        # Add custom filters
        env.filters.update({
            'format_date': format_date,
            'format_currency': format_currency,
            'translate': self._translate,
            'qrcode': self._generate_qrcode,
            'barcode': self._generate_barcode
        })

        # Add custom functions
        env.globals.update({
            'get_field_value': self._get_field_value,
            'include_image': self._include_image,
            'get_company_logo': self._get_company_logo
        })

        return env

    async def render(
        self,
        template: Template,
        context: dict
    ) -> str:
        """
        Render template with context
        """
        # Get compiled template
        compiled = self._get_compiled_template(template)

        # Validate context
        self.validator.validate_context(template, context)

        # Add system context
        context.update(self._get_system_context())

        # Render
        try:
            rendered = await self._async_render(compiled, context)
        except TemplateError as e:
            self._log_template_error(template, e)
            raise

        # Post-process
        rendered = self._post_process(rendered, template)

        return rendered

    def _get_compiled_template(self, template: Template):
        """
        Get compiled template with caching
        """
        cache_key = f"compiled:{template.name}:{template.template_version}"

        compiled = self.cache.get(cache_key)
        if not compiled:
            # Load template source
            source = self._load_template_source(template)

            # Compile
            compiled = self.env.compile_expression(source)

            # Cache compiled template
            self.cache.set(cache_key, compiled, ttl=3600)

        return compiled

class DatabaseTemplateLoader(BaseLoader):
    """
    Load Jinja2 templates from database
    """

    def get_source(self, environment, template):
        """
        Fetch template source from database
        """
        doc = frappe.get_doc("Document Template Registry", template)

        if not doc:
            raise TemplateNotFound(template)

        # Get template content from print format
        print_format = frappe.get_doc("Print Format", doc.print_format)
        source = print_format.html

        # Check if template was modified
        mtime = doc.modified.timestamp()

        def uptodate():
            try:
                current = frappe.get_value(
                    "Document Template Registry",
                    template,
                    "modified"
                )
                return current.timestamp() == mtime
            except:
                return False

        return source, None, uptodate
```

### PDF Generation Architecture

```python
# pdf_generator.py
class PDFGenerator:
    """
    High-performance PDF generation service
    """

    def __init__(self):
        self.engine = self._select_engine()
        self.optimizer = PDFOptimizer()
        self.pool = ProcessPoolExecutor(max_workers=4)

    def _select_engine(self):
        """
        Select PDF generation engine based on configuration
        """
        engine_type = frappe.conf.get('pdf_engine', 'weasyprint')

        engines = {
            'weasyprint': WeasyPrintEngine,
            'wkhtmltopdf': WkHtmlToPdfEngine,
            'puppeteer': PuppeteerEngine,
            'reportlab': ReportLabEngine
        }

        return engines[engine_type]()

    async def generate(
        self,
        html: str,
        print_format: str,
        options: dict = None
    ) -> bytes:
        """
        Generate PDF from HTML
        """
        # Prepare HTML
        html = self._prepare_html(html, print_format)

        # Generate PDF in process pool
        future = self.pool.submit(
            self._generate_pdf_sync,
            html,
            options or {}
        )

        # Wait for result with timeout
        try:
            pdf_data = await asyncio.wait_for(
                asyncio.wrap_future(future),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise PDFGenerationTimeout()

        # Optimize PDF
        pdf_data = self.optimizer.optimize(pdf_data)

        return pdf_data

    def _generate_pdf_sync(self, html: str, options: dict) -> bytes:
        """
        Synchronous PDF generation
        """
        return self.engine.generate(html, options)

class WeasyPrintEngine:
    """
    WeasyPrint PDF generation engine
    """

    def generate(self, html: str, options: dict) -> bytes:
        """
        Generate PDF using WeasyPrint
        """
        from weasyprint import HTML, CSS

        # Parse HTML
        doc = HTML(string=html, base_url=frappe.utils.get_url())

        # Add custom CSS
        css = CSS(string=self._get_custom_css(options))

        # Generate PDF
        pdf = doc.write_pdf(
            stylesheets=[css],
            pdf_version='1.7',
            optimize_size=('fonts', 'images'),
            jpeg_quality=85,
            dpi=96
        )

        return pdf

    def _get_custom_css(self, options: dict) -> str:
        """
        Build custom CSS for PDF generation
        """
        css_parts = [
            # Base styles
            """
            @page {
                size: A4;
                margin: 2cm;
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                }
            }
            body {
                font-family: -apple-system, sans-serif;
                font-size: 10pt;
                line-height: 1.5;
            }
            """
        ]

        # Add watermark if requested
        if options.get('watermark'):
            css_parts.append("""
                body::before {
                    content: "DRAFT";
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%) rotate(-45deg);
                    font-size: 100pt;
                    opacity: 0.1;
                    z-index: -1;
                }
            """)

        return '\n'.join(css_parts)
```

## Caching Strategy

### Multi-Layer Cache Architecture

```python
# cache_manager.py
class CacheManager:
    """
    Hierarchical caching system
    """

    def __init__(self):
        self.l1_cache = LocalMemoryCache(max_size=1000)  # In-process
        self.l2_cache = RedisCache()  # Shared Redis
        self.l3_cache = CDNCache()  # CDN for static content

    async def get(self, key: str, loader=None):
        """
        Multi-level cache lookup
        """
        # L1: Local memory
        value = self.l1_cache.get(key)
        if value:
            return value

        # L2: Redis
        value = await self.l2_cache.get(key)
        if value:
            self.l1_cache.set(key, value, ttl=60)
            return value

        # L3: CDN (for static content)
        if key.startswith('static:'):
            value = await self.l3_cache.get(key)
            if value:
                await self.l2_cache.set(key, value, ttl=3600)
                self.l1_cache.set(key, value, ttl=60)
                return value

        # Load from source
        if loader:
            value = await loader()
            await self.set(key, value)
            return value

        return None

    async def set(self, key: str, value, ttl: int = 3600):
        """
        Set value in all cache levels
        """
        # Determine cache levels based on key pattern
        if key.startswith('static:'):
            # Static content: all levels
            self.l1_cache.set(key, value, ttl=60)
            await self.l2_cache.set(key, value, ttl=ttl)
            await self.l3_cache.set(key, value, ttl=86400)
        elif key.startswith('template:'):
            # Templates: L1 and L2
            self.l1_cache.set(key, value, ttl=60)
            await self.l2_cache.set(key, value, ttl=ttl)
        else:
            # Dynamic content: L1 only
            self.l1_cache.set(key, value, ttl=ttl)

    def invalidate(self, pattern: str):
        """
        Invalidate cache entries matching pattern
        """
        self.l1_cache.clear_pattern(pattern)
        self.l2_cache.delete_pattern(pattern)
        # CDN invalidation is expensive, do selectively
        if pattern.startswith('static:'):
            self.l3_cache.invalidate(pattern)

# Redis Cache Configuration
class RedisCache:
    """
    Redis cache implementation
    """

    def __init__(self):
        self.pool = redis.ConnectionPool(
            host=frappe.conf.redis_cache_host or 'localhost',
            port=frappe.conf.redis_cache_port or 6379,
            db=frappe.conf.redis_cache_db or 1,
            max_connections=50,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)
        self.pipeline = self.client.pipeline()

    async def get(self, key: str):
        """
        Get value from Redis
        """
        try:
            value = await self.client.get(f"docgen:{key}")
            if value:
                return json.loads(value)
        except redis.RedisError as e:
            frappe.logger().error(f"Redis get error: {e}")
        return None

    async def set(self, key: str, value, ttl: int = 3600):
        """
        Set value in Redis with TTL
        """
        try:
            await self.client.setex(
                f"docgen:{key}",
                ttl,
                json.dumps(value)
            )
        except redis.RedisError as e:
            frappe.logger().error(f"Redis set error: {e}")
```

## Performance Optimization

### Async Processing Architecture

```python
# async_processor.py
class AsyncDocumentProcessor:
    """
    Asynchronous document processing with RQ
    """

    def __init__(self):
        self.high_queue = rq.Queue('high', connection=redis_conn)
        self.default_queue = rq.Queue('default', connection=redis_conn)
        self.low_queue = rq.Queue('low', connection=redis_conn)
        self.scheduler = Scheduler(connection=redis_conn)

    def enqueue_generation(
        self,
        request: GenerationRequest,
        priority: str = 'default'
    ) -> str:
        """
        Queue document generation job
        """
        queues = {
            'high': self.high_queue,
            'default': self.default_queue,
            'low': self.low_queue
        }

        queue = queues.get(priority, self.default_queue)

        job = queue.enqueue(
            'lms.document_generation.tasks.generate_documents',
            request=request,
            job_timeout='5m',
            result_ttl=3600,
            failure_ttl=86400,
            meta={
                'user': frappe.session.user,
                'request_time': now(),
                'priority': priority
            }
        )

        # Store job mapping
        frappe.cache().hset(
            'generation_jobs',
            request.user_id,
            job.id
        )

        return job.id

    def schedule_bulk_generation(
        self,
        criteria: BulkCriteria,
        scheduled_time: datetime
    ) -> str:
        """
        Schedule bulk generation for later
        """
        job = self.scheduler.schedule(
            scheduled_time=scheduled_time,
            func='lms.document_generation.tasks.bulk_generate',
            args=[criteria],
            job_timeout='30m',
            queue_name='low'
        )

        return job.id

# Worker Configuration
"""
# supervisord.conf
[program:docgen-worker-high]
command=/usr/local/bin/rq worker high --url redis://localhost:6379/0
process_name=%(program_name)s_%(process_num)02d
numprocs=2
directory=/home/frappe/frappe-bench
user=frappe
autostart=true
autorestart=true
stdout_logfile=/var/log/docgen/worker-high.log
stderr_logfile=/var/log/docgen/worker-high-error.log

[program:docgen-worker-default]
command=/usr/local/bin/rq worker default --url redis://localhost:6379/0
process_name=%(program_name)s_%(process_num)02d
numprocs=4
directory=/home/frappe/frappe-bench
user=frappe
autostart=true
autorestart=true

[program:docgen-worker-low]
command=/usr/local/bin/rq worker low --url redis://localhost:6379/0
process_name=%(program_name)s_%(process_num)02d
numprocs=2
directory=/home/frappe/frappe-bench
user=frappe
autostart=true
autorestart=true
"""
```

### Database Query Optimization

```python
# query_optimizer.py
class QueryOptimizer:
    """
    Database query optimization strategies
    """

    @staticmethod
    def get_templates_optimized(filters: dict) -> list:
        """
        Optimized template query with eager loading
        """
        query = """
            SELECT
                dtr.name,
                dtr.template_name,
                dtr.template_type,
                dtr.country,
                dtr.priority,
                dtr.template_version,
                dtr.is_active,
                dtr.is_default,
                pf.html as template_content,
                GROUP_CONCAT(
                    DISTINCT tcb.bullet_text
                    ORDER BY tcb.display_order
                    SEPARATOR '|||'
                ) as compliance_bullets
            FROM `tabDocument Template Registry` dtr
            INNER JOIN `tabPrint Format` pf
                ON dtr.print_format = pf.name
            LEFT JOIN `tabTemplate Compliance Bullets` tcb
                ON tcb.parent = dtr.name
            WHERE
                dtr.is_active = 1
                AND dtr.effective_from <= CURDATE()
                AND (dtr.effective_to IS NULL OR dtr.effective_to >= CURDATE())
                {where_clause}
            GROUP BY dtr.name
            ORDER BY
                dtr.priority DESC,
                dtr.template_name
        """

        # Build where clause
        where_parts = []
        params = {}

        if filters.get('country'):
            where_parts.append("AND (dtr.country = %(country)s OR dtr.is_default = 1)")
            params['country'] = filters['country']

        if filters.get('template_type'):
            where_parts.append("AND dtr.template_type = %(template_type)s")
            params['template_type'] = filters['template_type']

        where_clause = ' '.join(where_parts)

        return frappe.db.sql(
            query.format(where_clause=where_clause),
            params,
            as_dict=1
        )

    @staticmethod
    def batch_insert_logs(logs: List[dict]):
        """
        Batch insert generation logs
        """
        if not logs:
            return

        values = []
        for log in logs:
            values.append((
                log['user'],
                log['role_type'],
                log['template_used'],
                log['generation_type'],
                log['generation_status'],
                log['generation_datetime'],
                log.get('processing_time_ms', 0)
            ))

        query = """
            INSERT INTO `tabDocument Generation Log`
            (name, user, role_type, template_used, generation_type,
             generation_status, generation_datetime, processing_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Generate names
        values_with_names = [
            (frappe.generate_hash(length=10),) + v
            for v in values
        ]

        frappe.db.executemany(query, values_with_names)
```

## Deployment Architecture

### Infrastructure Layout

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Application Servers
  frappe-app-1:
    image: frappe/erpnext:v14
    container_name: docgen-app-1
    environment:
      - SITE_NAME=docgen.example.com
      - DB_HOST=mariadb-primary
      - REDIS_CACHE=redis-cache:6379
      - REDIS_QUEUE=redis-queue:6379
    volumes:
      - ./apps/lms:/home/frappe/frappe-bench/apps/lms
      - ./sites:/home/frappe/frappe-bench/sites
    networks:
      - docgen-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  frappe-app-2:
    extends: frappe-app-1
    container_name: docgen-app-2

  frappe-app-3:
    extends: frappe-app-1
    container_name: docgen-app-3

  # Database Cluster
  mariadb-primary:
    image: mariadb:10.6
    container_name: docgen-db-primary
    environment:
      - MYSQL_ROOT_PASSWORD=secure_password
      - MYSQL_DATABASE=docgen
    volumes:
      - mariadb-data:/var/lib/mysql
      - ./config/mariadb.cnf:/etc/mysql/conf.d/custom.cnf
    networks:
      - docgen-network
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  mariadb-replica:
    image: mariadb:10.6
    container_name: docgen-db-replica
    environment:
      - MYSQL_ROOT_PASSWORD=secure_password
      - MYSQL_REPLICATION_MODE=slave
      - MYSQL_MASTER_HOST=mariadb-primary
    networks:
      - docgen-network

  # Redis Cluster
  redis-cache:
    image: redis:7-alpine
    container_name: docgen-redis-cache
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-cache-data:/data
    networks:
      - docgen-network

  redis-queue:
    image: redis:7-alpine
    container_name: docgen-redis-queue
    command: redis-server --appendonly yes
    volumes:
      - redis-queue-data:/data
    networks:
      - docgen-network

  # Workers
  worker-high:
    extends: frappe-app-1
    container_name: docgen-worker-high
    command: bench worker --queue high
    deploy:
      replicas: 2

  worker-default:
    extends: frappe-app-1
    container_name: docgen-worker-default
    command: bench worker --queue default
    deploy:
      replicas: 4

  worker-low:
    extends: frappe-app-1
    container_name: docgen-worker-low
    command: bench worker --queue low
    deploy:
      replicas: 2

  # Load Balancer
  nginx:
    image: nginx:alpine
    container_name: docgen-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    networks:
      - docgen-network
    depends_on:
      - frappe-app-1
      - frappe-app-2
      - frappe-app-3

  # Monitoring
  prometheus:
    image: prom/prometheus
    container_name: docgen-prometheus
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - docgen-network

  grafana:
    image: grafana/grafana
    container_name: docgen-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - docgen-network

networks:
  docgen-network:
    driver: bridge

volumes:
  mariadb-data:
  redis-cache-data:
  redis-queue-data:
  prometheus-data:
  grafana-data:
```

### Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docgen-app
  namespace: document-generation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docgen
      tier: backend
  template:
    metadata:
      labels:
        app: docgen
        tier: backend
    spec:
      containers:
      - name: frappe
        image: frappe/erpnext:v14-docgen
        ports:
        - containerPort: 8000
        env:
        - name: SITE_NAME
          value: docgen.example.com
        - name: DB_HOST
          value: mariadb-service
        - name: REDIS_CACHE
          value: redis-cache-service:6379
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /api/method/ping
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/method/ping
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: docgen-service
  namespace: document-generation
spec:
  selector:
    app: docgen
    tier: backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: docgen-hpa
  namespace: document-generation
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: docgen-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Security Architecture

### Authentication & Authorization

```python
# security/auth.py
class DocumentSecurityManager:
    """
    Security manager for document operations
    """

    def __init__(self):
        self.permission_manager = PermissionManager()
        self.encryption = EncryptionService()
        self.audit = AuditLogger()

    def check_document_access(
        self,
        user: str,
        document_id: str,
        operation: str
    ) -> bool:
        """
        Check if user has access to document
        """
        # Get document
        doc = frappe.get_doc("Employee Course Documents", document_id)

        # Check ownership
        if operation == 'read':
            if self._is_document_owner(user, doc):
                return True

        # Check role-based permissions
        user_roles = frappe.get_roles(user)

        permission_matrix = {
            'read': ['Employee', 'HR Manager', 'Compliance Officer'],
            'write': ['HR Manager', 'Compliance Officer'],
            'delete': ['System Manager'],
            'approve': ['Compliance Officer']
        }

        allowed_roles = permission_matrix.get(operation, [])

        if any(role in allowed_roles for role in user_roles):
            # Log access
            self.audit.log_access(user, document_id, operation, 'granted')
            return True

        # Log denied access
        self.audit.log_access(user, document_id, operation, 'denied')
        return False

    def encrypt_sensitive_data(self, data: dict) -> dict:
        """
        Encrypt sensitive fields
        """
        sensitive_fields = [
            'social_security_number',
            'bank_account',
            'tax_id'
        ]

        encrypted = data.copy()
        for field in sensitive_fields:
            if field in encrypted:
                encrypted[field] = self.encryption.encrypt(
                    encrypted[field]
                )

        return encrypted

class APISecurityMiddleware:
    """
    API security middleware
    """

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.token_validator = TokenValidator()
        self.ip_filter = IPFilter()

    def process_request(self, request):
        """
        Process incoming API request
        """
        # Validate API token
        if not self.token_validator.validate(request.headers.get('X-API-Key')):
            raise AuthenticationError("Invalid API key")

        # Check IP whitelist
        if not self.ip_filter.is_allowed(request.remote_addr):
            raise ForbiddenError("IP not whitelisted")

        # Apply rate limiting
        if not self.rate_limiter.check_limit(request):
            raise RateLimitError("Rate limit exceeded")

        # Add security headers
        request.security_context = {
            'authenticated': True,
            'timestamp': now(),
            'request_id': generate_request_id()
        }

        return request
```

## Monitoring & Observability

### Metrics Collection

```python
# monitoring/metrics.py
class MetricsCollector:
    """
    Prometheus metrics collection
    """

    def __init__(self):
        self.registry = CollectorRegistry()
        self.setup_metrics()

    def setup_metrics(self):
        """
        Define Prometheus metrics
        """
        # Counters
        self.generation_counter = Counter(
            'document_generation_total',
            'Total number of documents generated',
            ['template_type', 'status'],
            registry=self.registry
        )

        self.api_requests = Counter(
            'api_requests_total',
            'Total API requests',
            ['endpoint', 'method', 'status'],
            registry=self.registry
        )

        # Histograms
        self.generation_duration = Histogram(
            'document_generation_duration_seconds',
            'Document generation duration',
            ['template_type'],
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
            registry=self.registry
        )

        self.pdf_size = Histogram(
            'pdf_file_size_bytes',
            'Generated PDF file sizes',
            ['template_type'],
            buckets=(10000, 50000, 100000, 500000, 1000000),
            registry=self.registry
        )

        # Gauges
        self.queue_size = Gauge(
            'document_queue_size',
            'Current document generation queue size',
            ['priority'],
            registry=self.registry
        )

        self.active_sessions = Gauge(
            'active_user_sessions',
            'Number of active user sessions',
            registry=self.registry
        )

    def record_generation(
        self,
        template_type: str,
        status: str,
        duration: float,
        file_size: int
    ):
        """
        Record document generation metrics
        """
        self.generation_counter.labels(
            template_type=template_type,
            status=status
        ).inc()

        if status == 'success':
            self.generation_duration.labels(
                template_type=template_type
            ).observe(duration)

            self.pdf_size.labels(
                template_type=template_type
            ).observe(file_size)
```

## Handoff Instructions for DocType Developer

### Next Steps

The DocType Developer should use handoff key: **DOCTYPE_DEV_Dynamic_Document_Generation_2025-10-23T14:00:00Z**

### Implementation Priorities

1. **Phase 1: Core DocTypes**
   - Create Document Template Registry with all fields
   - Implement Template Compliance Bullets child table
   - Create Document Generation Log
   - Enhance Employee Course Documents

2. **Phase 2: Supporting DocTypes**
   - Create Country Template Mapping
   - Implement Course Template Exception
   - Create Document Template Variables
   - Build Generated Document Items

3. **Phase 3: Controllers & Hooks**
   - Implement template selection logic
   - Create document generation controllers
   - Build workflow state handlers
   - Add validation functions

4. **Phase 4: API Endpoints**
   - Implement template management APIs
   - Create document generation endpoints
   - Build compliance review APIs
   - Add bulk operation endpoints

### Technical Implementation Details

#### DocType Controller Template
```python
# document_template_registry.py
class DocumentTemplateRegistry(Document):
    def validate(self):
        self.validate_dates()
        self.validate_country()
        self.validate_template_type()
        self.set_defaults()

    def validate_dates(self):
        if self.effective_to and self.effective_to <= self.effective_from:
            frappe.throw(_("Effective To date must be after Effective From date"))

    def validate_country(self):
        if self.country and not frappe.db.exists("Country", self.country):
            frappe.throw(_("Invalid country: {0}").format(self.country))

    def validate_template_type(self):
        valid_types = [
            "Employee Declaration",
            "Employee Certificate",
            "Distributor Declaration",
            "Distributor Certificate"
        ]
        if self.template_type not in valid_types:
            frappe.throw(_("Invalid template type"))

    def set_defaults(self):
        if not self.priority:
            self.priority = 0
        if not self.template_version:
            self.template_version = "1.0.0"

    def on_update(self):
        # Clear cache on template update
        clear_template_cache(self.name)

    def on_trash(self):
        # Prevent deletion if template is in use
        if frappe.db.exists("Document Generation Log", {"template_used": self.name}):
            frappe.throw(_("Cannot delete template that has been used for document generation"))
```

#### API Method Template
```python
# api/document_generation.py
@frappe.whitelist()
def get_applicable_templates(user_type, user_id, course, country=None):
    """
    Get applicable templates for user and course
    """
    # Validate inputs
    if not user_type in ['employee', 'distributor']:
        frappe.throw(_("Invalid user type"))

    # Get user country if not provided
    if not country:
        if user_type == 'employee':
            country = frappe.db.get_value("Employee", user_id, "country")
        else:
            country = frappe.db.get_value("Distributor", user_id, "country")

    # Get templates
    service = TemplateManagementService()
    templates = service.get_applicable_templates(
        user_type=user_type,
        user_id=user_id,
        course=course,
        country=country
    )

    return {
        "templates": templates,
        "default_selection": [t.name for t in templates if t.is_default],
        "user_context": {
            "country": country,
            "course": course,
            "user_type": user_type
        }
    }
```

### Migration Script Template
```python
# patches/migrate_hardcoded_templates.py
def execute():
    """
    Migrate hardcoded templates to database
    """
    # Mapping of existing hardcoded templates
    legacy_templates = {
        'IMDRF_01_24_Br': {
            'country': 'Brazil',
            'template_type': 'Employee Declaration',
            'print_format': 'IMDRF Brazil Declaration'
        },
        # ... more templates
    }

    for template_code, config in legacy_templates.items():
        # Check if already migrated
        if frappe.db.exists("Document Template Registry", {"template_name": template_code}):
            continue

        # Create template
        doc = frappe.new_doc("Document Template Registry")
        doc.template_name = template_code
        doc.template_type = config['template_type']
        doc.country = config['country']
        doc.print_format = config['print_format']
        doc.is_active = 1
        doc.effective_from = '2024-01-01'
        doc.template_version = '1.0.0'
        doc.priority = 100  # High priority for legacy templates
        doc.insert()

    frappe.db.commit()
    print(f"Migrated {len(legacy_templates)} templates")
```

### Critical Success Factors

1. **Database Performance**: Ensure all indexes are created as specified
2. **Cache Implementation**: Redis cache must be properly configured
3. **Async Processing**: RQ workers must be running for bulk operations
4. **Security**: All API endpoints must validate permissions
5. **Monitoring**: Prometheus metrics must be exposed for monitoring
6. **Testing**: Comprehensive test coverage for all controllers
7. **Documentation**: API documentation must be complete
8. **Migration**: Zero-downtime migration strategy must be followed

---

*This architecture document provides the complete technical blueprint for implementing the dynamic document generation system. The DocType Developer should follow these specifications exactly to ensure system consistency and maintainability.*