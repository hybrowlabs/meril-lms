import AudioBlock from '@/components/AudioBlock.vue'
import VideoBlock from '@/components/VideoBlock.vue'
import UploadPlugin from '@/components/UploadPlugin.vue'
import { h, createApp } from 'vue'
import { Upload as UploadIcon } from 'lucide-vue-next'
import { createDialog } from '@/utils/dialogs'
import translationPlugin from '../translation'

export class Upload {
	constructor({ data, api, readOnly }) {
		this.data = data
		this.readOnly = readOnly
	}

	static get toolbox() {
		const app = createApp({
			render: () =>
				h(UploadIcon, { size: 18, strokeWidth: 1.5, color: 'black' }),
		})

		const div = document.createElement('div')
		app.mount(div)

		return {
			title: 'Upload',
			icon: div.innerHTML,
		}
	}

	static get isReadOnlySupported() {
		return true
	}

	render() {
		this.wrapper = document.createElement('div')

		if (this.data && this.data.file_url) {
			this.renderFile(this.data)
		} else {
			this.renderFileUploader()
		}

		return this.wrapper
	}

	renderFile(file) {
		// Check if it's a video (with fallback to URL extension check)
		if (this.isVideo(file.file_type, file.file_url)) {
			const app = createApp(VideoBlock, {
				file: file.file_url,
				readOnly: this.readOnly,
				quizzes: file.quizzes || [],
				saveQuizzes: (quizzes) => {
					if (this.readOnly) return
					this.data.quizzes = quizzes
				},
			})
			app.use(translationPlugin)
			app.config.globalProperties.$dialog = createDialog
			app.mount(this.wrapper)
			return
		} else if (this.isAudio(file.file_type, file.file_url)) {
			const app = createApp(AudioBlock, {
				file: file.file_url,
			})
			app.mount(this.wrapper)
			return
		} else if (file.file_type == 'PDF' || this.isPDF(file.file_type, file.file_url)) {
			this.wrapper.innerHTML = `<iframe src="${
				window.location.origin
			}${encodeURI(
				file.file_url
			)}" width='100%' height='700px' class="mb-4" type="application/pdf"></iframe>`
			return
		} else {
			this.wrapper.innerHTML = `<img class="mb-4" src=${encodeURI(
				file.file_url
			)} width='100%'>`
			return
		}
	}

	renderFileUploader() {
		const app = createApp(UploadPlugin, {
			onFileUploaded: (file) => {
				this.data.file_url = file.file_url
				this.data.file_type = file.file_type
				this.renderFile(file)
			},
		})
		app.use(translationPlugin)
		app.mount(this.wrapper)
	}

	validate(savedData) {
		if (!savedData.file_url || !savedData.file_type) {
			return false
		}
		return true
	}

	save(blockContent) {
		return {
			file_url: this.data.file_url,
			file_type: this.data.file_type,
			quizzes: this.data.quizzes || [],
		}
	}

	isVideo(type, fileUrl = null) {
		if (!type && !fileUrl) return false
		
		// Check file extension
		const videoExtensions = ['mov', 'mp4', 'avi', 'mkv', 'webm']
		
		if (type) {
			const typeLower = type.toLowerCase()
			
			// Check if it's a video extension
			if (videoExtensions.includes(typeLower)) {
				return true
			}
			
			// Check if it's a MIME type (e.g., 'video/mp4')
			if (typeLower.startsWith('video/')) {
				return true
			}
			
			// Check if it's a generic 'video' type
			if (typeLower === 'video') {
				return true
			}
		}
		
		// Fallback: check file URL extension
		if (fileUrl) {
			const extension = this.getExtensionFromUrl(fileUrl)
			if (extension && videoExtensions.includes(extension.toLowerCase())) {
				return true
			}
		}
		
		return false
	}

	isAudio(type, fileUrl = null) {
		if (!type && !fileUrl) return false
		
		const audioExtensions = ['mp3', 'wav', 'ogg']
		
		if (type) {
			const typeLower = type.toLowerCase()
			
			// Check if it's an audio extension
			if (audioExtensions.includes(typeLower)) {
				return true
			}
			
			// Check if it's a MIME type (e.g., 'audio/mpeg')
			if (typeLower.startsWith('audio/')) {
				return true
			}
			
			// Check if it's a generic 'audio' type
			if (typeLower === 'audio') {
				return true
			}
		}
		
		// Fallback: check file URL extension
		if (fileUrl) {
			const extension = this.getExtensionFromUrl(fileUrl)
			if (extension && audioExtensions.includes(extension.toLowerCase())) {
				return true
			}
		}
		
		return false
	}

	isPDF(type, fileUrl = null) {
		if (!type && !fileUrl) return false
		
		if (type) {
			const typeLower = type.toLowerCase()
			if (typeLower === 'pdf' || typeLower === 'application/pdf') {
				return true
			}
		}
		
		// Fallback: check file URL extension
		if (fileUrl) {
			const extension = this.getExtensionFromUrl(fileUrl)
			if (extension && extension.toLowerCase() === 'pdf') {
				return true
			}
		}
		
		return false
	}

	getExtensionFromUrl(url) {
		if (!url) return null
		
		try {
			// Remove query parameters
			const urlWithoutParams = url.split('?')[0]
			// Get the last part after the last slash
			const filename = urlWithoutParams.split('/').pop()
			// Extract extension
			if (filename && filename.includes('.')) {
				return filename.split('.').pop().toLowerCase()
			}
		} catch (e) {
			// Ignore errors
		}
		
		return null
	}
}
