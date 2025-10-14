import { reactive, computed } from 'vue'
import { call } from 'frappe-ui'
import { safeApiCall, handleApiError, createDegradedModeResponse } from '../utils/api-error-handler'
import { resetCourseCompletion } from './course_completion.js'

const state = reactive({
  // Modal and workflow state
  isOpen: false,
  currentStep: 1,
  totalSteps: 5,
  courseName: null,

  // User and role information
  userRole: null,
  declarationInfo: null,

  // Document configuration
  enabledDocuments: {
    distributor_self_declaration: false,
    meril_distributor_compliance_code_of_conduct: false,
    meril_distributor_compliance_policy_adoption_form: false
  },

  // Endo division detection
  distributorDivisions: {
    hasEndo: false,
    hasNonEndo: false,
    divisions: []
  },

  // Document tracking
  requiredDocuments: [],
  uploadedDocuments: new Set(),
  documentsList: [],
  uploadedDocumentsList: [],

  // Step states
  complianceOfficerName: '',
  complianceOfficerValid: false,

  certification: {
    name: '',
    date: '',
    isCompleted: false
  },

  downloads: {
    completedDownloads: new Set(),
    isStepCompleted: false
  },

  uploads: {
    currentDocument: null,
    uploadProgress: {},
    isStepCompleted: false
  },

  // Loading and error states
  loading: {
    initialization: false,
    upload: false,
    download: false
  },

  errors: {
    general: null,
    upload: null,
    download: null
  },

  // Course document record
  courseDocumentsRecordId: null,
  doctype: null
})

// Computed properties
const isAllDocumentsUploaded = computed(() => {
  // Only count uploadable documents, not download-only ones
  const uploadableDocuments = state.requiredDocuments.filter(doc => !doc.downloadOnly)
  const requiredCount = uploadableDocuments.length
  const uploadedCount = state.uploadedDocuments.size
  return requiredCount > 0 && uploadedCount >= requiredCount
})

const currentDocumentToUpload = computed(() => {
  // Only consider uploadable documents, skip download-only ones
  const uploadableDocuments = state.requiredDocuments.filter(doc => !doc.downloadOnly)
  for (const doc of uploadableDocuments) {
    if (!state.uploadedDocuments.has(doc.name)) {
      return doc
    }
  }
  return null
})

const progressPercentage = computed(() => {
  if (state.totalSteps === 0) return 0
  return Math.round((state.currentStep / state.totalSteps) * 100)
})

const canProceedToNextStep = computed(() => {
  switch (state.currentStep) {
    case 1: // Compliance Officer step
      return state.complianceOfficerValid && state.complianceOfficerName.trim().length >= 3
    case 2: // Certification step
      return state.certification.isCompleted && state.certification.name.trim().length >= 3
    case 3: // Download step
      return state.downloads.isStepCompleted
    case 4: // Upload step
      return state.uploads.isStepCompleted || isAllDocumentsUploaded.value
    case 5: // Completion step
      return true
    default:
      return false
  }
})

// Actions
const openModal = (courseName) => {
  state.isOpen = true
  state.courseName = courseName
  state.currentStep = 1
  resetErrors()
  initializeWorkflow()
}

const closeModal = () => {
  state.isOpen = false
  resetState()
  resetCourseCompletion()
}

const nextStep = () => {
  if (canProceedToNextStep.value && state.currentStep < state.totalSteps) {
    state.currentStep++
  }
}

const previousStep = () => {
  if (state.currentStep > 1) {
    state.currentStep--
  }
}

const goToStep = (step) => {
  if (step >= 1 && step <= state.totalSteps) {
    state.currentStep = step
  }
}

const resetState = () => {
  state.currentStep = 1
  state.courseName = null
  state.userRole = null
  state.declarationInfo = null
  state.uploadedDocuments.clear()
  state.documentsList = []
  state.uploadedDocumentsList = []
  state.courseDocumentsRecordId = null
  state.doctype = null

  // Reset step states
  state.complianceOfficerName = ''
  state.complianceOfficerValid = false

  state.certification = {
    name: '',
    date: '',
    isCompleted: false
  }

  state.downloads = {
    completedDownloads: new Set(),
    isStepCompleted: false
  }

  state.uploads = {
    currentDocument: null,
    uploadProgress: {},
    isStepCompleted: false
  }

  resetErrors()
}

const resetErrors = () => {
  state.errors.general = null
  state.errors.upload = null
  state.errors.download = null
}

const setError = (type, message) => {
  state.errors[type] = message
}

const clearError = (type) => {
  state.errors[type] = null
}


// API calls
const initializeWorkflow = async () => {
  if (!state.courseName) return

  try {
    state.loading.initialization = true
    resetErrors()

    // Get enabled document flags with error handling
    const enabledResponse = await safeApiCall(
      () => call("lms.overrides.documents.get_upload_download_docuemtn_enabled"),
      {
        fallbackValue: createDegradedModeResponse('enabled_flags'),
        context: 'Getting enabled documents',
        showErrorToast: false
      }
    )

    if (enabledResponse) {
      state.enabledDocuments = {
        distributor_self_declaration: !!enabledResponse.distributor_self_declaration,
        meril_distributor_compliance_code_of_conduct: !!enabledResponse.meril_distributor_compliance_code_of_conduct,
        meril_distributor_compliance_policy_adoption_form: !!enabledResponse.meril_distributor_compliance_policy_adoption_form
      }

      if (enabledResponse.degradedMode) {
        console.warn('Running in degraded mode - using default document configuration')
      }
    }

    // Check document submission status with better error handling
    const submissionResponse = await safeApiCall(
      () => call('lms.overrides.documents.has_user_submited_document', {
        course: state.courseName
      }),
      {
        fallbackValue: null,
        throwOnError: false,
        context: 'Checking document submission status',
        showErrorToast: false
      }
    )

    if (!submissionResponse) {
      // If API call failed completely, use degraded mode
      const degradedResponse = createDegradedModeResponse('documents')
      setError('general', 'Unable to access document services. Some features may be limited.')

      // Set minimal state to allow navigation
      state.userRole = 'Unknown'
      state.documentsList = []
      state.uploadedDocumentsList = []
      await updateRequiredDocuments()
      return
    }

    // Handle various error conditions
    if (submissionResponse?.error) {
      setError('general', submissionResponse.error)
      return
    }

    if (submissionResponse?.success === false) {
      // Check specific error conditions
      if (submissionResponse.enrollment_required) {
        setError('general', 'You are not enrolled in this course. Please enroll first.')
        return
      }
      if (submissionResponse.progress !== undefined && submissionResponse.progress < 100) {
        setError('general', `Please complete the course first. Current progress: ${submissionResponse.progress}%`)
        return
      }
      if (submissionResponse.message) {
        setError('general', submissionResponse.message)
        return
      }
    }

    // Set user role and document info
    state.userRole = submissionResponse.role_is
    state.courseDocumentsRecordId = submissionResponse.course_documents_record_id
    state.doctype = submissionResponse.doctype
    state.documentsList = submissionResponse.documents_list || []

    // Detect Endo divisions from the documents list
    detectEndoDivisions(submissionResponse.documents_list)

    // Handle uploaded documents
    if (submissionResponse.uploaded_documents && submissionResponse.uploaded_documents.length > 0) {
      state.uploadedDocumentsList = submissionResponse.uploaded_documents
      submissionResponse.uploaded_documents.forEach(doc => {
        state.uploadedDocuments.add(doc.name)
      })
    }

    // Set certification status from backend response
    if (submissionResponse.is_certified !== undefined) {
      state.certification.isCompleted = submissionResponse.is_certified
    }

    // Set required documents based on enabled flags
    await updateRequiredDocuments()

    // Get declaration info with error handling
    if (submissionResponse?.role_is) {
      try {
        await getDeclarationInfo()
      } catch (declError) {
        console.warn('Failed to get declaration info:', declError)
        // Continue without declaration info - it's not critical
      }
    }

    // Determine initial step based on current state
    determineInitialStep()

  } catch (error) {
    console.error('Error initializing workflow:', error)
    setError('general', 'Error initializing document workflow')
  } finally {
    state.loading.initialization = false
  }
}

const updateRequiredDocuments = async () => {
  try {
    // Use the new dynamic document configuration API
    const response = await call("lms.overrides.documents.get_document_configuration", {
      course: state.courseName
    })

    if (response && response.success) {
      // Convert the API response to the store format
      const documents = response.document_types.map(doc => ({
        key: doc.key,
        name: doc.name,
        requiresDeclaration: doc.requires_declaration,
        downloadOnly: !doc.uploadable
      }))

      state.requiredDocuments = documents

      // Update the state with the configuration data
      state.enabledDocuments = response.enabled_documents || {}
      state.distributorDivisions = response.division_info || {
        hasEndo: false,
        hasNonEndo: false,
        divisions: []
      }
      state.userRole = response.user_role

      console.log('Updated documents from API:', {
        documents: documents.length,
        hasEndo: state.distributorDivisions.hasEndo,
        hasNonEndo: state.distributorDivisions.hasNonEndo,
        userRole: state.userRole
      })
    } else {
      console.error('Failed to get document configuration:', response?.message)
      // Fallback to empty state
      state.requiredDocuments = []
    }
  } catch (error) {
    console.error('Error fetching document configuration:', error)
    // Fallback to empty state
    state.requiredDocuments = []
  }
}

const getDeclarationInfo = async () => {
  try {
    const response = await call("lms.overrides.documents.get_declaration_info")
    if (response && response.success !== false) {
      state.declarationInfo = response

      // Set default certification name if available
      if (!state.certification.name && response.attendee_name) {
        state.certification.name = response.attendee_name
      }

      // Also detect Endo divisions from distributor's company table if available
      if (response.meril_company_table && Array.isArray(response.meril_company_table)) {
        await detectEndoDivisionsFromCompanyTable(response.meril_company_table)
      }
    }
  } catch (error) {
    console.error('Error getting declaration info:', error)
    // Don't throw - declaration info is optional
  }
}

const detectEndoDivisions = (documentsList) => {
  // Reset division flags
  state.distributorDivisions.hasEndo = false
  state.distributorDivisions.hasNonEndo = false
  state.distributorDivisions.divisions = []

  // Check if documents list contains Endo-specific or general compliance policy
  if (documentsList && Array.isArray(documentsList)) {
    if (documentsList.includes('Meril Distributor Compliance Policy for Endo')) {
      state.distributorDivisions.hasEndo = true
    }
    if (documentsList.includes('Meril Distributor Compliance Policy')) {
      state.distributorDivisions.hasNonEndo = true
    }
  }
}

const detectEndoDivisionsFromCompanyTable = async (companyTable) => {
  // Additional detection from company table data
  if (!companyTable || !Array.isArray(companyTable)) return

  let hasEndo = false
  let hasNonEndo = false
  const divisions = []

  for (const company of companyTable) {
    const divisionName = (company.division || '').toLowerCase()
    divisions.push(company.division || '')

    if (divisionName.includes('endo')) {
      hasEndo = true
    } else if (divisionName) {
      hasNonEndo = true
    }
  }

  // Update state with detected divisions
  state.distributorDivisions.hasEndo = state.distributorDivisions.hasEndo || hasEndo
  state.distributorDivisions.hasNonEndo = state.distributorDivisions.hasNonEndo || hasNonEndo
  state.distributorDivisions.divisions = divisions

  // Re-update required documents after detection
  await updateRequiredDocuments()
}

const determineInitialStep = () => {
  // Check if user has completed certification step
  const isCertified = state.certification.isCompleted

  // If documents are already submitted, go to completion step
  if (isAllDocumentsUploaded.value) {
    state.currentStep = 4
    state.certification.isCompleted = true
    state.downloads.isStepCompleted = true
    state.uploads.isStepCompleted = true
  } else if (state.uploadedDocuments.size > 0 && isCertified) {
    // Some documents uploaded and user is certified, go to upload step
    state.currentStep = 3
    state.certification.isCompleted = true
    state.downloads.isStepCompleted = true
  } else if (isCertified) {
    // User is certified but no documents uploaded, go to download step
    state.currentStep = 2
    state.certification.isCompleted = true
  } else {
    // Start from beginning - certification step
    state.currentStep = 1
  }
}

const completeCertification = async (name, date) => {
  state.certification.name = name
  state.certification.date = date
  state.certification.isCompleted = true

  // Call backend to persist certification status
  try {
    const response = await call("lms.overrides.documents.complete_certification", {
      course: state.courseName,
      name: name,
      date: date
    })

    if (!response.success) {
      console.error('Failed to save certification status:', response.message)
      // Don't revert the frontend state as user has completed the step
    }
  } catch (error) {
    console.error('Error saving certification status:', error)
    // Don't revert the frontend state as user has completed the step
  }
}

const markDownloadCompleted = (documentName) => {
  state.downloads.completedDownloads.add(documentName)

  // Check if all required downloads are completed
  // All documents need to be downloaded (both uploadable and download-only)
  const requiredDownloads = state.requiredDocuments.length
  if (state.downloads.completedDownloads.size >= requiredDownloads) {
    state.downloads.isStepCompleted = true
  }
}

const markDocumentUploaded = (documentName) => {
  state.uploadedDocuments.add(documentName)

  // Update upload progress
  state.uploads.uploadProgress[documentName] = 100

  // Check if all required uploads are completed (only uploadable documents)
  const uploadableDocuments = state.requiredDocuments.filter(doc => !doc.downloadOnly)
  if (state.uploadedDocuments.size >= uploadableDocuments.length) {
    state.uploads.isStepCompleted = true
  }
}

const setUploadProgress = (documentName, progress) => {
  state.uploads.uploadProgress[documentName] = progress
}

const setCurrentUploadDocument = (documentName) => {
  state.uploads.currentDocument = documentName
}

const getUploadableDocuments = () => {
  // Filter out download-only documents (like compliance policies)
  return state.requiredDocuments.filter(doc => !doc.downloadOnly)
}

const getDownloadableDocuments = () => {
  // Return all documents that need to be downloaded
  // This includes both uploadable docs and download-only docs
  return state.requiredDocuments
}

export {
  state,
  isAllDocumentsUploaded,
  currentDocumentToUpload,
  progressPercentage,
  canProceedToNextStep,
  openModal,
  closeModal,
  nextStep,
  previousStep,
  goToStep,
  resetState,
  setError,
  clearError,
  initializeWorkflow,
  completeCertification,
  markDownloadCompleted,
  markDocumentUploaded,
  setUploadProgress,
  setCurrentUploadDocument,
  getUploadableDocuments,
  getDownloadableDocuments
}