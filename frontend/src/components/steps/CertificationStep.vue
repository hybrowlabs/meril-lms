<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h3 class="text-lg font-medium text-gray-900 mb-2">
        {{ getHeaderTitle() }}
      </h3>
      <p class="text-sm text-gray-600">
        {{ getHeaderDescription() }}
      </p>
    </div>

    <!-- Certification Form -->
    <div class="max-w-md mx-auto space-y-4">
      <!-- Name field for non-compliance forms and non-employee users -->
      <div v-if="!showDeclaration('Meril Distributor Compliance Policy Adoption Form') && userRole !== 'Employee'">
        <label for="certification-name" class="block text-sm font-medium text-gray-700 mb-1">
          Name <span class="text-red-500">*</span>
        </label>
        <TextInput
          id="certification-name"
          v-model="localName"
          type="text"
          placeholder="Enter your name"
          class="w-full"
          required
          :min-length="3"
        />
        <p v-if="nameError" class="text-sm text-red-600 mt-1">{{ nameError }}</p>
      </div>

      <div>
        <label for="certification-date" class="block text-sm font-medium text-gray-700 mb-1">
          Date
        </label>
        <input
          id="certification-date"
          v-model="localDate"
          type="datetime-local"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
          readonly
        />
      </div>

      <Button
        v-if="userRole === 'Employee'"
        theme="gray"
        variant="solid"
        class="w-full"
        @click="handleCertify"
        :disabled="!isValid"
      >
        Certify
      </Button>
    </div>

    <!-- Initial Loading State -->
    <div v-if="!documentConfiguration && !configurationError && configurationLoading" class="max-w-3xl mx-auto">
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div class="flex items-center justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <span class="ml-3 text-gray-600">Loading document configuration...</span>
        </div>
      </div>
    </div>

    <!-- Declaration Content -->
    <div v-else class="max-w-3xl mx-auto">
      <!-- Dynamic Preview Content for Multiple Documents -->
      <div v-if="!useStaticPreview && documentConfiguration" class="space-y-6">
        <!-- Show configuration loading -->
        <div v-if="configurationLoading" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <div class="flex items-center justify-center">
            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mr-3"></div>
            <span class="text-gray-600">Loading document configuration...</span>
          </div>
        </div>

        <!-- Show configuration error -->
        <div v-else-if="configurationError" class="bg-red-50 border border-red-200 rounded-lg p-6">
          <p class="text-red-600">{{ configurationError }}</p>
          <button @click="fetchDocumentConfiguration" class="mt-2 text-sm text-blue-600 hover:text-blue-800">
            Retry Loading Configuration
          </button>
        </div>

        <!-- Show previews for all document types that require declaration -->
        <template v-else>
          <div v-for="(docType, index) in getAllDocumentTypes()" :key="docType">
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-6">
              <h4 class="text-center font-semibold mb-4">{{ docType }} - Preview</h4>
              <div v-if="documentPreviews[docType]"
                   class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 overflow-auto"
                   style="max-height: 400px; min-height: 200px;"
                   v-html="getSanitizedPreview(docType)">
              </div>
              <div v-else-if="previewLoading[docType]" class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 flex items-center justify-center" style="min-height: 200px;">
                <div class="flex items-center">
                  <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mr-3"></div>
                  <span class="text-gray-600">Loading preview...</span>
                </div>
              </div>
              <div v-else-if="previewErrors[docType]" class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4" style="min-height: 200px;">
                <div class="text-center text-red-600">
                  <p>{{ previewErrors[docType] }}</p>
                  <button @click="fetchDocumentPreview(docType)" class="mt-2 text-sm text-blue-600 hover:text-blue-800">
                    Retry Loading Preview
                  </button>
                </div>
              </div>
              <div v-else class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 flex items-center justify-center" style="min-height: 200px;">
                <button @click="fetchDocumentPreview(docType)" class="text-blue-600 hover:text-blue-800">
                  Load Preview
                </button>
              </div>
              <div class="mt-2 text-xs text-gray-500 text-center">
                <span>Preview shows the actual document content as it will appear when downloaded</span>
              </div>
            </div>

            <!-- Compliance Officer Nomination Field (appears after adoption form preview) -->
            <div v-if="docType === 'Meril Distributor Compliance Policy Adoption Form' && userRole === 'Distributor'" class="compliance-officer-highlight bg-blue-50 rounded-lg p-4 mt-4">
              <label for="compliance-officer-name-dynamic" class="block text-sm font-medium text-gray-700 mb-2">
                Compliance Officer Name <span class="text-red-500">*</span>
              </label>
              <TextInput
                id="compliance-officer-name-dynamic"
                v-model="localComplianceOfficerName"
                type="text"
                placeholder="Enter compliance officer name"
                class="w-full compliance-officer-input"
                required
                :min-length="3"
              />
              <p v-if="complianceOfficerError" class="text-sm text-red-600 mt-1">{{ complianceOfficerError }}</p>
              <p class="text-xs text-gray-500 mt-1">This person will be nominated as the compliance officer for your organization.</p>
            </div>
          </div>
        </template>

        <!-- Distributor "I Certify" Button (at the bottom after all previews - Dynamic Section) -->
        <div v-if="userRole === 'Distributor'" class="max-w-md mx-auto mt-6">
          <Button
            theme="gray"
            variant="solid"
            class="w-full"
            @click="handleCertify"
            :disabled="!isValid"
          >
            I Certify
          </Button>
        </div>
      </div>

      <!-- Static Fallback for Distributor Declaration -->
      <div v-else-if="userRole === 'Distributor'" class="space-y-6">
        <!-- Policy Adoption Form Declaration -->
        <div v-if="showDeclaration('Meril Distributor Compliance Policy Adoption Form') || useStaticPreview" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 class="text-center font-semibold mb-4">
            Meril Distributor - Compliance Policy Adoption Form
          </h4>
          <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
            <p class="text-right">
              {{ currentDateTime }}
            </p>
            <p class="text-justify">
              We {{ declarationInfo?.distributor_company_name || 'Company Name' }}, being the Distributor of Meril {{ declarationInfo?.meril_company_table?.[0]?.meril_company_name || 'Company' }} do hereby certify that we have willingly adopted attached Meril Distributor Compliance Policy as our own Compliance Policy with effect from {{ currentDate }} and declare to abide by the same.
            </p>
            <p class="text-justify">
              All employees, partners, directors, proprietor of our organization are expected to observe and adhere to this Policy.
            </p>
            <p class="text-justify font-semibold underline">
              Nomination of Compliance Officer:
            </p>
            <p class="text-justify">
              {{ localComplianceOfficerName || complianceOfficerName || 'Name' }} is nominated as Compliance Officer of our organization with effect from {{ currentDate }}
            </p>
            <div class="mt-6 space-y-1">
              <p class="text-justify">Authorized representative of {{ declarationInfo?.distributor_company_name || 'Company Name' }}</p>
              <p class="text-justify">Name: {{ declarationInfo?.attendee_name || 'Name' }}</p>
              <p class="text-justify">Title: {{ declarationInfo?.designation || 'Designation' }}</p>
              <p class="text-justify">Email Id: {{ declarationInfo?.distributor_email_address || 'Email' }}</p>
              <p class="text-justify">Contact number: {{ declarationInfo?.distributor_contact_number || 'Contact' }}</p>
              <p class="text-justify">
                Sign and Seal:
              </p>
            </div>
          </div>
        </div>

        <!-- Compliance Officer Nomination Field (appears right after adoption form) -->
        <div v-if="showDeclaration('Meril Distributor Compliance Policy Adoption Form') && userRole === 'Distributor'" class="compliance-officer-highlight bg-blue-50 rounded-lg p-4">
          <label for="compliance-officer-name" class="block text-sm font-medium text-gray-700 mb-2">
            Compliance Officer Name <span class="text-red-500">*</span>
          </label>
          <TextInput
            id="compliance-officer-name"
            v-model="localComplianceOfficerName"
            type="text"
            placeholder="Enter compliance officer name"
            class="w-full compliance-officer-input"
            required
            :min-length="3"
          />
          <p v-if="complianceOfficerError" class="text-sm text-red-600 mt-1">{{ complianceOfficerError }}</p>
          <p class="text-xs text-gray-500 mt-1">This person will be nominated as the compliance officer for your organization.</p>
        </div>

        <!-- Self Declaration -->
        <div v-if="showDeclaration('Distributor Self Declaration')" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 class="text-center font-semibold mb-4">
            Distributor Self Declaration
          </h4>
          <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
            <p class="text-justify">
              This is to declare that we {{ declarationInfo?.distributor_company_name || 'Company Name' }}, have reviewed and understood the Meril Distributor Compliance Policy and will adhere to all its provisions.
            </p>
            <p class="text-justify">
              We confirm that we will:
            </p>
            <ul class="list-disc pl-6 space-y-1">
              <li>Comply with all applicable laws and regulations</li>
              <li>Maintain ethical business practices</li>
              <li>Report any violations or concerns</li>
              <li>Cooperate with compliance reviews and audits</li>
            </ul>
            <div class="mt-6 space-y-1">
              <p class="text-justify">Authorized representative of {{ declarationInfo?.distributor_company_name || 'Company Name' }}</p>
              <p class="text-justify">Name: {{ declarationInfo?.attendee_name || 'Name' }}</p>
              <p class="text-justify">Title: {{ declarationInfo?.designation || 'Designation' }}</p>
              <p class="text-justify">Date: {{ currentDate }}</p>
            </div>
          </div>
        </div>

        <!-- Code of Conduct -->
        <div v-if="showDeclaration('Meril Distributor Compliance Code of Conduct')" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 class="text-center font-semibold mb-4">
            Meril Distributor Compliance Code of Conduct
          </h4>
          <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
            <p class="text-justify">
              We {{ declarationInfo?.distributor_company_name || 'Company Name' }} acknowledge and agree to abide by the Meril Distributor Compliance Code of Conduct.
            </p>
            <p class="text-justify">
              We understand and will comply with:
            </p>
            <ol class="list-decimal pl-6 space-y-1">
              <li>Anti Bribery and Anti Corruption policies</li>
              <li>Fair business practices</li>
              <li>Confidentiality and data protection</li>
              <li>Conflict of interest policies</li>
              <li>Product quality and safety standards</li>
            </ol>
            <div class="mt-6 space-y-1">
              <p class="text-justify">Authorized representative of {{ declarationInfo?.distributor_company_name || 'Company Name' }}</p>
              <p class="text-justify">Name: {{ declarationInfo?.attendee_name || 'Name' }}</p>
              <p class="text-justify">Title: {{ declarationInfo?.designation || 'Designation' }}</p>
              <p class="text-justify">Date: {{ currentDate }}</p>
            </div>
          </div>
        </div>

        <!-- Ethical Practices Declaration -->
        <div v-if="showDeclaration('Distributor Declaration - Ethical Practices & Compliance')" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 class="text-center font-semibold mb-4">
            Distributor Declaration - Ethical Practices & Compliance
          </h4>
          <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
            <p class="text-justify">
              I hereby declare that {{ declarationInfo?.distributor_company_name || 'Company Name' }} has undergone and understood training provided on Ethical Practices and Compliance.
            </p>
            <p class="text-justify">
              We acknowledge and accept the duty to comply with:
            </p>
            <ul class="list-disc pl-6 space-y-1">
              <li>All procedural frameworks developed by Meril</li>
              <li>Ethical operation guidelines</li>
              <li>NPPA norms and trade regulations</li>
              <li>International compliance standards</li>
            </ul>
            <p class="text-justify">
              We certify that we are not currently in violation of any compliance policies.
            </p>
            <div class="mt-6 space-y-1">
              <p class="text-justify">Authorized representative of {{ declarationInfo?.distributor_company_name || 'Company Name' }}</p>
              <p class="text-justify">Name: {{ declarationInfo?.attendee_name || 'Name' }}</p>
              <p class="text-justify">Title: {{ declarationInfo?.designation || 'Designation' }}</p>
              <p class="text-justify">Date: {{ currentDate }}</p>
            </div>
          </div>
        </div>

        <!-- Distributor "I Certify" Button (at the bottom after all previews) -->
        <div class="max-w-md mx-auto mt-6">
          <Button
            theme="gray"
            variant="solid"
            class="w-full"
            @click="handleCertify"
            :disabled="!isValid"
          >
            I Certify
          </Button>
        </div>
      </div>


      <!-- Static Fallback for Employee Declaration -->
      <div v-else-if="userRole === 'Employee'" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h4 class="text-center font-semibold mb-4">
          Employee Declaration - Ethical Practices & Compliance
        </h4>
        <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
          <p class="text-justify">
            I hereby declare that I have undergone and understood training provided on Ethical Practices and compliance. As a responsible employee of Meril, I acknowledge and accept the duty to comply with the procedural frameworks developed and adopted by the Meril's Management from time to time.
          </p>
          <p class="text-justify">
            I have been thoroughly informed on the various Code of Conduct that govern the ethical operation of Meril's business, which I agree to follow diligently. I have read understood and consent to abide by the following Codes of Conduct on a consensus-ad-idem basis:
          </p>
          <ol class="list-decimal pl-6 space-y-1">
            <li>Anti Bribery and Anti Corruption Policy</li>
            <li>Export Controls and Trade Sanctions Policy</li>
            <li>HCP & HCO Compliance framework</li>
            <li>National Pharmaceutical Pricing Authority norms for capping of maximum retail price & maximum trade margin across all trade channels</li>
            <li>FCPA (Foreign Corrupt Practices Act)</li>
          </ol>
          <p class="text-justify">
            I hereby confirm that I shall adhere in all respects to the ethics and standards of conduct outlined in the above Codes of Conduct. I understand that any violation or even potential violation of the these Codes of Conduct / Policies may result in disciplinary action, including termination of my employment.
          </p>
          <p class="text-justify">
            I certify that I am not currently in violation of any of the afore mentioned Codes of Conduct.
          </p>
          <p class="text-justify">
            Furthermore, I declare that I have no direct or indirect familial, financial, or other relationships with any distributor or nominated representative of the distributor. Should I become aware of any such relationship in the future, I commit to disclosing it to Meril within thirty (30) days from the date of awareness.
          </p>
          <p class="text-justify">
            I also declare that I will not engage in any financial transactions with any distributor or nominated representative of the distributor. I acknowledge that Meril Group shall bear no responsibility or liability for any such transactions.
          </p>
          <div class="mt-6 space-y-1">
            <p class="text-justify">Employee Name: {{ declarationInfo?.employee_name || 'Name' }}</p>
            <p class="text-justify">Employee ID: {{ declarationInfo?.custom_employee_id || 'ID' }}</p>
            <p class="text-justify">Company Name: {{ declarationInfo?.company || 'Company' }}</p>
            <p class="text-justify">Date: {{ currentDate }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { TextInput, Button, createResource } from 'frappe-ui'
import DOMPurify from 'dompurify'

const props = defineProps({
  userRole: {
    type: String,
    default: null
  },
  declarationInfo: {
    type: Object,
    default: () => ({})
  },
  certificationData: {
    type: Object,
    default: () => ({
      name: '',
      date: '',
      isCompleted: false
    })
  },
  course: {
    type: String,
    default: null
  },
  documentType: {
    type: String,
    default: null
  },
  complianceOfficerName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['certification-complete', 'officer-nominated', 'validation-changed'])

const localName = ref('')
const localDate = ref('')
const utcDate = ref('')
const nameError = ref('')
const localComplianceOfficerName = ref('')
const complianceOfficerError = ref('')
const documentPreviews = ref({})
const previewLoading = ref({})
const previewErrors = ref({})
const useStaticPreview = ref(false)
const documentConfiguration = ref(null)
const configurationLoading = ref(false)
const configurationError = ref(null)

const currentDate = computed(() => {
  const date = new Date()
  const day = date.getDate().toString().padStart(2, '0')
  const month = date.toLocaleString('default', { month: 'long' })
  const year = date.getFullYear()
  return `${day} ${month} ${year}`
})

const currentDateTime = computed(() => {
  const now = new Date()
  const day = now.getDate().toString().padStart(2, '0')
  const month = (now.getMonth() + 1).toString().padStart(2, '0')
  const year = now.getFullYear()
  const hours = now.getHours().toString().padStart(2, '0')
  const minutes = now.getMinutes().toString().padStart(2, '0')

  return `${day}/${month}/${year}, ${hours}:${minutes}`
})

const isValid = computed(() => {
  // For employees, no name validation required (comes from Employee doctype)
  if (props.userRole === 'Employee') {
    return true
  }

  // For adoption form (distributors), also check compliance officer name
  const isCompliancePolicyForm = showDeclaration('Meril Distributor Compliance Policy Adoption Form') ||
    (useStaticPreview.value && props.documentType === 'Meril Distributor Compliance Policy Adoption Form')

  // For adoption form (distributors), ONLY check compliance officer name
  // (name field is hidden, so don't validate it)
  if (isCompliancePolicyForm && props.userRole === 'Distributor') {
    const isOfficerValid = localComplianceOfficerName.value.trim().length >= 3
    return isOfficerValid
  }

  // For other forms, check the name field
  const isNameValid = localName.value.trim().length >= 3
  return isNameValid
})

const getSanitizedPreview = (docType) => {
  if (!documentPreviews.value[docType]) return ''
  // Configure DOMPurify to allow certain attributes and tags
  const config = {
    ALLOWED_TAGS: ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section',
                   'header', 'footer', 'img', 'br', 'hr', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th',
                   'strong', 'b', 'em', 'i', 'u', 'pre', 'code', 'style'],
    ALLOWED_ATTR: ['class', 'id', 'style', 'src', 'alt', 'width', 'height', 'colspan', 'rowspan',
                    'data-num', 'href', 'target'],
    ALLOW_DATA_ATTR: true,
    ADD_TAGS: ['style'],
    ADD_ATTR: ['style'],
    KEEP_CONTENT: true
  }
  return DOMPurify.sanitize(documentPreviews.value[docType], config)
}

const getDocumentTypes = () => {
  if (!documentConfiguration.value || !documentConfiguration.value.document_types) {
    return []
  }

  // For employees, only get documents with preview enabled that require declaration
  if (props.userRole === 'Employee') {
    return documentConfiguration.value.document_types
      .filter(doc => doc.show_preview !== false && doc.requires_declaration &&
              (doc.name.includes('Employee') || doc.key === 'employee_declaration_form'))
      .map(doc => doc.name)
  }

  // For distributors, get uploadable documents that require declaration
  return documentConfiguration.value.document_types
    .filter(doc => doc.requires_declaration && doc.uploadable)
    .map(doc => doc.name)
}

const getAllDocumentTypes = () => {
  if (!documentConfiguration.value || !documentConfiguration.value.document_types) {
    return []
  }

  // For employees, only return documents with show_preview enabled
  if (props.userRole === 'Employee') {
    return documentConfiguration.value.document_types
      .filter(doc => doc.show_preview !== false)  // Only show preview if show_preview is true/undefined
      .filter(doc => doc.name.includes('Employee') || doc.key === 'employee_declaration_form')
      .map(doc => doc.name)
  }

  // For distributors, return all document types
  return documentConfiguration.value.document_types.map(doc => doc.name)
}

// Function to fetch document configuration
const fetchDocumentConfiguration = async () => {
  configurationLoading.value = true
  configurationError.value = null

  try {
    const resource = createResource({
      url: 'lms.overrides.documents.get_document_configuration',
      params: {
        course: props.course
      },
      onSuccess: (data) => {
        if (data.success) {
          documentConfiguration.value = data
          // After getting configuration, fetch previews for documents that require declaration
          const docsWithDeclaration = data.document_types.filter(doc => doc.requires_declaration).map(doc => doc.name)
          if (docsWithDeclaration.length > 0) {
            fetchDocumentPreview()
          }
          // Now handle pre-filling logic after configuration is loaded
          handleNamePreFilling()
        } else {
          configurationError.value = data.message || 'Failed to load document configuration'
          useStaticPreview.value = true
          // Handle pre-filling for static preview
          handleNamePreFilling()
        }
        configurationLoading.value = false
      },
      onError: (error) => {
        console.error('Error fetching document configuration:', error)
        configurationError.value = 'Failed to load document configuration'
        useStaticPreview.value = true
        // Handle pre-filling for static preview
        handleNamePreFilling()
        configurationLoading.value = false
      }
    })

    resource.reload()
  } catch (error) {
    console.error('Error in fetchDocumentConfiguration:', error)
    configurationError.value = 'Failed to load document configuration'
    useStaticPreview.value = true
    // Handle pre-filling for static preview
    handleNamePreFilling()
    configurationLoading.value = false
  }
}

// Helper function to check if all previews are loaded
const allPreviewsLoaded = computed(() => {
  const docTypes = getAllDocumentTypes()
  return docTypes.every(docType =>
    documentPreviews.value[docType] || previewErrors.value[docType] || previewLoading.value[docType]
  )
})

const fetchDocumentPreview = (specificDocType = null) => {
  const docTypes = specificDocType ? [specificDocType] : getDocumentTypes()

  docTypes.forEach(docType => {
    previewLoading.value[docType] = true
    previewErrors.value[docType] = null

    // Create individual resource for each document type
    const resource = createResource({
      url: 'lms.overrides.documents.get_document_preview_html',
      params: {
        course: props.course,
        document_type: docType,
        compliance_officer_name: localComplianceOfficerName.value || props.complianceOfficerName || localName.value || props.certificationData?.name || props.declarationInfo?.attendee_name
      },
      onSuccess: (data) => {
        if (data.success && data.html_content) {
          documentPreviews.value[docType] = data.html_content
        } else {
          previewErrors.value[docType] = data.message || 'Failed to load preview'
        }
        previewLoading.value[docType] = false
      },
      onError: (error) => {
        console.error(`Error fetching preview for ${docType}:`, error)
        previewErrors.value[docType] = 'Failed to load document preview'
        previewLoading.value[docType] = false
      }
    })

    resource.reload()
  })
}

const getHeaderTitle = () => {
  if (props.userRole === 'Employee') {
    return 'Employee Declaration'
  }
  return 'Document Certification'
}

const getHeaderDescription = () => {
  if (props.userRole === 'Employee') {
    return 'Please review the Employee Declaration and provide your certification.'
  }
  return 'Please review the compliance documents and provide your certification.'
}

const showDeclaration = (documentType) => {
  if (!documentConfiguration.value || !documentConfiguration.value.document_types) {
    return false
  }

  // Check if the document type exists in the configuration and requires declaration
  const docConfig = documentConfiguration.value.document_types.find(doc => doc.name === documentType)
  return docConfig && docConfig.requires_declaration
}

// Handle name pre-filling logic after configuration is loaded
const handleNamePreFilling = () => {
  // Pre-fill name if available from declaration info (except for compliance policy adoption form)
  const isCompliancePolicyForm = showDeclaration('Meril Distributor Compliance Policy Adoption Form') ||
    (useStaticPreview.value && props.documentType === 'Meril Distributor Compliance Policy Adoption Form')

  // Do not auto-fill for compliance policy adoption form since compliance officer name comes from previous step
  if (!isCompliancePolicyForm) {
    if (props.declarationInfo?.attendee_name && !localName.value) {
      localName.value = props.declarationInfo.attendee_name
    } else if (props.declarationInfo?.employee_name && !localName.value) {
      localName.value = props.declarationInfo.employee_name
    }
  }
  // For compliance policy forms, the compliance officer name comes from the previous step (props.complianceOfficerName)
}

const validateName = () => {
  nameError.value = ''
  if (localName.value.trim().length < 3) {
    nameError.value = 'Name must be at least 3 characters long'
    return false
  }
  return true
}

const validateComplianceOfficer = () => {
  complianceOfficerError.value = ''
  if (localComplianceOfficerName.value.trim().length < 3) {
    complianceOfficerError.value = 'Compliance officer name must be at least 3 characters long'
    return false
  }
  return true
}

const handleCertify = () => {
  // For adoption form, also validate compliance officer
  const isCompliancePolicyForm = showDeclaration('Meril Distributor Compliance Policy Adoption Form') ||
    (useStaticPreview.value && props.documentType === 'Meril Distributor Compliance Policy Adoption Form')

  // Skip name validation for employees and for adoption forms (name field is hidden)
  if (props.userRole !== 'Employee' && !(isCompliancePolicyForm && props.userRole === 'Distributor') && !validateName()) {
    return
  }

  if (isCompliancePolicyForm && props.userRole === 'Distributor') {
    if (!validateComplianceOfficer()) {
      return
    }
    // Emit compliance officer nominated event
    emit('officer-nominated', {
      name: localComplianceOfficerName.value.trim(),
      isValid: true
    })
  }

  // For employees, use employee name from declaration info; for others use local name
  const certificationName = (() => {
    if (props.userRole === 'Employee') {
      return props.declarationInfo?.employee_name || props.declarationInfo?.attendee_name || 'Employee'
    }
    // If adoption form for Distributor, use the nominated compliance officer name
    if (isCompliancePolicyForm && props.userRole === 'Distributor') {
      return (localComplianceOfficerName.value || props.complianceOfficerName || '').trim() || localName.value.trim()
    }
    return localName.value.trim()
  })()

  emit('certification-complete', {
    name: certificationName,
    date: utcDate.value
  })
}

// Watch for changes in certification data from parent
watch(() => props.certificationData, (newData) => {
  // Check if this is a compliance policy adoption form before pre-filling name
  const isCompliancePolicyForm = showDeclaration('Meril Distributor Compliance Policy Adoption Form') ||
    (useStaticPreview.value && props.documentType === 'Meril Distributor Compliance Policy Adoption Form')

  // Do not auto-fill name for compliance policy adoption form (compliance officer field should be empty)
  if (newData.name && !localName.value && !isCompliancePolicyForm) {
    localName.value = newData.name
  }
  if (newData.date && !localDate.value) {
    localDate.value = newData.date
    utcDate.value = newData.date
  }
}, { immediate: true })

// Watch for name changes to update preview
watch(localName, (newName) => {
  if (newName && Object.keys(documentPreviews.value).length > 0) {
    // Debounce the preview update
    clearTimeout(window.previewUpdateTimeout)
    window.previewUpdateTimeout = setTimeout(() => {
      fetchDocumentPreview()
    }, 500)
  }
})

// Watch for compliance officer changes
watch(localComplianceOfficerName, (newName) => {
  const isValid = newName.trim().length >= 3
  emit('validation-changed', isValid)

  if (newName && Object.keys(documentPreviews.value).length > 0) {
    // Debounce the preview update
    clearTimeout(window.previewUpdateTimeout)
    window.previewUpdateTimeout = setTimeout(() => {
      fetchDocumentPreview()
    }, 500)
  }
})

// Watch for changes in compliance officer prop
watch(() => props.complianceOfficerName, (newName) => {
  if (newName && !localComplianceOfficerName.value) {
    localComplianceOfficerName.value = newName
  }
}, { immediate: true })

onMounted(() => {
  // Set current date/time — display in browser's local timezone, store UTC for submission
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  localDate.value = `${year}-${month}-${day}T${hours}:${minutes}`
  utcDate.value = now.toISOString().slice(0, 16)

  // Fetch document configuration first, which will then fetch previews
  fetchDocumentConfiguration()
})
</script>

<style scoped>
/* Compliance Officer Field Highlighting */
.compliance-officer-highlight {
  border: 2px solid #dc3545 !important;
  box-shadow: 0 0 6px rgba(220, 53, 69, 0.4);
}

.compliance-officer-highlight :deep(input),
.compliance-officer-highlight :deep(.compliance-officer-input input) {
  border: 2px solid #dc3545 !important;
  box-shadow: 0 0 4px rgba(220, 53, 69, 0.3);
}

.compliance-officer-highlight :deep(input:focus),
.compliance-officer-highlight :deep(.compliance-officer-input input:focus) {
  border-color: #dc3545 !important;
  box-shadow: 0 0 6px rgba(220, 53, 69, 0.5);
  outline: none;
}
</style>
