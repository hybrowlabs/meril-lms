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
          {{ currentDocument.name }}
        </h4>
        <p class="text-sm text-gray-600">
          Please upload your signed and completed document.
        </p>
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
              <p class="text-sm font-medium text-green-900">{{ documentName }}</p>
              <p class="text-xs text-green-700">Successfully uploaded</p>
            </div>
          </div>
          <div class="text-green-600">
            <span class="text-xs font-medium">100%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Remaining Documents -->
    <div v-if="remainingDocuments.length > 0" class="space-y-3">
      <h4 class="text-sm font-medium text-gray-900">Remaining Documents</h4>
      <div class="space-y-2">
        <div
          v-for="document in remainingDocuments"
          :key="document.name"
          class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg p-3"
        >
          <div class="flex items-center">
            <svg class="w-5 h-5 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ document.name }}</p>
              <p class="text-xs text-gray-500">Pending upload</p>
            </div>
          </div>
          <div class="text-gray-400">
            <span class="text-xs">Waiting</span>
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
  }
})

const emit = defineEmits(['upload-complete', 'upload-progress'])

const fileInput = ref(null)
const selectedFile = ref(null)
const isUploading = ref(false)
const uploadError = ref('')
const fileSizeError = ref('')

const uploadableDocuments = computed(() => {
  // Filter out download-only documents
  return props.requiredDocuments.filter(doc => !doc.downloadOnly)
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

  // Check file type
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

    // Upload the document
    const response = await call('lms.overrides.documents.upload_distributor_document_with_datetime', {
      course: props.courseName,
      document_name: props.currentDocument.name,
      filename: selectedFile.value.name,
      base64_file_data: base64Data,
      is_private: 1,
      document_upload_datetime: new Date().toISOString(),
      uploadDocumentName: props.currentDocument.name
    })

    clearInterval(progressInterval)

    if (response.success) {
      // Complete the progress
      emit('upload-progress', props.currentDocument.name, 100)

      // Mark as uploaded
      emit('upload-complete', props.currentDocument.name)

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