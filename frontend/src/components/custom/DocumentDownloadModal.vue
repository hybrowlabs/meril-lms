<template>
  <div v-if="show">
    <div v-if="showError">
      <div class="fixed inset-0 z-50 bg-black bg-opacity-50">
        <div class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative">
          <button
        class="absolute top-3 right-3 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="$emit('close')"
        aria-label="Close"
      >
        ×
      </button>
          <h3 class="text-lg font-medium mb-4">Error</h3>
          <p>{{ errorMessage }}</p>
          <Button theme="gray" variant="solid" @click="checkDocumentSubmission">Try again</Button>
        </div>
      </div>
    </div>
  <div v-else-if="loadingScreen">
    <div class="fixed inset-0 z-50 bg-black bg-opacity-50">
        <div class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative">
          <button
        class="absolute top-3 right-3 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="$emit('close')"
        aria-label="Close"
      >
        ×
      </button>
          <p>Loading...</p>
        </div>
      </div>
  </div>
  <div  v-else-if="showDownloadForm" class="fixed inset-0 z-50 bg-black bg-opacity-50">
    <div
      title="Compliance Documents"
      class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative"
    >
      <!-- Close Icon -->
      <button
        class="absolute top-3 right-3 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
        @click="$emit('close')"
        aria-label="Close"
      >
        ×
      </button>
      <h3 class="text-lg font-medium mb-4">Compliance Documents</h3>
      <ul class="space-y-4 mb-2" v-for="document in documentsList" :key="document">
        <li class="flex items-center justify-between">
          <span>{{ document }}</span>
          <a href="/files/cartoon-man-wearing-glasses.jpg" download>
            <Button theme="gray" variant="solid">Download Form</Button>
          </a>
        </li>
      </ul>
    </div>
  </div>

  <!-- Second Modal: Form Modal -->
  <div v-else-if="showUploadForm" class="fixed inset-0 z-50 bg-black bg-opacity-50">
    <div
      class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative"
    >
      <!-- Close Icon -->
      <button
        class="absolute top-3 right-3 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="$emit('close')"
        aria-label="Close"
      >
        ×
      </button>
      <h3 class="text-lg font-medium mb-4">Please Enter Name and Date for Compliance Policy Adoption Form</h3>
      <div v-if="showDownloadForm" class="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
        <strong>✓ Document Submitted</strong> - You have already submitted a document for this course.
      </div>
      <form @submit.prevent="handleDownload">
      <div class="mb-4">
        <label for="name">Name</label>
        <TextInput
            id="name"
            v-model="name"
            type="text"
            placeholder="Name"
            class="w-full rounded-lg border p-2 focus:outline-none focus:ring-2"
            required
          />
     
        <label for="date">Date</label>
        <TextInput
            type="date"
            id="date"
            v-model="date"
            class="w-full rounded-lg border p-2 focus:outline-none focus:ring-2"
            required
          />
      </div>
      <Button theme="gray" variant="solid" class="mb-4" type="submit">Download DOCX</Button>
    </form>
    <form @submit.prevent="uploadDocument">
        <div class="mb-4">
          <label for="signatureType">Signature Type</label>
          <Select
            id="signatureType"
            v-model="signatureType"
            class="w-full rounded-lg border p-2 focus:outline-none focus:ring-2"
                  :options="[
              {
                label: 'Arial',
                value: 'arial',
              },
              {
                label: 'Times New Roman',
                value: 'times-new-roman',
              },
              {
                label: 'Helvetica',
                value: 'helvetica',
              },
              {
                label: 'Georgia',
                value: 'georgia',
              },
              {
                label: 'Verdana',
                value: 'verdana',
              }
            ]"
            required
          />
        </div>
      <div class="mb-4">
       <input type="file" @change="onFileChange" class="w-full" required/>
      </div>
      <Button theme="gray" variant="solid" class="w-full" type="submit">Submit</Button>
      </form>
    </div>
  </div>
</div>
</template>

<script setup>
import { Button } from "frappe-ui";
import { defineProps, defineEmits, ref, watch } from "vue";
import { call , TextInput, Select, toast } from 'frappe-ui'
import { useRoute } from 'vue-router'

const props = defineProps({
  show: Boolean
});


const emit = defineEmits(['close']);


// Second modal state and logic
const showUploadForm = ref(true)
const loadingScreen = ref(false);
const showDownloadForm = ref(false)
const signatureType = ref('')
const showError = ref(false)

const name = ref('')
const date = ref('')
const file = ref(null)
const documentsList = ref([])

const handleDownload = () => {
  //TODO:  validate form and save download  file from server
  alert("Downloading...")
}


const onFileChange = (e) => {
  file.value = e.target.files[0]
}

const route = useRoute()
const courseName = route.params.courseName


watch(() => props.show, (newVal) => {
  if (newVal) {
    checkDocumentSubmission()
  }
})

const checkDocumentSubmission = async () => {
try {
    loadingScreen.value = true
    const res = await call('lms.overrides.documents.has_user_submited_document', { course: courseName })
    console.log("res",res)
    if(res.error){
      showError.value = true
      errorMessage.value = res.error
      toast.error(res.error)
      return
    }
    if (res.submited === true) {
      showDownloadForm.value = true
      showUploadForm.value = false
      documentsList.value = res.documents_list
      console.log('Document already submitted for this course')
    } else {
      showDownloadForm.value = false
      showUploadForm.value = true
    }

    if(showError.value){
      showError.value = false;
    }
  } catch (e) {
    // handle error
    showDownloadForm.value = false
    showUploadForm.value = false
    showError.value = true
    toast.error(e?.exception || 'Error checking document submission')
  } finally {
    loadingScreen.value = false
  }
}

const uploadDocument = async () => {
  console.log("uploadDocument")
  if(!file.value) {
    toast.error("Please select a file")
    return
  }
  if (!signatureType.value) {
    toast.error("Please select a signature type")
    return
  }
  try {

    // Convert file to base64
    const base64Data = await fileToBase64(file.value)
    
    // Call the save_user_course_document_with_file method
    const response = await call('lms.overrides.documents.save_user_course_document_with_file', {
      course: courseName,
      document_name: name.value || file.value.name,
      filename: file.value.name,
      base64_file_data: base64Data,
      is_private: 0,
      signature_type: signatureType.value
    })
    console.log("response", response)
    if (response.message && response.success) {
      toast.success('Document uploaded successfully')
      showUploadForm.value = false
      showDownloadForm.value = true
      // Reset form
      name.value = ''
      date.value = ''
      file.value = null
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]')
      if (fileInput) fileInput.value = ''
    } else {
      toast.error(response?.message || 'Upload failed')
    }
  } catch (error) {
    console.error('Upload error:', error)
    toast.error(error.messages?.[0] || 'Upload failed')
  }
}

// Helper function to convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        // Get the base64 string without the data URL prefix
        const base64 = reader.result.split(',')[1]
        // Clean the base64 string
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


</script>

<style>
</style>