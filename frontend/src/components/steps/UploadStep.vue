<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h3 class="text-lg font-medium text-gray-900 mb-2">
        Upload Completed Documents
      </h3>
      <p class="text-sm text-gray-600">
        Upload your signed and completed documents to complete the compliance process.
      </p>
    </div>

    <!-- Instructions -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex">
        <svg class="w-5 h-5 text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3">
          <h4 class="text-sm font-medium text-blue-800">Upload Instructions</h4>
          <div class="text-sm text-blue-700 mt-1 space-y-1">
            <p><strong>Required Documents:</strong> Must be completed forms and declarations</p>
            <p><strong>Policy Documents:</strong> Required - Upload signed policy documents</p>
            <p><strong>File Formats:</strong> .doc, .docx, or .pdf files only (Max 4MB each)</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload Progress Overview -->
    <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-sm font-medium text-gray-900">Upload Progress</h4>
        <span class="text-sm font-medium text-gray-700">
          {{ uploadedDocuments.size }} of {{ uploadableDocuments.length }} completed
        </span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-gray-900 h-2 rounded-full transition-all duration-300"
          :style="{ width: `${overallProgress}%` }"
        ></div>
      </div>
    </div>

    <!-- Current Document Upload -->
    <div v-if="currentDocument" class="bg-white border border-gray-200 rounded-lg p-6">
      <div class="text-center mb-4">
        <h4 class="text-lg font-medium text-gray-900 mb-2">
          {{ getDocumentLabel(currentDocument) }}
        </h4>
        <p class="text-sm text-gray-600">
          {{ getDocumentUploadInstructions(currentDocument.name) }}
        </p>

        <!-- Special note for policy documents -->
        <div v-if="isPolicyDocument(currentDocument.name)" class="mt-2">
          <div class="bg-yellow-50 border border-yellow-200 rounded p-2">
            <p class="text-xs text-yellow-800">
              <strong>Note:</strong> Policy documents must be signed PDF files.
            </p>
          </div>
        </div>
      </div>

      <!-- Upload Form -->
      <form @submit.prevent="handleUpload" class="max-w-md mx-auto space-y-4">
        <!-- File Input -->
        <div>
          <label for="document-upload" class="block text-sm font-medium text-gray-700 mb-2">
            Select Document File <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              id="document-upload"
              ref="fileInput"
              type="file"
              @change="onFileChange"
              accept=".docx,.doc,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,application/pdf"
              class="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-900 hover:file:bg-gray-100 transition"
              required
            />
            <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-1">
            Supported formats: .docx, .doc, .pdf (Max size: 4MB)
          </p>
        </div>

        <!-- File Size Warning -->
        <div v-if="fileSizeError" class="bg-red-50 border border-red-200 rounded-lg p-3">
          <p class="text-sm text-red-700">{{ fileSizeError }}</p>
        </div>

        <!-- Upload Progress -->
        <div v-if="isUploading" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-600">Uploading...</span>
            <span class="font-medium">{{ currentUploadProgress }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${currentUploadProgress}%` }"
            ></div>
          </div>
        </div>

        <!-- Upload Button -->
        <Button
          type="submit"
          theme="gray"
          variant="solid"
          class="w-full"
          :disabled="!selectedFile || isUploading"
        >
          <Spinner v-if="isUploading" class="w-4 h-4 mr-2" />
          {{ isUploading ? 'Uploading...' : 'Upload Document' }}
        </Button>
      </form>

      <!-- Upload Error -->
      <div v-if="uploadError" class="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
        <div class="flex">
          <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3">
            <h4 class="text-sm font-medium text-red-800">Upload Failed</h4>
            <p class="text-sm text-red-700 mt-1">{{ uploadError }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Completed Uploads -->
    <div v-if="uploadedDocuments.size > 0" class="space-y-3">
      <h4 class="text-sm font-medium text-gray-900">Completed Uploads</h4>
      <div class="space-y-2">
        <div
          v-for="documentName in Array.from(uploadedDocuments)"
          :key="documentName"
          class="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg p-3"
        >
          <div class="flex items-center">
            <svg class="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
            <div>
              <p class="text-sm font-medium text-green-900">{{ getLabelForName(documentName) }}</p>
              <p class="text-xs text-green-700">Successfully uploaded</p>
            </div>
          </div>
          <div class="text-green-600">
            <span class="text-xs font-medium">100%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Required Documents Section -->
    <div v-if="requiredUserDocuments.filter(doc => !uploadedDocuments.has(doc.name)).length > 0" class="space-y-3">
      <h4 class="text-sm font-medium text-gray-900">Required Compliance Documents</h4>
      <div class="space-y-2">
        <div
          v-for="document in requiredUserDocuments.filter(doc => !uploadedDocuments.has(doc.name))"
          :key="document.name"
          class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg p-3"
        >
          <div class="flex items-center">
            <svg class="w-5 h-5 text-red-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ getDocumentLabel(document) }}</p>
              <p class="text-xs text-red-600">Required - Pending upload</p>
            </div>
          </div>
          <div class="text-red-400">
            <span class="text-xs font-medium">Required</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Policy Documents Section -->
    <div v-if="policyDocuments.filter(doc => !uploadedDocuments.has(doc.name)).length > 0" class="space-y-3">
      <h4 class="text-sm font-medium text-gray-900">Policy Documents (Required)</h4>
      <p class="text-xs text-gray-600">Upload signed policy documents - these are mandatory for compliance</p>
      <div class="space-y-2">
        <div
          v-for="document in policyDocuments.filter(doc => !uploadedDocuments.has(doc.name))"
          :key="document.name"
          class="flex items-center justify-between bg-red-50 border border-red-200 rounded-lg p-3"
        >
          <div class="flex items-center">
            <svg class="w-5 h-5 text-red-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ getDocumentLabel(document) }}</p>
              <p class="text-xs text-red-600">Required - PDF only</p>
            </div>
          </div>
          <div class="text-red-400">
            <span class="text-xs font-medium">Required</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Completion Message -->
    <div v-if="allUploadsCompleted" class="bg-green-50 border border-green-200 rounded-lg p-4">
      <div class="flex">
        <svg class="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3">
          <h4 class="text-sm font-medium text-green-800">All Documents Uploaded</h4>
          <p class="text-sm text-green-700 mt-1">
            Congratulations! All required documents have been successfully uploaded. You can now proceed to the completion step.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Button, Spinner, call, toast } from 'frappe-ui'

const props = defineProps({
  requiredDocuments: {
    type: Array,
    default: () => []
  },
  uploadedDocuments: {
    type: Set,
    default: () => new Set()
  },
  currentDocument: {
    type: Object,
    default: null
  },
  courseName: {
    type: String,
    default: ''
  },
  uploadProgress: {
    type: Object,
    default: () => ({})
  },
  userRole: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['upload-complete', 'upload-progress'])

const fileInput = ref(null)
const selectedFile = ref(null)
const isUploading = ref(false)
const uploadError = ref('')
const fileSizeError = ref('')

const uploadableDocuments = computed(() => {
  // Include all documents that can be uploaded (forms and policy documents)
  return props.requiredDocuments.filter(doc => {
    // Always include user-generated documents
    if (!doc.downloadOnly) return true

    // Include policy documents as uploadable options
    const policyDocuments = [
      'Meril Distributor Compliance Policy',
      'Meril Distributor Compliance Policy for Endo'
    ]
    return policyDocuments.includes(doc.name)
  })
})

// Separate required user documents from optional policy documents
const requiredUserDocuments = computed(() => {
  const userDocTypes = [
    'Meril Distributor Compliance Policy Adoption Form',
    'Distributor Self Declaration',
    'Meril Distributor Compliance Code of Conduct'
  ]
  return uploadableDocuments.value.filter(doc => userDocTypes.includes(doc.name))
})

const policyDocuments = computed(() => {
  const policyDocTypes = [
    'Meril Distributor Compliance Policy',
    'Meril Distributor Compliance Policy for Endo'
  ]
  return uploadableDocuments.value.filter(doc => policyDocTypes.includes(doc.name))
})

const overallProgress = computed(() => {
  const uploadableCount = uploadableDocuments.value.length
  if (uploadableCount === 0) return 0
  return Math.round((props.uploadedDocuments.size / uploadableCount) * 100)
})

const currentUploadProgress = computed(() => {
  if (!props.currentDocument) return 0
  return props.uploadProgress[props.currentDocument.name] || 0
})

const allUploadsCompleted = computed(() => {
  const uploadableCount = uploadableDocuments.value.length
  return uploadableCount > 0 && props.uploadedDocuments.size >= uploadableCount
})

const remainingDocuments = computed(() => {
  // Only show uploadable documents that haven't been uploaded yet
  return uploadableDocuments.value.filter(doc => !props.uploadedDocuments.has(doc.name))
})

// Helper functions
const getDocumentLabel = (document) => document?.label || document?.name

const documentLabelMap = computed(() => {
  const map = new Map()
  props.requiredDocuments.forEach(doc => {
    map.set(doc.name, getDocumentLabel(doc))
  })
  return map
})

const getLabelForName = (name) => documentLabelMap.value.get(name) || name

const isPolicyDocument = (documentName) => {
  const policyDocTypes = [
    'Meril Distributor Compliance Policy',
    'Meril Distributor Compliance Policy for Endo'
  ]
  return policyDocTypes.includes(documentName)
}

const getDocumentUploadInstructions = (documentName) => {
  if (isPolicyDocument(documentName)) {
    return 'Upload the signed policy document as a PDF file.'
  }
  return 'Please upload your signed and completed document.'
}

const onFileChange = (event) => {
  const file = event.target.files[0]
  fileSizeError.value = ''
  uploadError.value = ''

  if (!file) {
    selectedFile.value = null
    return
  }

  // Check file size (4MB limit)
  const maxSize = 4 * 1024 * 1024 // 4MB
  if (file.size > maxSize) {
    fileSizeError.value = 'File size must be less than 4MB'
    selectedFile.value = null
    event.target.value = '' // Reset file input
    return
  }

  // Check file type - stricter validation for policy documents
  if (isPolicyDocument(props.currentDocument?.name)) {
    // Policy documents must be PDF only
    if (file.type !== 'application/pdf' && !file.name.match(/\.pdf$/i)) {
      fileSizeError.value = 'Policy documents must be PDF files only'
      selectedFile.value = null
      event.target.value = '' // Reset file input
      return
    }
  } else {
    // Regular documents can be DOC, DOCX, or PDF
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
      'application/msword', // .doc
      'application/pdf' // .pdf
    ]
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(docx?|pdf)$/i)) {
      fileSizeError.value = 'Only .doc, .docx, and .pdf files are allowed'
      selectedFile.value = null
      event.target.value = '' // Reset file input
      return
    }
  }

  selectedFile.value = file
}

const handleUpload = async () => {
  if (!selectedFile.value || !props.currentDocument) return

  try {
    isUploading.value = true
    uploadError.value = ''

    // Convert file to base64
    const base64Data = await fileToBase64(selectedFile.value)

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      const current = props.uploadProgress[props.currentDocument.name] || 0
      if (current < 90) {
        emit('upload-progress', props.currentDocument.name, current + 10)
      }
    }, 100)

    // Upload the document using the appropriate function based on user role
    const uploadFunction = props.userRole === 'Employee'
      ? 'lms.overrides.documents.save_user_course_document_with_file'
      : 'lms.overrides.documents.upload_distributor_document_with_datetime'

    const uploadParams = {
      course: props.courseName,
      document_name: props.currentDocument.name,
      filename: selectedFile.value.name,
      base64_file_data: base64Data,
      is_private: 1
    }

    // Add additional parameters for distributor uploads
    if (props.userRole !== 'Employee') {
      uploadParams.document_upload_datetime = new Date().toISOString()
      uploadParams.uploadDocumentName = props.currentDocument.name
    }

    const response = await call(uploadFunction, uploadParams)

    clearInterval(progressInterval)

    if (response.success) {
      // Complete the progress
      emit('upload-progress', props.currentDocument.name, 100)

      // Mark as uploaded, passing file info for the completion step
      emit('upload-complete', props.currentDocument.name, {
        file_url: response.file_url,
        file_name: response.file_name,
        upload_datetime: new Date().toISOString()
      })

      // Reset form
      selectedFile.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }

      toast.success('Document uploaded successfully')
    } else {
      throw new Error(response.message || 'Upload failed')
    }
  } catch (error) {
    console.error('Upload error:', error)
    uploadError.value = error.message || 'Upload failed'
    toast.error('Upload failed')
  } finally {
    isUploading.value = false
  }
}

// Helper function to convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const base64 = reader.result.split(',')[1]
        const cleanBase64 = base64.replace(/[^A-Za-z0-9+/=]/g, '')
        resolve(cleanBase64)
      } catch (error) {
        reject(error)
      }
    }
    reader.onerror = error => reject(error)
    reader.readAsDataURL(file)
  })
}

// Watch for changes in current document to reset form
watch(() => props.currentDocument, () => {
  selectedFile.value = null
  uploadError.value = ''
  fileSizeError.value = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
})
</script>
