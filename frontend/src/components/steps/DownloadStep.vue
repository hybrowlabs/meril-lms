<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h3 class="text-lg font-medium text-gray-900 mb-2">
        Download Required Documents
      </h3>
      <p class="text-sm text-gray-600">
        {{ headerDescription }}
      </p>
    </div>

    <!-- Instructions -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex">
        <svg class="w-5 h-5 text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3">
          <h4 class="text-sm font-medium text-blue-800">Instructions</h4>
          <div class="text-sm text-blue-700 mt-1">
            <ol class="list-decimal list-inside space-y-1">
              <li>Download each required document using the buttons below</li>
              <li v-if="hasDocumentRequiringLetterhead && !isEmployee">Insert your company's letterhead at the top of the Compliance Policy Adoption Form</li>
              <li>Sign all downloaded documents</li>
              <li v-if="!isEmployee">Keep the signed documents ready for upload in the next step</li>
              <li v-else>Keep the signed documents for your records</li>
            </ol>
          </div>
        </div>
      </div>
    </div>

    <!-- Document Download List -->
    <div class="space-y-4">
      <div
        v-for="document in requiredDocuments"
        :key="document.name"
        class="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-medium text-gray-900 break-words">{{ getDocumentLabel(document) }}</h4>
            <p class="text-sm text-gray-500 mt-1 break-words">
              {{ getDocumentDescription(getDocumentLabel(document)) }}
            </p>

            <!-- Special instruction for Policy Adoption Form -->
            <div v-if="document.name === 'Meril Distributor Compliance Policy Adoption Form'" class="mt-2">
              <div class="bg-yellow-50 border border-yellow-200 rounded p-2">
                <p class="text-xs text-yellow-800">
                  <strong>Note:</strong> Please insert your company's letterhead at the top of this document before signing.
                </p>
              </div>
            </div>
          </div>

          <div class="flex-shrink-0 flex flex-col items-end space-y-2">
            <!-- Download Status -->
            <div v-if="completedDownloads.has(document.name)" class="flex items-center text-green-600 bg-green-50 px-2 py-1 rounded-full">
              <svg class="w-4 h-4 mr-1 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              <span class="text-xs font-medium whitespace-nowrap">Downloaded</span>
            </div>

            <!-- Download Button -->
            <Button
              theme="gray"
              variant="outline"
              size="md"
              icon="download"
              @click="downloadDocument(document)"
              :disabled="downloadingDocuments.has(document.name)"
              class="flex items-center justify-center min-w-[140px] px-6 py-3 h-12 bg-white border-2 border-gray-300 text-gray-700 font-medium hover:bg-gray-50 hover:border-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 transition-all duration-200 text-sm"
            >
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Progress Summary -->
    <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <div class="flex items-center justify-between">
        <div>
          <h4 class="text-sm font-medium text-gray-900">Download Progress</h4>
          <p class="text-sm text-gray-600">
            {{ completedDownloads.size }} of {{ requiredDocuments.length }} documents downloaded
          </p>
        </div>
        <div class="flex items-center">
          <div class="w-32 bg-gray-200 rounded-full h-2 mr-3">
            <div
              class="bg-gray-900 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${downloadProgress}%` }"
            ></div>
          </div>
          <span class="text-sm font-medium text-gray-700">{{ downloadProgress }}%</span>
        </div>
      </div>
    </div>

    <!-- Next Step Preview / Downloads Complete -->
    <div v-if="allDownloadsCompleted" class="bg-green-50 border border-green-200 rounded-lg p-4">
      <div class="flex">
        <svg class="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3">
          <h4 class="text-sm font-medium text-green-800">{{ isEmployee ? 'Downloads Complete' : 'Ready for Next Step' }}</h4>
          <p class="text-sm text-green-700 mt-1">
            {{ isEmployee
              ? 'All documents have been downloaded. You can close this dialog.'
              : 'All documents have been downloaded. You can now proceed to the upload step.'
            }}
          </p>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="downloadError" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex">
        <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3">
          <h4 class="text-sm font-medium text-red-800">Download Error</h4>
          <p class="text-sm text-red-700 mt-1">{{ downloadError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Button, Spinner, call, toast } from 'frappe-ui'
import { handleApiError, safeApiCall } from '../../utils/api-error-handler'

const props = defineProps({
  requiredDocuments: {
    type: Array,
    default: () => []
  },
  certificationData: {
    type: Object,
    default: () => ({})
  },
  courseName: {
    type: String,
    default: ''
  },
  completedDownloads: {
    type: Set,
    default: () => new Set()
  },
  complianceOfficerName: {
    type: String,
    default: ''
  },
  userRole: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['download-complete'])

const downloadingDocuments = ref(new Set())
const downloadError = ref('')

const downloadProgress = computed(() => {
  if (props.requiredDocuments.length === 0) return 0
  return Math.round((props.completedDownloads.size / props.requiredDocuments.length) * 100)
})

const allDownloadsCompleted = computed(() => {
  return props.requiredDocuments.length > 0 && props.completedDownloads.size >= props.requiredDocuments.length
})

const hasDocumentRequiringLetterhead = computed(() => {
  return props.requiredDocuments.some(doc =>
    doc.name === 'Meril Distributor Compliance Policy Adoption Form'
  )
})

const isEmployee = computed(() => props.userRole === 'Employee')

const headerDescription = computed(() => {
  if (isEmployee.value) {
    return 'Download the generated documents for your records.'
  }
  return 'Download the generated documents, sign them, and prepare for upload.'
})

const getDocumentDescription = (documentName) => {
  if (documentName && documentName.toLowerCase().includes('employee declaration')) {
    return 'Employee declaration and acknowledgment form'
  }
  const descriptions = {
    'Meril Distributor Compliance Policy Adoption Form': 'Company compliance policy adoption with letterhead requirement',
    'Distributor Self Declaration': 'Self-declaration of compliance understanding',
    'Meril Distributor Compliance Code of Conduct': 'Code of conduct acknowledgment and agreement',
    'Distributor Completion Certificate': 'Certificate of course completion',
    'Meril Distributor Compliance Policy for Endo': 'Compliance policy document for Endo division',
    'Meril Distributor Compliance Policy': 'Non-Endo compliance policy document',
    'Employee Declaration Form': 'Employee declaration and acknowledgment form',
    'Employee Completion Certificate': 'Employee course completion certificate',
    'International Completion Certificate': 'Employee course completion certificate with company and country details'
  }
  return descriptions[documentName] || 'Required compliance document'
}

const getDocumentLabel = (document) => document?.label || document?.name

const downloadDocument = async (docItem) => {
  if (downloadingDocuments.value.has(docItem.name)) return

  try {
    downloadingDocuments.value.add(docItem.name)
    downloadError.value = ''

    const documentLabel = getDocumentLabel(docItem)
    console.log('Starting download for document:', documentLabel)
    console.log('Props data:', {
      certificationData: props.certificationData,
      courseName: props.courseName
    })

    let response

    // Handle special cases for Endo/Non-Endo compliance policy documents
    if (docItem.name === "Meril Distributor Compliance Policy") {
      console.log('Downloading Non-Endo compliance policy')
      try {
        // Get the base URL for API endpoint
        const baseUrl = window.frappe?.boot?.frappe_base_url || window.location.origin
        const url = `${baseUrl}/api/method/lms.overrides.documents.download_nonendo_file`

        // Create a temporary link to trigger download
        const link = document.createElement('a')
        link.href = url
        link.download = 'Meril_Distributor_Compliance_Policy.pdf'
        link.style.display = 'none'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        // Mark as downloaded (no response content needed for direct downloads)
        emit('download-complete', docItem.name)
        toast.success('Non-Endo compliance policy download started')
        return
      } catch (error) {
        console.error('Error downloading Non-Endo policy:', error)
        throw new Error('Failed to download compliance policy document')
      }
    } else if (docItem.name === "Meril Distributor Compliance Policy for Endo") {
      console.log('Downloading Endo compliance policy')
      try {
        // Get the base URL for API endpoint
        const baseUrl = window.frappe?.boot?.frappe_base_url || window.location.origin
        const url = `${baseUrl}/api/method/lms.overrides.documents.download_endo_file`

        // Create a temporary link to trigger download
        const link = document.createElement('a')
        link.href = url
        link.download = 'Meril_Distributor_Compliance_Policy_Endo.pdf'
        link.style.display = 'none'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        // Mark as downloaded (no response content needed for direct downloads)
        emit('download-complete', docItem.name)
        toast.success('Endo compliance policy download started')
        return
      } catch (error) {
        console.error('Error downloading Endo policy:', error)
        throw new Error('Failed to download compliance policy document')
      }
    } else {
      // Use the proper Frappe backend API for other document generation
      try {
        console.log('Generating document using Frappe print format:', docItem.name)

        // Call the generate_dynamic_docx API with print format enabled
        // This will generate PDF from the appropriate print format
        const isAdoption = docItem.name === 'Meril Distributor Compliance Policy Adoption Form'
        const effectiveName = isAdoption
          ? (props.complianceOfficerName || props.certificationData?.name || 'User')
          : (props.certificationData?.name || 'User')

        response = await call("lms.overrides.documents.generate_dynamic_docx", {
          name: effectiveName,
          course: props.courseName,
          font_path: null,
          document_type: docItem.name,
          use_print_format: true
        })

    console.log('Document generation response:', response)
      } catch (apiError) {
        console.error('Error generating document:', apiError)

        // Handle the error and check its type
        const errorResult = handleApiError(apiError, {
          showToast: false,
          context: `Generating ${docItem.name}`
        })

        if (errorResult.isPermissionError) {
          console.log('Permission error detected, trying alternative approach')
        }

        // If the main API fails, try without the course parameter for standalone generation
        try {
          console.log('Trying standalone document generation without course context')
          const effectiveName = isAdoption
            ? (props.complianceOfficerName || props.certificationData?.name || 'User')
            : (props.certificationData?.name || 'User')

          response = await call("lms.overrides.documents.generate_dynamic_docx", {
            name: effectiveName,
            course: null,
            font_path: null,
            document_type: docItem.name,
            use_print_format: true
          })
          console.log('Standalone generation response:', response)
        } catch (standaloneError) {
          console.error('Standalone generation also failed:', standaloneError)

          // Handle the standalone error
          const standaloneErrorResult = handleApiError(standaloneError, {
            showToast: false,
            context: `Standalone generation of ${docItem.name}`
          })

          throw new Error(standaloneErrorResult.message)
        }
      }
    }

    // Check if we have a valid response with file content
    if (response && response.file_content) {
      toast.success("Processing document...")

      // Determine file name and type from response or defaults
      const fileName = response.file_name || `${docItem.name.replace(/\s+/g, '_')}.pdf`

      // Download the file using the existing directDownload function
      await directDownload(response.file_content, fileName)

      // Mark as downloaded
      emit('download-complete', docItem.name)

      toast.success(`${documentLabel} downloaded successfully`)
    } else if (response?.success === false) {
      // Handle API error response
      const errorMsg = response.message || response.error || `Failed to generate ${documentLabel}`
      throw new Error(errorMsg)
    } else {
      // If no valid response, throw error
      throw new Error(`Failed to generate ${documentLabel}. Please ensure you have completed the course and all required information is available.`)
    }
  } catch (error) {
    console.error('Download error:', error)

    // Provide more specific error messages
    let errorMessage = error.message
    if (error.message?.includes('required information') || error.message?.includes('missing')) {
      errorMessage = 'Please ensure all your profile information is complete before downloading documents.'
    } else if (error.message?.includes('not found')) {
      errorMessage = 'Document template not found. Please contact support.'
    } else if (error.message?.includes('not enrolled')) {
      errorMessage = 'You must be enrolled in the course to download documents.'
    } else if (error.message?.includes('progress')) {
      errorMessage = 'Please complete the course before downloading documents.'
    } else if (error.message?.includes('permission') || error.message?.includes('403')) {
      errorMessage = 'You do not have permission to download this document. Please contact support.'
    }

    downloadError.value = `Failed to download ${documentLabel}: ${errorMessage}`
    toast.error(errorMessage)
  } finally {
    downloadingDocuments.value.delete(docItem.name)
  }
}

// Helper function to check if submission status has documents ready
const checkDocumentAvailability = async () => {
  try {
    const response = await call('lms.overrides.documents.has_user_submited_document', {
      course: props.courseName
    })
    return response
  } catch (error) {
    console.error('Error checking document availability:', error)
    return null
  }
}

// Helper function to get proper document type mappings
const getDocumentPrintFormat = (documentName) => {
  // Map document names to their corresponding print format names
  const printFormatMap = {
    'Meril Distributor Compliance Policy Adoption Form': 'Meril Distributor Compliance Policy Adoption Form',
    'Distributor Self Declaration': 'Distributor Self Declaration',
    'Meril Distributor Compliance Code of Conduct': 'Meril Distributor Compliance Code of Conduct',
    'Distributor Completion Certificate': 'Distributor Completion Certificate',
    'Meril Distributor Compliance Policy for Endo': 'Meril Distributor Compliance Policy',
    'Meril Distributor Compliance Policy': 'Meril Distributor Compliance Policy'
  }

  return printFormatMap[documentName] || documentName
}

// Helper function to convert blob to base64
const blobToBase64 = (blob) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = (error) => {
      console.error("FileReader error:", error)
      reject(error)
    }
    reader.readAsDataURL(blob)
  })
}

// Helper function to fetch document as base64
const fetchDocumentAsBase64 = async (url) => {
  try {
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': '*/*'
      }
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const blob = await response.blob()
    return blobToBase64(blob)
  } catch (error) {
    console.error("Error fetching document as base64:", error)
    throw error
  }
}

// Helper function for downloading (copied from original modal)
const directDownload = async (url, fileName) => {
  // Check if running in WebView
  if (window.nativeInterface && window.isApp) {
    try {
      // Check if url is already base64 content
      let base64Content
      if (url.startsWith('data:') || (!url.startsWith('http') && !url.startsWith('/'))) {
        base64Content = url
      } else {
        base64Content = await fetchDocumentAsBase64(url)
      }

      const mimeType = fileName?.endsWith('.pdf') ? 'application/pdf' :
                      fileName?.endsWith('.docx') ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' :
                      'application/octet-stream'

      const result = await window.nativeInterface.execute("downloadFile", {
        base64: base64Content,
        name: fileName,
        mimeType
      })

      if (result.success) {
        toast.success("Document sent to device for download")
      } else {
        toast.error("Download failed. Please try again.")
      }
    } catch (error) {
      console.error("Error downloading in WebView:", error)
      toast.error("Download failed. Please try again.")
      // Fallback: try opening in new window
      window.open(url, '_blank')
    }
  } else {
    // Regular browser download
    const link = document.createElement('a')

    // Check if url is already base64 content
    if (!url.startsWith('http') && !url.startsWith('/')) {
      // Convert base64 to blob URL for download
      const mimeType = fileName?.endsWith('.pdf') ? 'application/pdf' :
                      fileName?.endsWith('.docx') ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' :
                      'application/octet-stream'
      const byteCharacters = atob(url)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: mimeType })
      link.href = URL.createObjectURL(blob)
    } else {
      link.href = url
    }

    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // Clean up blob URL if created
    if (link.href.startsWith('blob:')) {
      URL.revokeObjectURL(link.href)
    }
  }
}

// Watch for changes in completed downloads to clear errors
watch(() => props.completedDownloads.size, () => {
  if (downloadError.value) {
    downloadError.value = ''
  }
})
</script>
