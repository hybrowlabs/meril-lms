<template>
	<div>
		<!-- File size detection input -->
		<input
			v-if="!showLargeFileUploader"
			ref="fileInputDetector"
			type="file"
			:accept="acceptedFileTypes"
			@change="handleFileSelection"
			style="display: none"
		/>

		<!-- Frappe UI FileUploader for small files -->
		<FileUploader
			v-if="!showLargeFileUploader && selectedFile"
			:fileTypes="['image/*', 'video/*', 'audio/*', '.pdf']"
			:validateFile="validateFile"
			@success="(data) => addFile(data)"
			ref="fileUploader"
			class="hide"
			:file="selectedFile"
		/>

		<!-- Dropzone for large files -->
		<DropzoneUpload
			v-if="showLargeFileUploader"
			:acceptedFiles="acceptedFileTypes"
			:maxFilesize="1024"
			:chunkSize="2097152"
			@uploadComplete="handleDropzoneUpload"
			@uploadError="handleUploadError"
			ref="dropzoneUploader"
		/>

		<!-- Error display -->
		<div v-if="uploadError" class="mt-2 p-3 bg-red-50 text-red-600 rounded">
			{{ uploadError }}
		</div>
	</div>
</template>
<script setup>
import { FileUploader } from 'frappe-ui'
import DropzoneUpload from './DropzoneUpload.vue'
import { onMounted, ref, nextTick } from 'vue'

const fileUploader = ref(null)
const dropzoneUploader = ref(null)
const fileInputDetector = ref(null)
const showLargeFileUploader = ref(false)
const selectedFile = ref(null)
const uploadError = ref('')
const acceptedFileTypes = 'image/*,video/*,audio/*,.pdf'

// File size threshold (100MB in bytes)
const FILE_SIZE_THRESHOLD = 100 * 1024 * 1024

const emit = defineEmits(['fileUploaded'])

const props = defineProps({
	onFileUploaded: {
		type: Function,
		required: true,
	},
})

onMounted(async () => {
	await nextTick()
	// Click the file detector input to start file selection
	if (fileInputDetector.value) {
		fileInputDetector.value.click()
	}
})

// Handle initial file selection to determine upload method
const handleFileSelection = async (event) => {
	const file = event.target.files[0]
	if (!file) return

	// Validate file type first
	const validationError = validateFile(file)
	if (validationError) {
		uploadError.value = validationError
		return
	}

	uploadError.value = ''

	// Check file size to determine upload method
	if (file.size >= FILE_SIZE_THRESHOLD) {
		// Use Dropzone for large files
		showLargeFileUploader.value = true
		await nextTick()

		// Programmatically add file to Dropzone
		if (dropzoneUploader.value && dropzoneUploader.value.dropzoneInstance) {
			dropzoneUploader.value.dropzoneInstance.addFile(file)
		}
	} else {
		// Use frappe-ui FileUploader for small files
		selectedFile.value = file
		await nextTick()

		// Trigger the FileUploader
		if (fileUploader.value) {
			const fileInput = fileUploader.value.$el.querySelector('input[type="file"]')
			if (fileInput) {
				// Create a new FileList containing our file
				const dataTransfer = new DataTransfer()
				dataTransfer.items.add(file)
				fileInput.files = dataTransfer.files

				// Trigger change event
				const changeEvent = new Event('change', { bubbles: true })
				fileInput.dispatchEvent(changeEvent)
			}
		}
	}
}

// Handle successful upload from Frappe UI FileUploader
const addFile = (file) => {
	props.onFileUploaded({
		file_url: file.file_url,
		file_type: file.file_type,
	})
}

// Handle successful upload from Dropzone
const handleDropzoneUpload = (data) => {
	// Extract file URL from response
	let fileUrl = data.fileUrl || data.response?.file_url || data.response?.message?.file_url

	if (fileUrl) {
		// Extract file type from filename, file object, or file URL
		let fileType = null
		
		// First try to get extension from filename
		if (data.file?.name) {
			fileType = getFileExtension(data.file.name)
		}
		
		// If not available, try to extract from file URL
		if (!fileType && fileUrl) {
			fileType = getFileExtension(fileUrl)
		}
		
		// If still not available, try to extract from MIME type
		if (!fileType && data.file?.type) {
			fileType = getExtensionFromMimeType(data.file.type)
		}
		
		// Fallback to generic type if nothing works
		if (!fileType) {
			fileType = getFileType(data.file?.name || fileUrl)
		}

		props.onFileUploaded({
			file_url: fileUrl,
			file_type: fileType,
		})
	} else {
		uploadError.value = 'Upload succeeded but no file URL received'
	}
}

// Handle upload errors
const handleUploadError = (data) => {
	uploadError.value = data.error || 'Upload failed. Please try again.'
}

// Get file extension from file name or URL
const getFileExtension = (fileNameOrUrl) => {
	if (!fileNameOrUrl) return null
	
	// Extract filename from URL if needed
	let filename = fileNameOrUrl
	if (fileNameOrUrl.includes('/')) {
		// Remove query parameters
		filename = fileNameOrUrl.split('?')[0]
		// Get the last part after the last slash
		filename = filename.split('/').pop()
	}
	
	// Extract extension
	if (filename.includes('.')) {
		return filename.split('.').pop().toLowerCase()
	}
	
	return null
}

// Convert MIME type to file extension
const getExtensionFromMimeType = (mimeType) => {
	if (!mimeType) return null
	
	const mimeToExt = {
		'video/mp4': 'mp4',
		'video/quicktime': 'mov',
		'video/x-msvideo': 'avi',
		'video/x-matroska': 'mkv',
		'video/webm': 'webm',
		'audio/mpeg': 'mp3',
		'audio/wav': 'wav',
		'audio/ogg': 'ogg',
		'application/pdf': 'pdf',
		'image/jpeg': 'jpg',
		'image/png': 'png',
		'image/gif': 'gif',
		'image/webp': 'webp',
	}
	
	return mimeToExt[mimeType.toLowerCase()] || null
}

// Get file type from file name (kept for backward compatibility)
const getFileType = (fileName) => {
	if (!fileName) return 'file'
	const extension = getFileExtension(fileName)
	
	if (!extension) return 'file'
	
	// Return the extension directly instead of generic type
	return extension
}

const validateFile = (file) => {
	let extension = file.name.split('.').pop().toLowerCase()
	const allowedExtensions = ['jpg', 'jpeg', 'png', 'mp4', 'mov', 'mp3', 'pdf', 'avi', 'mkv', 'webm', 'wav', 'ogg']

	if (!allowedExtensions.includes(extension)) {
		return `Only the following file types are allowed: ${allowedExtensions.join(', ')}`
	}

	// Check file size for very large files (> 1GB)
	const maxSize = 1024 * 1024 * 1024 // 1GB
	if (file.size > maxSize) {
		return 'File size must not exceed 1GB'
	}
}

const isVideo = (type) => {
	return ['mov', 'mp4', 'avi', 'mkv', 'webm'].includes(type.toLowerCase())
}

const isAudio = (type) => {
	return ['mp3', 'wav', 'ogg'].includes(type.toLowerCase())
}
</script>
