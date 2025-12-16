/**
 * API Error Handler Utility
 * Provides centralized error handling and fallback mechanisms for API calls
 */

import { toast } from 'frappe-ui'

/**
 * Check if an error is a permission/authorization error
 */
export function isPermissionError(error) {
  if (!error) return false

  const errorStr = JSON.stringify(error).toLowerCase()
  return (
    errorStr.includes('permission') ||
    errorStr.includes('403') ||
    errorStr.includes('forbidden') ||
    errorStr.includes('unauthorized') ||
    error?.exc_type?.includes('PermissionError') ||
    error?.http_status_code === 403
  )
}

/**
 * Check if an error is due to missing enrollment
 */
export function isEnrollmentError(error) {
  if (!error) return false

  const errorStr = JSON.stringify(error).toLowerCase()
  return (
    errorStr.includes('not enrolled') ||
    errorStr.includes('enrollment required') ||
    error?.enrollment_required === true
  )
}

/**
 * Check if an error is due to incomplete course progress
 */
export function isProgressError(error) {
  if (!error) return false

  const errorStr = JSON.stringify(error).toLowerCase()
  return (
    errorStr.includes('progress') ||
    errorStr.includes('not completed') ||
    errorStr.includes('complete the course') ||
    (error?.progress !== undefined && error.progress < 100)
  )
}

/**
 * Get a user-friendly error message from an API error
 */
export function getUserFriendlyErrorMessage(error, defaultMessage = 'An error occurred. Please try again.') {
  if (!error) return defaultMessage

  // Check for specific error types
  if (isPermissionError(error)) {
    return 'You do not have permission to perform this action. Please contact support if you believe this is an error.'
  }

  if (isEnrollmentError(error)) {
    return 'You are not enrolled in this course. Please enroll first to access course documents.'
  }

  if (isProgressError(error)) {
    const progress = error?.progress || 0
    return `Please complete the course before accessing documents. Current progress: ${progress}%`
  }

  // Check for custom error messages
  if (error?.message && typeof error.message === 'string') {
    // Clean up technical error messages
    if (error.message.includes('DocType')) {
      return 'A configuration error occurred. Please contact support.'
    }
    if (error.message.includes('SQL') || error.message.includes('Database')) {
      return 'A database error occurred. Please try again later.'
    }
    if (error.message.includes('missing') || error.message.includes('required')) {
      return 'Required information is missing. Please complete your profile and try again.'
    }

    return error.message
  }

  // Return default message
  return defaultMessage
}

/**
 * Handle API errors with appropriate user feedback
 */
export function handleApiError(error, options = {}) {
  const {
    showToast = true,
    logError = true,
    context = '',
    fallbackMessage = 'An error occurred. Please try again.'
  } = options

  // Log error if enabled
  if (logError) {
    console.error(`API Error${context ? ` (${context})` : ''}:`, error)
  }

  // Get user-friendly message
  const message = getUserFriendlyErrorMessage(error, fallbackMessage)

  // Show toast notification if enabled
  if (showToast) {
    toast.error(message)
  }

  return {
    error: true,
    message,
    isPermissionError: isPermissionError(error),
    isEnrollmentError: isEnrollmentError(error),
    isProgressError: isProgressError(error),
    originalError: error
  }
}

/**
 * Wrapper for API calls with automatic error handling
 */
export async function safeApiCall(apiFunction, options = {}) {
  const {
    fallbackValue = null,
    throwOnError = false,
    context = '',
    showErrorToast = true
  } = options

  try {
    const response = await apiFunction()

    // Check if response indicates an error
    if (response?.success === false || response?.error) {
      const errorResult = handleApiError(response, {
        showToast: showErrorToast,
        context
      })

      if (throwOnError) {
        throw new Error(errorResult.message)
      }

      return fallbackValue !== null ? fallbackValue : response
    }

    return response
  } catch (error) {
    const errorResult = handleApiError(error, {
      showToast: showErrorToast,
      context
    })

    if (throwOnError) {
      throw new Error(errorResult.message)
    }

    return fallbackValue
  }
}

/**
 * Create a degraded mode response when APIs are not accessible
 */
export function createDegradedModeResponse(type = 'documents') {
  switch (type) {
    case 'documents':
      return {
        success: false,
        degradedMode: true,
        message: 'Document services are temporarily unavailable. Some features may be limited.',
        submited: false,
        documents_list: [],
        uploaded_documents: [],
        role_is: 'Unknown'
      }

    case 'enabled_flags':
      return {
        success: false,
        degradedMode: true,
        distributor_self_declaration: true,
        meril_distributor_compliance_code_of_conduct: true,
        meril_distributor_compliance_policy_adoption_form: true
      }

    default:
      return {
        success: false,
        degradedMode: true,
        message: 'Service temporarily unavailable'
      }
  }
}

export default {
  isPermissionError,
  isEnrollmentError,
  isProgressError,
  getUserFriendlyErrorMessage,
  handleApiError,
  safeApiCall,
  createDegradedModeResponse
}