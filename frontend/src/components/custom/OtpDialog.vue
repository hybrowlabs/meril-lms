<template>
<Teleport to="body" >
  <div v-if="showOtpDialog" 
   aria-modal="true" 
   ref="otpDialogContent"
   tabindex="2" 
   @keydown.tab="trapFocus"
   class="fixed h-screen w-screen inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div
      title="Verify Your Identity"
      class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white"
    >
      <form class="p-6" @submit.prevent="submitOtp">
        <p class="text-center mb-4 text-gray-700 font-medium">
          Please Enter OTPs to continue your Training.
        </p>
        <div class="mb-4">
          <label class="block mb-1 text-gray-800 " for="email-otp">Email OTP</label>
          <TextInput
            id="email-otp"
            v-model="emailOtp"
            type="text"
            placeholder="Enter Email OTP"
            class="w-full mb-2 rounded-lg border p-2 focus:outline-none focus:ring-2"
            :error="!!errors.emailOtp"
          />
        </div>
        <div v-if="requiresMobileOtp" class="mb-6">
          <label class="block mb-1 text-gray-800 " for="mobile-otp">Mobile OTP</label>
          <TextInput
            id="mobile-otp" 
            v-model="mobileOtp"
            type="text"
            placeholder="Enter Mobile OTP"
            class="w-full rounded-lg border p-2 focus:outline-none focus:ring-2"
            :error="!!errors.mobileOtp"
          />
        </div>
        <Button
          id="send-otp" 
          type="button"
          class="block w-fit p-2 ml-auto mb-4 rounded-lg border border-gray-500 cursor-pointer select-none active:ring-2 ring-gray-800"
          @click="sendOtp"
          v-bind:disabled="loading"
        >
          Resend me OTPs
        </Button>
        <Button 
          id="submit-otp" 
          type="submit"
          variant="solid"
          class="w-full flex"
          v-bind:disabled="loading"
        >
        <div class="flex items-center justify-center w-full">
         <Spinner v-if="loading" class="w-4 mr-2" />
          <span v-if="loading" class="block">Loading...</span>
          <span v-else class="block">Submit</span>
          
          </div>
        </Button>
      </form>
    </div>
  </div>
</Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call, TextInput, Button , Spinner, toast } from "frappe-ui";

const showOtpDialog = ref(false)
const emailOtp = ref('')
const mobileOtp = ref('')
const requiresMobileOtp = ref(true) // Default to true for safety
const errors = ref({
  emailOtp: "",
  mobileOtp: ""
})
const loading = ref(false);

const otpDialogContent = ref(null);

// focus trap prevent focus on other elements than otpDialog 
const trapFocus = (event) => {
  if (event.key !== 'Tab') return;

  const dialog = otpDialogContent.value;
  if (!dialog) return;

  const focusableSelectors = requiresMobileOtp.value 
    ? "#email-otp, #mobile-otp, #send-otp, #submit-otp"
    : "#email-otp, #send-otp, #submit-otp";
  const focusableElements = dialog.querySelectorAll(focusableSelectors);

  if (focusableElements.length === 0) {
    event.preventDefault();
    return;
  }

  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  if (event.shiftKey) {
    if (document.activeElement === firstFocusable || document.activeElement === dialog) {
      lastFocusable.focus();
      event.preventDefault();
    }
  } else {
    if (document.activeElement === lastFocusable || document.activeElement === dialog) {
      firstFocusable.focus();
      event.preventDefault();
    }
  }
};
onMounted(() => {
if(window.self === window.top)
    should_user_redirect();
});

async function checkMobileOtpRequirement() {
  try {
    const res = await call("lms.overrides.otp_aut.requires_mobile_otp", {});
    requiresMobileOtp.value = res.requires_mobile_otp || false;
  } catch (error) {
    // Default to requiring mobile OTP for safety if API call fails
    console.error("Error checking mobile OTP requirement:", error);
    requiresMobileOtp.value = true;
  }
}

async function getUnlockedStatus() {
  try {
    // Check if mobile OTP is required before showing dialog
    await checkMobileOtpRequirement();
    
    const res = await call("lms.overrides.otp_aut.get_user_status", {});
    if (res.status === "unlocked") {
      showOtpDialog.value = false;
      return;
    }
    showOtpDialog.value = true;
    if (res.status === "locked") {
      sendOtp();
      return;
    }
    if (res.status === "error") {
      sendOtp();
      // console.error("Error fetching user status:", res.message);
      toast.error(res.message || "Failed to fetch user status. Please refresh the page again.");
    }
  } catch (error) {
    // console.error("Error fetching user status:", error);
    toast.error("Failed to fetch user status. Please try again after few seconds.");
  }
}

async function sendOtp() {
  try {
    loading.value = true;
    const res = await call("lms.overrides.otp_aut.send_email_otp");
    if (res.status === "success" || res.status === "resent" || res.status === "new") {
      toast.success(res.message || "OTP sent successfully!");

    } else if (res.status === "error") {
      toast.error(res.message || "Failed to send OTP. Please try again.");
    }
  } catch (error) {
    // console.error("Error sending OTP:", error);
    toast.error("Failed to send OTP. Please try again later.");
  }finally{
    loading.value = false;
  }
}

async function submitOtp() {
  errors.value.emailOtp = ""
  errors.value.mobileOtp = ""
  if (!emailOtp.value) {
    errors.value.emailOtp = "Email OTP is required"
  }
  if (requiresMobileOtp.value && !mobileOtp.value) {
    errors.value.mobileOtp = "Mobile OTP is required"
  }
  if (errors.value.emailOtp || errors.value.mobileOtp) return;

  try {
    loading.value = true;
    const res = await call("lms.overrides.otp_aut.verify_email_otp", {
      otp: emailOtp.value,
      otp1: requiresMobileOtp.value ? mobileOtp.value : null
    });
    if (res.status === "success") {
      toast.success("OTP verified successfully!");
      showOtpDialog.value = false;
    } else if (res.status === "error") {
      toast.error(res.message || "Failed to verify OTP. Please try again.");
    }
  } catch (error) {
    // console.error("Error verifying OTP:", error);
    toast.error("Failed to verify OTP. Please try again later.");
  }finally{
    loading.value = false;
  }
}

const should_user_redirect = async() =>{
  try{
    const res = await call("lms.overrides.otp_aut.should_user_redirect", {});
    if(res.status === "redirect"){
      window.location.href = "/edit-distributor-profile";
      return;
    }
    getUnlockedStatus();
  }catch(error){
    // console.error("Error checking if user is a distributor:", error);
    getUnlockedStatus();
  }
}
</script>

<style scoped>
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

</style>