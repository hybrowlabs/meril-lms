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
      class="block ml-auto focus:ring-2 hover:ring-3 px-2 rounded-sm hover:ring-gray-900 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
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
            readonly
            disabled
            minlength="3"
          />
     
        <label for="date">Date</label>
        <TextInput
            type="date"
            id="date"
            v-model="date"
            :value="date || new Date().toISOString().split('T')[0]"
            class="w-full rounded-lg border p-2 focus:outline-none focus:ring-2"
            required
            readonly
            disabled
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
            :options="fontStyles.map(font => ({
              label: font.label,
              value: font.value,
              font_file: font.font_file // Pass font_file for later use
            }))"
            required
            :option-style="option => option.font_file ? { fontFamily: `'${option.label}', sans-serif` } : {}"
            readonly
            disabled
          />
          </div>
      <div class="mb-4">
       <input
         type="file"
         @change="onFileChange"
         class="w-full"
         required
         accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/pdf"
       />
      </div>
      <Button theme="gray" variant="solid" class="w-full" type="submit" :disabled="loadingUploadForm">
        <div class="flex items-center justify-center w-full">
        <Spinner v-if="loadingUploadForm" class="w-4 mr-2" />  
        <span>{{ loadingUploadForm ? "Uploading Document" : "Submit"}}</span>
        </div>
      </Button>
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
          <h3 class="text-center font-semibold mx-auto max-w-80">Meril Distributor- Compliance Policy Adoption Form</h3>
          <div class="overflow-y-auto h-60 pb-4 border-2 mb-2 mt-4 rounded-lg border-black/50 px-2 border-dotted ">
              <p class="text-sm mt-4">
                {{ current_date }}
              </p>
              <p class="text-sm text-justify mt-2">We {{ declaratinoInfo.distributor_company_name }}, being the Distributor of Meril {{ distributor?.meril_company_table[0]?.meril_company_name }} do hereby certify that we have willingly adopted attached Meril
            Distributor Compliance Policy as our own Compliance Policy with effect from
            {{ current_date }} and declare to abide by the same.</p>
            <p class="text-sm text-justify mt-2">All employees, partners, directors, proprietor of our organization are expected to
              observe and adhere to this Policy.</p>
              <p class="text-sm text-justify mt-2 underline font-semibold">Nomination of Compliance Officer:</p>
              <p class="text-sm text-justify mt-2">{{ name?name:"<signature>" }} is nominated as Compliance Officer of our organization with effect
                from {{ current_date }}</p>
                
                <p class="text-sm text-justify mt-6">Authorized representative of {{ declaratinoInfo.distributor_company_name }}</p>
                <p class="text-sm text-justify mt-6">Name : {{ declaratinoInfo.attendee_name }}</p>
                <p class="text-sm text-justify mt-2">Title : {{ declaratinoInfo.designation }}</p>
                <p class="text-sm text-justify mt-2">Email Id : {{ declaratinoInfo.distributor_email_address }}</p>
                <p class="text-sm text-justify mt-2">Contact number : {{ declaratinoInfo.distributor_contact_number }}</p>
                <p class="text-sm text-justify mt-2">Sign and Seal : {{ name?name:"<signature>" }}</p>
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
             
                <p class="text-sm text-justify mt-6">Signature : {{ name?name:"<signature>" }}</p>
                <p class="text-sm text-justify mt-2">Employee Name : {{ declaratinoInfo.employee_name }}</p>
                <p class="text-sm text-justify mt-2">Employee ID : {{ declaratinoInfo.custom_employee_id }}</p>
                <p class="text-sm text-justify mt-2">Company Name : {{ declaratinoInfo.company }}</p>
                <p class="text-sm text-justify mt-2">Date : {{ date }}</p>
             </div>
        </div>
        
        <form @submit="handleCertify" class="flex flex-col gap-y-2">
        <TextInput
            type="text"
            placeholder="Signature"
            v-model="name"
            class="w-full rounded-lg border focus:outline-none focus:ring-2 border-none p-0"
            required
            minlength="3"
            ></TextInput>
            <div class="flex gap-x-2">
            <select
              v-model="signatureType"
              @change="signatureType = $event.target.value"
              :style="{ fontFamily: signatureType || 'sans-serif', lineHeight: 1.9, padding: '0px 5px' }"
              class="block w-full px-3 overflow-auto py-2 border border-gray-300 rounded text-sm bg-white text-gray-900 focus:outline-none focus:ring-0 focus:border-gray-300"
              required
            >
              <option
                v-for="fontStyle in fontStyles"
                :key="fontStyle.value"
                :value="fontStyle.value"
                :style="{ fontFamily: fontStyle.value }"
              >
                {{ signatureText }}
              </option>
          </select>
          <TextInput
            type="date"
            id="date"
            v-model="date"
            :value="date || new Date().toISOString().split('T')[0]"
            disabled
            class="w-full rounded-lg border p-0 border-none focus:outline-none focus:ring-2"
            required
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
const loadingScreen = ref(false);
const showDownloadForm = ref(false)
const signatureType = ref('')
const showError = ref(false)
const declaratinoInfo = ref(null);
const showDeclarationForm = ref(true);

const name = ref('')
const signatureText = computed(() => {
  const trimmedName = name.value.trim();
  return trimmedName !== "" ? trimmedName : "Signature";
});

const date = ref( new Date().toISOString().split('T')[0])
const file = ref(null)
const documentsList = ref([])
const loadingUploadForm = ref(false);
const errorMessage = ref('')
const course_documents_record_id = ref('');
const doctype = ref('');

const role_is = ref(null);
const fontStyles = ref([]);


const handleCertify = async (event) => {
  if (event && typeof event.preventDefault === "function") {
    event.preventDefault();
  }

  // If Employee, take signature via API then show download form
  if (role_is.value === 'Employee') {
    if (!name.value || name.value.trim().length < 3) {
      toast.error("Please enter signature (minimum 3 characters)");
      return;
    }
    if (!signatureType.value) {
      toast.error("Please select a signature type");
      return;
    }
    try {
      loadingUploadForm.value = true;
      const res = await call('lms.overrides.documents.get_employee_signature', {
        signature: name.value,
        signature_font_type: signatureType.value,
        course: courseName.value
      });
      if (res?.success) {
        toast.success('Signature submitted successfully');
        await checkDocumentSubmission();
        showDeclarationForm.value = false;
        showUploadForm.value = false;
        showDownloadForm.value = true;
      } else {
        toast.error(res?.message || 'Failed to submit signature');
      }
    } catch (e) {
      toast.error(e?.message || 'Failed to submit signature');
    } finally {
      loadingUploadForm.value = false;
    }
    return;
  }

  // Default (Distributor): move to upload form
  showDeclarationForm.value = false;
  showUploadForm.value = true;
}
// Fetch list of signature types where font files are not private
async function fetchSignatureTypesWithPublicFonts() {
  try {
    // Use the whitelisted backend function to fetch public signature font styles
    const res = await call("lms.overrides.documents.get_public_signature_font_styles");
    console.log("res", res);
    // Dynamically generate @font-face CSS rules for each font style returned from backend
    if (Array.isArray(res)) {
      // Remove any previously injected font-face styles to avoid duplicates
      const prevStyle = document.getElementById('dynamic-font-face-styles');
      if (prevStyle) prevStyle.remove();

      let css = '';
      res.forEach(font => {
        if (font.font_file && font.value) {
          css += `
            @font-face {
              font-family: '${font.value}';
              src: url('${font.font_file}');
              font-display: swap;
            }
          `;
        }
      });
      if (css) {
        const style = document.createElement('style');
        style.id = 'dynamic-font-face-styles';
        style.innerHTML = css;
        document.head.appendChild(style);
      }
    }
    return res || [];
  } catch (e) {
    toast.error("Failed to fetch signature types");
    return [];
  }
}

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

onMounted(async () => {
  console.log("mounted");
  fontStyles.value = await fetchSignatureTypesWithPublicFonts();
  console.log(fontStyles.value)
});

const handleDownload = async() => {
  if(name.value === '' || name.value.trim().length < 3 || date.value === '') {
    toast.error("Please enter name (minimum 3 characters) and date")
    return
  }
  try{
    const res = await call("lms.overrides.documents.generate_dynamic_docx", {
        name: name.value
      });
    console.log("res", res)
    if(res?.success && res.file_url){
      const a = document.createElement('a');
      a.href = res.file_url;
      a.download = res.file_name || `${name.value}_Compliance_Policy_Adoption_Form.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else {
      toast.error(res?.error || "Error generating document")
    }
  }catch(e) {
    console.error("Error in handleDownload", e)
    toast.error("Error in downloading document")
  }
}

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
      showDownloadForm.value = false
      showUploadForm.value = false
      showDeclarationForm.value = true
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
  console.log("uploadDocument")
  loadingUploadForm.value = true

  if(!name.value || name.value.trim().length < 3){
    toast.error("Please enter name (minimum 3 characters)");
    loadingUploadForm.value = false
    return;
  }
  if(!file.value) {
    toast.error("Please select a file")
    loadingUploadForm.value = false
    return;
  }
  if (!signatureType.value) {
    toast.error("Please select a signature type")
    loadingUploadForm.value = false
    return;
  }
  try {

    // Convert file to base64
    const base64Data = await fileToBase64(file.value)
    
    // Call the save_user_course_document_with_file method
    const response = await call('lms.overrides.documents.save_user_course_document_with_file', {
      course: courseName.value,
      document_name: name.value || file.value.name,
      filename: file.value.name,
      base64_file_data: base64Data,
      is_private: 0,
      signature_type: signatureType.value,
      name : name.value
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
  console.log("directDownload", url, file_name)
   const link = document.createElement('a');
      link.href = url;
      link.download = file_name + '.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
}

// Helper function to download a file from an API endpoint and save it as a file
const downloadFileFromApi = async (apiUrl, fileName) => {
  console.log("apis called")
  try {
    let csrfToken = null;
   if(window?.csrf_token)
      csrfToken = window.csrf_token;
      const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/pdf',
        'Accept': 'application/pdf',
        'X-Frappe-CSRF-Token': csrfToken
      }
    });
    console.log('response', response)
    if (!response.ok) {
      consol.log("falied")
      toast.error("Failed to download the document.");
      return;
    }
    // Try to parse as JSON first (for error message)
    let isJson = false;
    let data;
    try {
      data = await response.clone().json();
      isJson = true;
    } catch (e) {
      // Not JSON, fallback to blob
    }
    if (isJson && data && data.message) {
      toast.error(data.message || "You are not allowed to download this file.");
      return;
    }
    // Otherwise, treat as PDF blob
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    directDownload(url, fileName);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    toast.error("Error downloading the document.");
  }
}

const downloadDocument = async (document_name) => {
  try {
    if (document_name === "Meril Distributor Compliance Policy") {
      await downloadFileFromApi('/api/method/lms.overrides.documents.downlaod_nonendo_file', document_name);
      return;
    }
    if (document_name === "Meril Distributor Compliance Policy for Endo") {
      await downloadFileFromApi('/api/method/lms.overrides.documents.downlaod_endo_file', document_name);
      return;
    }

    if (course_documents_record_id.value) {
        const baseUrl = window.location.origin;
        const params = new URLSearchParams({
            doctype: doctype.value,
            name: course_documents_record_id.value,
            format: document_name,
            no_letterhead: '1',
            letterhead: 'No Letterhead',
            settings: '{}',
            _lang: 'en'
          });
        const url = `${baseUrl}/api/method/frappe.utils.print_format.download_pdf?${params.toString()}`;
        directDownload(url, document_name);
    }else{
      toast.error("Course document record id not found")
      console.error("Course document record id not found")
    }
  } catch (e) {
    toast.error('Failed to download document');
    console.error("Error in downloadDocument", e);
  }
}

</script>

<style>
</style>