<template>
  <div class="dropzone-upload-container">
    <div ref="dropzoneElement" class="dropzone-area" :class="{ 'dropzone-dragging': isDragging }">
      <div v-if="!currentFile" class="dropzone-placeholder">
        <FileUp class="w-10 h-10 text-gray-400 mb-3" />
        <p class="text-lg font-medium text-gray-700 mb-1">
          Drop your file here or click to browse
        </p>
        <p class="text-sm text-gray-500">
          Supports files up to 1GB. Video formats: MP4, MOV, AVI, MKV, WEBM
        </p>
        <p class="text-sm text-gray-500">Other formats: Images, PDFs, Audio files</p>
      </div>

      <div v-else class="dropzone-content">
        <div v-if="previewType !== 'none'" class="file-preview">
          <img
            v-if="previewType === 'image'"
            :src="filePreviewUrl"
            :alt="currentFile.name"
            class="file-preview-media"
          />
          <video
            v-else-if="previewType === 'video'"
            :src="filePreviewUrl"
            controls
            playsinline
            class="file-preview-media"
          ></video>
          <audio
            v-else-if="previewType === 'audio'"
            :src="filePreviewUrl"
            controls
            class="file-preview-audio"
          ></audio>
          <div v-else class="file-preview-fallback">
            <FileUp class="w-10 h-10 text-gray-400 mb-2" />
            <p class="text-sm text-gray-600">Preview not available</p>
          </div>
        </div>

        <!-- Upload Progress -->
        <div v-if="!uploadComplete" class="upload-progress">
          <div class="flex items-center justify-between mb-2">
            <div class="flex-1 text-left">
              <p class="text-sm font-medium text-gray-700">{{ currentFile.name }}</p>
              <p class="text-xs text-gray-500">
                {{ formatFileSize(currentFile.size) }} • {{ getFileType(currentFile.type) }}
              </p>
            </div>
            <Button v-if="!uploadComplete" variant="ghost" size="sm" @click="cancelUpload">
              Cancel
            </Button>
          </div>

          <div class="mb-2">
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>{{ Math.round(uploadProgress) }}%</span>
              <span v-if="uploadSpeed">{{ uploadSpeed }}</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-blue-500 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${uploadProgress}%` }"
              ></div>
            </div>
          </div>

          <div v-if="chunksInfo" class="text-xs text-gray-500 text-left">
            Chunk {{ chunksInfo.currentChunk }} of {{ chunksInfo.totalChunks }}
            <span v-if="estimatedTime"> • {{ estimatedTime }} remaining</span>
          </div>
        </div>

        <!-- Upload Complete -->
        <div v-else class="upload-complete">
          <CheckCircle class="w-10 h-10 text-green-500 mb-2" />
          <p class="text-sm font-medium text-gray-700">Upload complete!</p>
          <p class="text-xs text-gray-500">{{ currentFile?.name }}</p>
          <Button variant="subtle" size="sm" class="mt-3" @click="resetUpload">
            Upload Another File
          </Button>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <ErrorMessage v-if="errorMessage" :message="errorMessage" class="mt-2" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Dropzone from 'dropzone'
import { Button, ErrorMessage } from 'frappe-ui'
import { FileUp, CheckCircle } from 'lucide-vue-next'
import { createResource } from 'frappe-ui'

// Disable auto-discover for all elements
Dropzone.autoDiscover = false

const props = defineProps({
  acceptedFiles: {
    type: String,
    default: 'image/*,video/*,audio/*,.pdf'
  },
  maxFilesize: {
    type: Number,
    default: 1024 // 1GB in MB
  },
  chunkSize: {
    type: Number,
    default: 2 * 1024 * 1024 // 2MB in bytes
  },
  uploadUrl: {
    type: String,
    default: '/api/method/lms.overrides.documents.upload_chunked'
  },
  headers: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['uploadComplete', 'uploadError', 'uploadProgress'])

// Refs
const dropzoneElement = ref(null)
const dropzoneInstance = ref(null)
const isDragging = ref(false)
const currentFile = ref(null)
const uploadProgress = ref(0)
const uploadComplete = ref(false)
const errorMessage = ref('')
const chunksInfo = ref(null)
const uploadSpeed = ref('')
const estimatedTime = ref('')
const uploadStartTime = ref(null)
const bytesUploaded = ref(0)
const filePreviewUrl = ref('')
const previewType = ref('none')

// Initialize Dropzone
onMounted(() => {
  if (!dropzoneElement.value) return

  dropzoneInstance.value = new Dropzone(dropzoneElement.value, {
    url: props.uploadUrl,
    maxFilesize: props.maxFilesize,
    chunking: true,
    forceChunking: true,
    chunkSize: props.chunkSize,
    parallelChunkUploads: true,
    retryChunks: true,
    retryChunksLimit: 3,
    acceptedFiles: props.acceptedFiles,
    autoProcessQueue: true,
    maxFiles: 1,
    headers: {
      'X-Frappe-CSRF-Token': window.csrf_token || '',
      ...props.headers
    },

    // Disable default UI elements
    clickable: true,
    previewsContainer: false,

    // Custom parameters for chunked upload
    params: (files, xhr, chunk) => {
      if (chunk) {
        return {
          dzuuid: chunk.file.upload.uuid,
          dzchunkindex: chunk.index,
          dztotalfilesize: chunk.file.size,
          dzchunksize: props.chunkSize,
          dztotalchunkcount: chunk.file.upload.totalChunkCount,
          dzchunkbyteoffset: chunk.index * props.chunkSize,
          filename: chunk.file.name,
          file_type: chunk.file.type
        }
      }
      return {}
    }
  })

  // Event handlers
  dropzoneInstance.value.on('addedfile', handleFileAdded)
  dropzoneInstance.value.on('uploadprogress', handleUploadProgress)
  dropzoneInstance.value.on('success', handleUploadSuccess)
  dropzoneInstance.value.on('error', handleUploadError)
  dropzoneInstance.value.on('sending', handleSending)
  dropzoneInstance.value.on('chunksUploaded', handleChunksUploaded)
  dropzoneInstance.value.on('canceled', handleCanceled)

  // Drag events
  dropzoneInstance.value.on('dragenter', () => { isDragging.value = true })
  dropzoneInstance.value.on('dragleave', () => { isDragging.value = false })
  dropzoneInstance.value.on('drop', () => { isDragging.value = false })
})

// Cleanup on unmount
onUnmounted(() => {
  clearPreview()
  if (dropzoneInstance.value) {
    dropzoneInstance.value.destroy()
  }
})

// Event Handlers
function handleFileAdded(file) {
  clearPreview()
  currentFile.value = file
  uploadComplete.value = false
  errorMessage.value = ''
  uploadProgress.value = 0
  uploadStartTime.value = Date.now()
  bytesUploaded.value = 0

  // Validate file size
  if (file.size > props.maxFilesize * 1024 * 1024) {
    errorMessage.value = `File size exceeds maximum limit of ${props.maxFilesize}MB`
    dropzoneInstance.value.removeFile(file)
    currentFile.value = null
    return
  }

  // Calculate total chunks
  const totalChunks = Math.ceil(file.size / props.chunkSize)
  chunksInfo.value = {
    currentChunk: 0,
    totalChunks: totalChunks
  }

  setPreviewForFile(file)
}

function handleUploadProgress(file, progress, bytesSent) {
  uploadProgress.value = progress
  bytesUploaded.value = bytesSent

  // Calculate upload speed
  if (uploadStartTime.value) {
    const elapsedSeconds = (Date.now() - uploadStartTime.value) / 1000
    if (elapsedSeconds > 0) {
      const speed = bytesSent / elapsedSeconds
      uploadSpeed.value = formatSpeed(speed)

      // Calculate estimated time
      const remainingBytes = file.size - bytesSent
      const estimatedSeconds = remainingBytes / speed
      estimatedTime.value = formatTime(estimatedSeconds)
    }
  }

  // Update chunk info
  if (file.upload && chunksInfo.value) {
    const currentChunk = Math.floor(bytesSent / props.chunkSize) + 1
    chunksInfo.value.currentChunk = Math.min(currentChunk, chunksInfo.value.totalChunks)
  }

  emit('uploadProgress', { file, progress, bytesSent })
}

function handleSending(file, xhr, formData) {
  // Add any additional form data if needed
  formData.append('doctype', 'File')
  formData.append('folder', 'Home/LMS Uploads')
}

function handleChunksUploaded(file, done) {
  // All chunks uploaded, finalize on server
  const finalizeResource = createResource({
    url: '/api/method/lms.overrides.documents.finalize_chunked_upload',
    params: {
      uuid: file.upload.uuid,
      filename: file.name,
      file_type: file.type,
      total_size: file.size
    },
    onSuccess(data) {
      file.serverResponse = data
      done()
    },
    onError(error) {
      handleUploadError(file, error.message)
    }
  })

  finalizeResource.reload()
}

function handleUploadSuccess(file, response) {
  uploadComplete.value = true
  uploadProgress.value = 100

  // Parse response if it's a string
  let responseData = response
  if (typeof response === 'string') {
    try {
      responseData = JSON.parse(response)
    } catch (e) {
      console.error('Failed to parse response:', e)
    }
  }

  emit('uploadComplete', {
    file: file,
    response: responseData,
    fileUrl: responseData.file_url || responseData.message?.file_url
  })
}

function handleUploadError(file, errorMsg) {
  errorMessage.value = errorMsg || 'Upload failed. Please try again.'
  uploadProgress.value = 0
  clearPreview()
  currentFile.value = null

  emit('uploadError', { file, error: errorMsg })
}

function handleCanceled(file) {
  clearPreview()
  currentFile.value = null
  uploadProgress.value = 0
  chunksInfo.value = null
  uploadSpeed.value = ''
  estimatedTime.value = ''
}

// Actions
function cancelUpload() {
  if (dropzoneInstance.value && currentFile.value) {
    dropzoneInstance.value.removeFile(currentFile.value)
  }
  clearPreview()
}

function resetUpload() {
  currentFile.value = null
  uploadComplete.value = false
  uploadProgress.value = 0
  errorMessage.value = ''
  chunksInfo.value = null
  uploadSpeed.value = ''
  estimatedTime.value = ''
  bytesUploaded.value = 0
  clearPreview()

  if (dropzoneInstance.value) {
    dropzoneInstance.value.removeAllFiles()
  }
}

// Utility functions
function formatFileSize(bytes) {
  const sizes = ['B', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 B'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

function formatSpeed(bytesPerSecond) {
  const speed = formatFileSize(bytesPerSecond)
  return `${speed}/s`
}

function formatTime(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`
}

function getFileType(mimeType) {
  if (mimeType.startsWith('video/')) return 'Video'
  if (mimeType.startsWith('image/')) return 'Image'
  if (mimeType.startsWith('audio/')) return 'Audio'
  if (mimeType.includes('pdf')) return 'PDF'
  return 'File'
}

function setPreviewForFile(file) {
  if (!file) return

  const type = file.type || ''
  const name = file.name || ''

  if (type.startsWith('image/')) {
    filePreviewUrl.value = URL.createObjectURL(file)
    previewType.value = 'image'
    return
  }

  if (type.startsWith('video/')) {
    filePreviewUrl.value = URL.createObjectURL(file)
    previewType.value = 'video'
    return
  }

  if (type.startsWith('audio/')) {
    filePreviewUrl.value = URL.createObjectURL(file)
    previewType.value = 'audio'
    return
  }

  if (name.toLowerCase().endsWith('.pdf')) {
    previewType.value = 'file'
    return
  }

  previewType.value = 'file'
}

function clearPreview() {
  if (filePreviewUrl.value) {
    URL.revokeObjectURL(filePreviewUrl.value)
  }
  filePreviewUrl.value = ''
  previewType.value = 'none'
}

// Expose methods for parent component
defineExpose({
  resetUpload,
  cancelUpload
})
</script>

<style scoped>
.dropzone-upload-container {
  width: 100%;
}

.dropzone-area {
  border: 2px dashed #cbd5e0;
  border-radius: 0.5rem;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f7fafc;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 1.5rem;
}

.dropzone-area:hover {
  border-color: #4299e1;
  background-color: #ebf8ff;
}

.dropzone-dragging {
  border-color: #3182ce;
  background-color: #bee3f8;
}

.dropzone-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  width: 100%;
}

.file-preview {
  width: 100%;
  display: flex;
  justify-content: center;
}

.file-preview-media {
  max-width: 100%;
  max-height: 280px;
  border-radius: 0.75rem;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.15);
}

.file-preview-audio {
  width: 100%;
}

.file-preview-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #4a5568;
}

.upload-progress,
.upload-complete {
  width: 100%;
  max-width: 400px;
}

.upload-complete {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Override Dropzone default styles */
.dropzone-area.dz-clickable {
  cursor: pointer;
}

.dropzone-area.dz-started .dropzone-placeholder {
  display: none;
}
</style>
