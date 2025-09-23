<template>
  <div v-if="state?.showDocument">
    <div v-if="showError">
      <div class="fixed inset-0 z-50 bg-black bg-opacity-50">
        <div class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative">
          <button
        class="block ml-auto focus:ring-2 hover:ring-3 hover:ring-gray-400 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
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
          class="block ml-auto focus:ring-2 hover:ring-3 hover:ring-gray-400 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
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
      class="block ml-auto focus:ring-2 hover:ring-3 hover:ring-gray-400 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
        aria-label="Close"
      >
        ×
      </button>
      <h3 class="text-xl font-medium mb-4">Compliance Documents</h3>
      <ul class="space-y-4 mb-2">
        <li v-for="document in documentsList" :key="document" class="flex  items-center justify-between">
          <span class="text-sm text-gray-900">{{ document }}</span>
          <Button theme="gray" variant="outline" @click="downloadDocument(document)" >Download</Button>
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
        class="block ml-auto focus:ring-2 hover:ring-3 px-2 rounded-sm hover:ring-gray-900 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none transition"
        @click="closeDialog"
        aria-label="Close"
      >
        ×
      </button>
      <h3 class="text-lg font-semibold mb-4 uppercase text-gray-900">{{ currentDocName || 'Instructions:' }}</h3>
      <ol class="list-decimal list-inside text-gray-700 mb-4 space-y-1">
        <li>
          Please <span class="font-semibold text-gray-900">download</span> the <span class="font-semibold"> {{  uploadDocumentName }} </span> 
        </li>
  
          <li v-if="uploadDocumentName=='Meril Distributor Compliance Policy Adoption Form'">
            Insert your company's letterhead at the top of the document.
          </li>
          <li v-else>
            Sign the Docuemnt
          </li>
          <li>
            Then upload the completed document.
          </li>
      </ol>
      <div v-if="showDownloadForm" class="mb-4 p-3 bg-gray-50 border border-gray-400 text-gray-800 rounded flex items-center gap-2">
        <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-900 text-white font-bold mr-2">✓</span>
        <span>
          <strong>Document Submitted</strong> - You have already submitted a document for this course.
        </span>
      </div>
      <form @submit.prevent="handleDownload" class="mb-4">
        <button
          type="submit"
          class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-gray-100 hover:bg-gray-300
          text-gray-900 font-semibold shadow transition-colors duration-150 focus:outline-none focus:ring-2 
          focus:ring-offset-2 focus:ring-gray-600 active:ring-2 active:ring-black"
        >
          <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4"/>
          </svg>
          Download Document
        </button>
      </form>
      <form @submit.prevent="uploadDocument">
        <div class="mb-4">
          <label
            for="upload-file"
            class="block mb-2 text-sm font-medium text-gray-700"
          >
            Upload Document
          </label>
          <div class="relative flex items-center">
            <input
              id="upload-file"
              type="file"
              @change="onFileChange"
              class="block w-full border border-gray-500 text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-900 hover:file:bg-gray-100 transition pr-10"
              required
              accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/pdf"
            />
            <span class="absolute right-3 pointer-events-none flex items-center">
              <!-- Upload Icon beside "Choose file" text -->
              <svg class="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5-5m0 0l5 5m-5-5v12"/>
              </svg>
            </span>
          </div>
        </div>
        <button
          type="submit"
          :disabled="loadingUploadForm"
          class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-gray-900 hover:bg-gray-700 text-white font-semibold shadow transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <Spinner v-if="loadingUploadForm" class="w-4 h-4 mr-2" />
          <span>{{ loadingUploadForm ? "Uploading Document" : "Submit" }}</span>
        </button>
      </form>
    </div>
  </div>

  <div v-if="showDeclarationForm" class="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
    <div
      class="min-[500px]:w-100 w-full max-w-md max-h-[90vh] overflow-y-auto shadow-lg rounded-lg bg-white p-6 relative"
    >
      <!-- Close Icon -->
      <button
      class="block ml-auto focus:ring-2 hover:ring-3 px-2 rounded-sm hover:ring-gray-900 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
        aria-label="Close"
      >
        ×
      </button>
      <div v-if="role_is=='Distributor'">
        <div v-if="uploadDocumentName=='Meril Distributor Compliance Policy Adoption Form'">
          <h3 class="text-center font-semibold mx-auto max-w-80">Meril Distributor- Compliance Policy Adoption Form</h3>
          <div class="overflow-y-auto h-60 pb-4 border-2 mb-2 mt-4 rounded-lg border-black/50 px-2 border-dotted ">
              <p class="text-sm mt-4">
                {{ new Date().toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true, year: 'numeric', month: 'short', day: '2-digit' }) }}
              </p>
              <p class="text-sm text-justify mt-2">We {{ declaratinoInfo.distributor_company_name }}, being the Distributor of Meril {{ distributor?.meril_company_table[0]?.meril_company_name }} do hereby certify that we have willingly adopted attached Meril
            Distributor Compliance Policy as our own Compliance Policy with effect from
            {{ current_date }} and declare to abide by the same.</p>
              <p class="text-sm text-justify mt-2">All employees, partners, directors, proprietor of our organization are expected to
              observe and adhere to this Policy.</p>
              <p class="text-sm text-justify mt-2 underline font-semibold">Nomination of Compliance Officer:</p>
              <p class="text-sm text-justify mt-2">{{ name }} is nominated as Compliance Officer of our organization with effect
                from {{ current_date }}</p>
                
                <p class="text-sm text-justify mt-6">Authorized representative of {{ declaratinoInfo.distributor_company_name }}</p>
                <p class="text-sm text-justify mt-6">Name : {{ declaratinoInfo.attendee_name }}</p>
                <p class="text-sm text-justify mt-2">Title : {{ declaratinoInfo.designation }}</p>
                <p class="text-sm text-justify mt-2">Email Id : {{ declaratinoInfo.distributor_email_address }}</p>
                <p class="text-sm text-justify mt-2">Contact number : {{ declaratinoInfo.distributor_contact_number }}</p>
                <p
                  class="text-sm text-justify mt-2"
                >
                  Sign and Seal : <span > {{"<Compliance officer nominee name>"}} </span>
                </p>
             </div>
            </div>
            <div v-else-if="uploadDocumentName=='Distributor Self Declaration'">
              Self Declaration
            </div>
            <div v-else-if="uploadDocumentName=='Meril Distributor Compliance Code Of Conduct'">
              Meril Distributor Compliance Code Of Conduct
            </div>
        </div>
        <div v-else-if="role_is=='Employee'">
          <h3 class="text-center font-semibold mx-auto max-w-80">Employee Declaration - Ethical Practices &amp; Compliance</h3>
          <div class="overflow-y-auto h-60 pb-4 border-2 mb-2 mt-4 rounded-lg border-black/50 px-2 border-dotted ">
              <p class="text-sm text-justify mt-2">I hereby declare that I have undergone and understood training provided on Ethical
Practices and compliance . As a responsible employee of Meril, I acknowledge and
accept the duty to comply with the procedural frameworks developed and adopted by
the Meril’s Management from time to time.</p>
            <p class="text-sm text-justify mt-2">I have been thoroughly informed on the various Code of Conduct that govern the
ethical operation of Meril’s business, which I agree to follow diligently. I have read
understood and consent to abide by the following Codes of Conduct on a consensus-
ad-idem basis :</p>
              <ol class="list-decimal pl-6 text-sm mt-2">
                <li>Anti Bribery and Anti Corruption Policy</li>
                <li>Export Controls and Trade Sanctions Policy</li>
                <li>HCP &amp; HCO Compliance framework</li>
                <li>National Pharmaceutical Pricing Authority norms for capping of
maximum retail price &amp; maximum trade margin across all trade
channels</li>
                <li>FCPA (Foreign Corrupt Practices Act)</li>
              </ol>
              <p class="text-sm text-justify mt-2">I hereby confirm that I shall adhere in all respects to the ethics and standards of conduct
outlined in the above Codes of Conduct. I understand that any violation or even potential
violation of the these Codes of Conduct / Policies may result in disciplinary action,
including termination of my employment.</p>
                <p class="text-sm text-justify mt-2">I certify that I am not currently in violation of any of the afore mentioned Codes of
                  Conduct.</p>
                <p class="text-sm text-justify mt-2">Furthermore, I declare that I have no direct or indirect familial, financial, or other
relationships with any distributor or nominated representative of the distributor. Should I
become aware of any such relationship in the future, I commit to disclosing it to Meril
within thirty (30) days from the date of awareness.</p>
                  <p class="text-sm text-justify mt-2">I also declare that I will not engage in any financial transactions with any distributor or
nominated representative of the distributor. I acknowledge that Meril Group shall bear no
responsibility or liability for any such transactions.</p>
                
                <p class="text-sm text-justify mt-2">Employee Name : {{ declaratinoInfo.employee_name }}</p>
                <p class="text-sm text-justify mt-2">Employee ID : {{ declaratinoInfo.custom_employee_id }}</p>
                <p class="text-sm text-justify mt-2">Company Name : {{ declaratinoInfo.company }}</p>
                <p class="text-sm text-justify mt-2">Date : {{ date }}</p>
             </div>
        </div>
        
        <form @submit="handleCertify" class="flex flex-col gap-y-2">
          <div class="flex flex-col gap-y-2">
            <label for="name" class="text-sm font-medium">Name</label>
            <TextInput
              id="name"
              type="text"
              placeholder="Enter name"
              v-model="name"
              class="w-full rounded-lg border focus:outline-none focus:ring-2 border-gray-300"
              required
              minlength="3"
            />
          </div>
        
          <div class="flex flex-col gap-y-2">
            <label for="date" class="text-sm font-medium">Date</label>
            <input
              id="date"
              type="datetime-local"
              :value="new Date().toISOString().slice(0,16)"
              class="border rounded px-2 py-1 text-sm"
              readonly
            />
          </div>
          <Button theme="gray" variant="solid" class="w-full mt-4" type="submit" :disabled="loadingUploadForm">
        <div class="flex items-center justify-center w-full">
        <Spinner v-if="loadingUploadForm" class="w-4 mr-2" />  
        <span>{{ loadingUploadForm ? "" : "I Certify"}}</span>
        </div>
      </Button>
    </form>
    </div>
  </div>
</div>
</template>

<script setup>
import { Button, Spinner } from "frappe-ui";
import { defineEmits, ref, watch, computed, onMounted } from "vue";
import { call , TextInput, Select, toast } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { resetCourseCompletion, state } from "../../stores/course_completion.js";

const emit = defineEmits(['close']);
const current_date = (() => {
  const date = new Date();
  const day = date.getDate().toString().padStart(2, '0');
  const month = date.toLocaleString('default', { month: 'long' });
  const year = date.getFullYear();
  return `${day} ${month} ${year}`;
})();
// Second modal state and logic
const showUploadForm = ref(false)
const uploadDocumentName = ref("Meril Distributor Compliance Policy Adoption Form");
const loadingScreen = ref(false);
const showDownloadForm = ref(false)
const name = ref('')
const currentDocName = ref('')
const signatureText = computed(() => name.value?.trim() || 'Signature')
const showError = ref(false)
const declaratinoInfo = ref(null);
const showDeclarationForm = ref(true);
const uploadDolaodEnabled = ref({
  distributor_self_declaration: false,
  meril_distributor_compliance_code_of_conduct: false,
  meril_distributor_compliance_policy_adoption_form: false,
})

// signature removed

const date = ref( new Date().toISOString().split('T')[0])
const file = ref(null)
const documentsList = ref([])
const loadingUploadForm = ref(false);
const errorMessage = ref('')
const course_documents_record_id = ref('');
const doctype = ref('');

const role_is = ref(null);
// signature fonts removed


const handleCertify = async (event) => {
  if (event && typeof event.preventDefault === "function") {
    event.preventDefault();
  }

  // If Employee, take signature via API then show download form
  if (role_is.value === 'Employee') {
    if (!name.value || name.value.trim().length < 3) {
      toast.error('Please enter name (minimum 3 characters)')
      return
    }
    showDeclarationForm.value = false;
    showUploadForm.value = false;
    showDownloadForm.value = true;
    return;
  }

  // Default (Distributor): move to upload form
  showDeclarationForm.value = false;
  showUploadForm.value = true;
}
// Fetch list of signature types where font files are not private
// signature fonts removed

async function get_declaration_info(){
  try{
  const res = await call("lms.overrides.documents.get_declaration_info");
  
  console.log("declaraion info", res);
  declaratinoInfo.value = res;
  }catch(err){
    console.error("Error getting declaration", e)
    toast.error("Error in  getting declaration")
  }
}
uploadDolaodEnabled
function decideInitialView() {
  // Priority: Self Declaration → Code of Conduct → Policy Adoption → else Download
  showError.value = false
  loadingScreen.value = false
  showDownloadForm.value = false
  showUploadForm.value = false
  showDeclarationForm.value = false

  if (uploadDolaodEnabled.value.distributor_self_declaration) {
    showDeclarationForm.value = true
    return
  }
  if (uploadDolaodEnabled.value.meril_distributor_compliance_code_of_conduct) {
    // enable upload flow for Code of Conduct
    currentDocName.value = 'Meril Distributor Compliance Code of Conduct'
    uploadDocumentName.value = currentDocName.value
    showUploadForm.value = true
    return
  }
  if (uploadDolaodEnabled.value.meril_distributor_compliance_policy_adoption_form) {
    // enable upload/download for Policy Adoption
    currentDocName.value = 'Meril Distributor Compliance Policy Adoption Form'
    uploadDocumentName.value = currentDocName.value
    showUploadForm.value = true
    return
  }
  // fallback: only show download list modal
  showDownloadForm.value = true
}

onMounted(async () => {
  console.log("mounted");
  try {
    const res = await call("lms.overrides.documents.get_upload_download_docuemtn_enabled");
    if (res?.success) {
      uploadDolaodEnabled.value = {
        distributor_self_declaration: !!res.distributor_self_declaration,
        meril_distributor_compliance_code_of_conduct: !!res.meril_distributor_compliance_code_of_conduct,
        meril_distributor_compliance_policy_adoption_form: !!res.meril_distributor_compliance_policy_adoption_form,
      }
    }
  } catch (e) {
    console.error("Error fetching upload/download enabled flags", e);
  }
  decideInitialView()
});


const closeDialog = ()=>{
  resetCourseCompletion();
  name.value = "";
  showError.value = false;
  showDownloadForm.value = false;
  showDeclarationForm.value = false;
}

const onFileChange = (e) => {
  const selectedFile = e.target.files[0];
  const maxSize = 4 * 1024 * 1024; // 4MB
  if (selectedFile && selectedFile.size > maxSize) {
    file.value = null;
    e.target.value = ""; // reset file input
    toast.warning("File size must be less than 4MB");
    return;
  }
  file.value = selectedFile;
}

const route = useRoute()
const courseName = computed(() => route.params.courseName || state.courseName)

watch( () => state.showDocument , (newVal) => {
  if (newVal) {
    checkDocumentSubmission()
  }
})

const checkDocumentSubmission = async () => {
try {
    loadingScreen.value = true
    showDeclarationForm.value = false
    // Gate by enablement flags with requested priority.
    // If none are enabled, show only download modal and return.
    if (!uploadDolaodEnabled.value.distributor_self_declaration
      && !uploadDolaodEnabled.value.meril_distributor_compliance_code_of_conduct
      && !uploadDolaodEnabled.value.meril_distributor_compliance_policy_adoption_form) {
      loadingScreen.value = false
      decideInitialView()
      return
    }
    const res = await call('lms.overrides.documents.has_user_submited_document', { course: courseName.value })
    console.log("res",res)
    if(res.error){
      showError.value = true
      showUploadForm.value = false
      errorMessage.value = res.error
      showDeclarationForm.value = false
      toast.error(res.error)
      return
    }
    if (res.submited === true) {
      showDownloadForm.value = true
      showUploadForm.value = false
      showDeclarationForm.value = false
      documentsList.value = res.documents_list
      course_documents_record_id.value = res.course_documents_record_id
      doctype.value = res.doctype
      role_is.value = res.role_is
      console.log('Document already submitted for this course')
    } else {
      get_declaration_info();
      role_is.value = res.role_is
      // decide initial view based on flags
      decideInitialView()
    }

    if(showError.value){
      showError.value = false;
    }
  } catch (e) {
    // handle error
    showDownloadForm.value = false
    showUploadForm.value = false
    showDeclarationForm.value = false
    showError.value = true
    toast.error(e?.exception || 'Error checking document submission')
  } finally {
    loadingScreen.value = false
  }
}

const uploadDocument = async () => {
  loadingUploadForm.value = true

  if(!file.value) {
    toast.error("Please select a file")
    loadingUploadForm.value = false
    return;
  }
  
  try {
    // Convert file to base64
    const base64Data = await fileToBase64(file.value)
    
    // Call the save_user_course_document_with_file method
    const response = await call('lms.overrides.documents.upload_distributor_document_with_datetime', {
      course: courseName.value,
      document_name: currentDocName.value || file.value.name,
      filename: file.value.name,
      base64_file_data: base64Data,
      is_private: 0,
      document_upload_datetime: new Date().toISOString(),
      uploadDocumentName: uploadDocumentName.value
    })
    console.log("response", response)
    if (response.message && response.success) {
      toast.success('Document uploaded successfully')
      showUploadForm.value = false
      showDownloadForm.value = true
      // After successful upload, check what should be prompted next
      try {
        const next = await call('lms.overrides.documents.get_next_distributor_document', { course: courseName.value })
        if (next?.success) {
          if (next.next_document) {
            // Prompt next document in sequence using existing download flow
            currentDocName.value = next.next_document
            uploadDocumentName.value = next.next_document
            showDownloadForm.value = false
            showUploadForm.value = true
            showDeclarationForm.value = false
          } else {
            // No further docs → refresh normal state
            await checkDocumentSubmission();
          }
        }
      } catch (e) {
        console.error('Failed to get next distributor document', e)
      }
      // Reset form
      date.value = ''
      file.value = null
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]')
      if (fileInput) fileInput.value = ''
      checkDocumentSubmission();
    } else {
      toast.error(response?.message || 'Upload failed')
    }
  } catch (error) {
    console.error('Upload error:', error)
    toast.error(error.messages?.[0] || 'Upload failed')
  }finally {
    loadingUploadForm.value = false
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

const directDownload = async(url, file_name)=>{
   const link = document.createElement('a');
      link.href = url;
      link.download = file_name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
}


const handleDownload = async() => {
  
  try{
    // Pass name in the API call
    const res = await call("lms.overrides.documents.generate_dynamic_docx", {
      name: name?.value || '',
      font_path: null,
    });
    console.log("res", res)
    if (res?.success && res.file_content) {
      toast.success("Downloading Started...");

      // Check if running inside React Native WebView
      const isReactNativeWebView = !!window.ReactNativeWebView;

      if (isReactNativeWebView) {                                                                                                                                                                                                                                                                                                                                                              
        // Send file data to React Native via postMessage
        window.ReactNativeWebView.postMessage(
          JSON.stringify({
            type: "DOWNLOAD_FILE",
            base64: res.file_content,
            fileName: res.file_name || `${name.value}_Compliance_Policy_Adoption_Form.docx`,
            mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          })
        );
      } else {
        const url = 'data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,' + res.file_content
        const a = document.createElement('a');
        a.href = url;
        a.download = res.file_name || `${name?.value || 'Compliance'}_Compliance_Policy_Adoption_Form.docx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } else {
      toast.error(res?.error || "Error generating document")
    }
  }catch(e) {
    console.error("Error in handleDownload", e)
    toast.error("Error in downloading document")
  }
}

const downloadDocument = async (document_name) => {

  try {
      const baseUrl = window.location.origin;
      let url = null;

      if(!course_documents_record_id?.value){
        toast.error("Course document record id not found")
        console.error("Course document record id not found")
        return;
      }

      const params = new URLSearchParams({
          doctype: doctype.value,
          name: course_documents_record_id.value,
          format: document_name,
          no_letterhead: '1',
          letterhead: 'No Letterhead',
          settings: '{}',
          _lang: 'en',
          custom_filename: document_name, // set custom filename
          custom_type: 'download'         // set custom type
      });

      url = `${baseUrl}/api/method/lms.overrides.download_pdf.custom_download_pdf?${params.toString()}`;
        
      if (document_name === "Meril Distributor Compliance Policy") 
          url = `${baseUrl}/api/method/lms.overrides.documents.downlaod_nonendo_file`;
      
      if (document_name === "Meril Distributor Compliance Policy for Endo") 
          url =  `${baseUrl}/api/method/lms.overrides.documents.downlaod_endo_file`;

      directDownload(url, document_name);
  } catch (e) {
      toast.error('Failed to download document');
      console.error("Error in downloadDocument", e);
  }
}

</script>

<style>
</style>