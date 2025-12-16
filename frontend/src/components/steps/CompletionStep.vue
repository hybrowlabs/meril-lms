<template>
  <div class="space-y-6">
    <!-- Success Header -->
    <div class="text-center">
      <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
        <svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">
        Process Complete!
      </h3>
      <p class="text-sm text-gray-600">
        All documents have been successfully processed and submitted.
      </p>
    </div>


    <!-- Document List -->
    <div class="space-y-4">
      <h4 class="text-lg font-medium text-gray-900">Your Documents</h4>

      <!-- Uploaded Documents -->
      <div v-if="uploadedDocuments.length > 0" class="space-y-3">
        <h5 class="text-sm font-medium text-gray-700">Uploaded Documents</h5>
        <div class="space-y-2">
          <div
            v-for="document in uploadedDocuments"
            :key="document.name"
            class="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
          >
            <div class="flex items-center">
              <div class="flex-shrink-0 w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V8zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2z" clip-rule="evenodd" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-900">{{ getLabelForName(document.name) }}</p>
                <p class="text-xs text-gray-500">
                  Uploaded: {{ formatDateTime(document.upload_datetime) }}
                </p>
              </div>
            </div>
            <Button
              theme="gray"
              variant="outline"
              size="md"
              icon="download"
              label="Download"
              @click="downloadDocument(document)"
              :disabled="downloadingDocuments.has(document.name)"
              class="h-12 px-6 py-3 min-w-[120px] text-sm font-medium inline-flex items-center justify-center gap-2 download-btn-override"
            >
              <Spinner v-if="downloadingDocuments.has(document.name)" class="w-4 h-4 flex-shrink-0" />
            </Button>
          </div>
        </div>
      </div>

      <!-- Available Documents -->
      <div v-if="availableDocuments.length > 0" class="space-y-3">
        <h5 class="text-sm font-medium text-gray-700">Available Documents</h5>
        <div class="space-y-2">
          <div
            v-for="document in availableDocuments"
            :key="document"
            class="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
          >
            <div class="flex items-center">
              <div class="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V8zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2z" clip-rule="evenodd" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-900">{{ getLabelForName(document) }}</p>
                <p class="text-xs text-gray-500">System generated document</p>
              </div>
            </div>
            <Button
              theme="gray"
              variant="outline"
              size="md"
              icon="download"
              label="Download"
              @click="downloadSystemDocument(document)"
              :disabled="downloadingDocuments.has(document)"
              class="h-12 px-6 py-3 min-w-[120px] text-sm font-medium inline-flex items-center justify-center gap-2 download-btn-override"
            >
              <Spinner v-if="downloadingDocuments.has(document)" class="w-4 h-4 flex-shrink-0" />
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk Download -->
    <div v-if="totalDocuments > 1" class="border-t border-gray-200 pt-6">
      <Button
        theme="gray"
        variant="solid"
        class="w-full inline-flex items-center justify-center h-14 px-8 py-4 text-base font-semibold gap-3 download-btn-override"
        @click="downloadAllDocuments"
        :disabled="isDownloadingAll"
      >
        <span class="whitespace-nowrap flex-shrink-0">{{ isDownloadingAll ? 'Downloading All Documents...' : 'Download All Documents' }}</span>
      </Button>
    </div>
    

    <!-- Next Steps -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex">
        <svg class="w-5 h-5 text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3">
          <h4 class="text-sm font-medium text-blue-800">What's Next?</h4>
          <div class="text-sm text-blue-700 mt-1">
            <ul class="list-disc list-inside space-y-1">
              <li>Your documents have been submitted for review</li>
              <li>You can download copies of all documents at any time</li>
              <li>Keep copies of signed documents for your records</li>
              <li>Check back for any additional compliance requirements</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Download Error -->
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
import { ref, computed } from 'vue'
import { Button, Spinner, toast } from 'frappe-ui'

const props = defineProps({
  uploadedDocuments: {
    type: Array,
    default: () => []
  },
  requiredDocuments: {
    type: Array,
    default: () => []
  },
  documentsList: {
    type: Array,
    default: () => []
  },
  courseName: {
    type: String,
    default: ''
  },
  courseDocumentsRecordId: {
    type: String,
    default: null
  },
  doctype: {
    type: String,
    default: 'Distributor Course Documents'
  },
  userRole: {
    type: String,
    default: 'Distributor'
  }
})

const downloadingDocuments = ref(new Set())
const isDownloadingAll = ref(false)
const downloadError = ref('')

const totalDocuments = computed(() => {
  return props.uploadedDocuments.length + props.documentsList.length
})

const availableDocuments = computed(() => {
  // Filter out documents that are already in uploaded documents
  const uploadedNames = new Set(props.uploadedDocuments.map(doc => doc.name))
  return props.documentsList.filter(doc => !uploadedNames.has(doc))
})

const getDocumentLabel = (document) => document?.label || document?.name

const requiredDocumentLabelMap = computed(() => {
  const map = new Map()
  props.requiredDocuments.forEach(doc => {
    map.set(doc.name, getDocumentLabel(doc))
  })
  return map
})

const getLabelForName = (name) => requiredDocumentLabelMap.value.get(name) || name

const requiredDocumentPrintFormatMap = computed(() => {
  const map = new Map()
  props.requiredDocuments.forEach(doc => {
    const printFormat = doc.printFormat || doc.name
    map.set(doc.name, printFormat)
    if (doc.label) {
      map.set(doc.label, printFormat)
    }
  })
  return map
})

const formatDateTime = (dateString) => {
  if (!dateString) return 'Unknown'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}

const downloadDocument = async (document) => {
  if (downloadingDocuments.value.has(document.name)) return

  try {
    downloadingDocuments.value.add(document.name)
    downloadError.value = ''
    const documentLabel = getLabelForName(document.name)

    if (document.file_url) {
      // Direct download of uploaded file
      const baseUrl = window.location.origin
      const url = document.file_url.startsWith('http') ? document.file_url : `${baseUrl}${document.file_url}`

      // Extract extension from file_url
      const urlPath = document.file_url.split('?')[0]
      const extension = urlPath.substring(urlPath.lastIndexOf('.'))

      const baseName = document.name || 'document'
      const fileName = baseName.includes('.') ?
                     baseName.substring(0, baseName.lastIndexOf('.')) + extension :
                     baseName + extension

      await directDownload(url, fileName)
    } else {
      throw new Error('Document file URL not available')
    }

    toast.success(`${documentLabel} downloaded successfully`)
  } catch (error) {
    console.error('Download error:', error)
    const documentLabel = getLabelForName(document.name)
    downloadError.value = `Failed to download ${documentLabel}: ${error.message}`
    toast.error(`Failed to download ${documentLabel}`)
  } finally {
    downloadingDocuments.value.delete(document.name)
  }
}

const downloadSystemDocument = async (documentName) => {
  if (downloadingDocuments.value.has(documentName)) return

  try {
    downloadingDocuments.value.add(documentName)
    downloadError.value = ''
    const documentLabel = getLabelForName(documentName)
    const printFormat = requiredDocumentPrintFormatMap.value.get(documentName) || documentName

    const baseUrl = window.location.origin

    // Handle compliance policy documents
    if (documentName === "Meril Distributor Compliance Policy") {
      const url = `${baseUrl}/api/method/lms.overrides.documents.download_nonendo_file`
      await directDownload(url, "Meril_Distributor_Compliance_Policy.pdf")
    } else if (documentName === "Meril Distributor Compliance Policy for Endo") {
      const url = `${baseUrl}/api/method/lms.overrides.documents.download_endo_file`
      await directDownload(url, "Meril_Distributor_Compliance_Policy_Endo.pdf")
    } else {
      // Use print format for other documents
      if (!props.courseDocumentsRecordId) {
        throw new Error("Course document record ID not found")
      }

      // Determine the correct doctype based on document name
      let doctype = props.doctype
      if (documentName.includes('Employee') || documentName.includes('employee')) {
        doctype = 'Employee Course Documents'
      }

      const params = new URLSearchParams({
        doctype: doctype,
        name: props.courseDocumentsRecordId,
        format: printFormat,
        no_letterhead: '1',
        letterhead: 'No Letterhead',
        settings: '{}',
        _lang: 'en',
        custom_filename: documentLabel,
        custom_type: 'download'
      })

      const url = `${baseUrl}/api/method/lms.overrides.download_pdf.custom_download_pdf?${params.toString()}`
      const fileName = documentLabel.endsWith('.pdf') ? documentLabel : `${documentLabel}.pdf`
      await directDownload(url, fileName)
    }

    toast.success(`${documentLabel} downloaded successfully`)
  } catch (error) {
    console.error('Download error:', error)
    const documentLabel = getLabelForName(documentName)
    downloadError.value = `Failed to download ${documentLabel}: ${error.message}`
    toast.error(`Failed to download ${documentLabel}`)
  } finally {
    downloadingDocuments.value.delete(documentName)
  }
}

const downloadAllDocuments = async () => {
  if (isDownloadingAll.value) return

  try {
    isDownloadingAll.value = true
    downloadError.value = ''

    toast.success('Starting download of all documents...')

    // Download uploaded documents
    for (const document of props.uploadedDocuments) {
      await downloadDocument(document)
      // Add delay between downloads
      await new Promise(resolve => setTimeout(resolve, 1000))
    }

    // Download system documents
    for (const documentName of availableDocuments.value) {
      await downloadSystemDocument(documentName)
      // Add delay between downloads
      await new Promise(resolve => setTimeout(resolve, 1000))
    }

    toast.success('All documents downloaded successfully')
  } catch (error) {
    console.error('Bulk download error:', error)
    downloadError.value = `Failed to download all documents: ${error.message}`
    toast.error('Failed to download all documents')
  } finally {
    isDownloadingAll.value = false
  }
}

// Helper function for downloading (reused from original modal)
const directDownload = async (url, fileName) => {
  // Check if running in WebView
  if (window.nativeInterface && window.isApp) {
    try {
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

      if (!result.success) {
        throw new Error("WebView download failed")
      }
    } catch (error) {
      console.error("Error downloading in WebView:", error)
      // Fallback: try opening in new window
      window.open(url, '_blank')
    }
  } else {
    // Regular browser download
    const link = document.createElement('a')

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
  } catch (error) {
    console.error("Error fetching document as base64:", error)
    throw error
  }
}
</script>

<style scoped>
/* Override frappe-ui Button truncate class */
.download-btn-override {
  text-overflow: initial !important;
  overflow: visible !important;
  white-space: nowrap !important;
}

/* Ensure the button content doesn't get truncated */
.download-btn-override :deep(.truncate) {
  text-overflow: initial !important;
  overflow: visible !important;
  white-space: nowrap !important;
}
</style>
