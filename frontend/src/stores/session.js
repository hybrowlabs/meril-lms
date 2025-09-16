import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { usersStore } from './user'
import router from '@/router'
import { computed, reactive, ref } from 'vue'
import { nativeInterface } from '@/utils/nativeInterface'

export const sessionStore = defineStore('lms-session', () => {
	let { userResource } = usersStore()
	const brand = reactive({})

	function sessionUser() {
		let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
		let _sessionUser = cookies.get('user_id')
		if (_sessionUser === 'Guest') {
			_sessionUser = null
		}
		return _sessionUser
	}

	let user = ref(sessionUser())
	const isLoggedIn = computed(() => !!user.value)

	const login = createResource({
		url: 'login',
		onError() {
			throw new Error('Invalid email or password')
		},
		async onSuccess() {
			userResource.reload()
			user.value = sessionUser()
			login.reset()

			// Register push token after successful login
			await registerPushToken()

			router.replace({ path: '/' })
		},
	})

	const logout = createResource({
		url: 'logout',
		onSuccess() {
			userResource.reset()
			user.value = null
			window.location.reload()
		},
	})

	const branding = createResource({
		url: 'lms.lms.api.get_branding',
		cache: 'brand',
		auto: true,
		onSuccess(data) {
			brand.name = data.app_name
			brand.logo = data.app_logo
			brand.favicon =
				data.favicon?.file_url || '/assets/lms/frontend/learning.svg'
		},
	})

	const sidebarSettings = createResource({
		url: 'lms.lms.api.get_sidebar_settings',
		cache: 'Sidebar Settings',
		auto: false,
	})

	const pushTokenResource = createResource({
		url: 'lms.lms.api.register_push_token',
		makeParams(values) {
			const params = {
				user_id: values.user_id,
				token: values.token,
			}
			if (values.device_id) {
				params.device_id = values.device_id
			}
			return params
		},
		onSuccess(data) {
			console.log('Push token registered successfully:', data)
			alert('Push token registration response: ' + JSON.stringify(data))
		},
		onError(error) {
			console.error('Failed to register push token:', error)
			alert('Push token registration failed: ' + error.message)
		},
	})

	async function registerPushToken() {
		if (!nativeInterface.isAvailable()) {
			console.log('Native interface not available')
			alert('Native interface not available')
			return
		}

		// Ensure user is logged in
		if (!user.value || user.value === 'Guest') {
			console.log('User not logged in, skipping push token registration')
			alert('User not logged in: ' + user.value)
			return
		}

		try {
			console.log('Starting push token registration for user:', user.value)
			alert('Starting push token registration for user: ' + user.value)

			// Request notification permission when user logs in
			const granted = await nativeInterface.requestNotificationPermission()
			alert('Permission granted: ' + granted)
			if (!granted) {
				console.log('Notification permission not granted, attempting to get token anyway')
			}

			// Get push token and device identifier from the native layer
			alert('Attempting to get push token...')
			const [token, deviceId] = await Promise.all([
				nativeInterface.getPushToken(),
				nativeInterface.getDeviceId(),
			])
			console.log('Retrieved push token:', token, 'device:', deviceId)
			alert('Retrieved push token: ' + (token ? token : 'null/undefined'))

			if (!token) {
				console.warn('Could not get push token - token is null or undefined')
				alert('Could not get push token - token is null or undefined')
				return
			}

			// Ensure token is a string
			const tokenString = typeof token === 'object' ? JSON.stringify(token) : String(token)
			alert('Token string prepared: ' + tokenString)

			console.log('Submitting push token to backend:', {
				user_id: user.value,
				token: tokenString,
				device_id: deviceId,
			})
			alert('Submitting to backend - User ID: ' + user.value + ', Token: ' + tokenString)

			// Register token with backend
			const result = await pushTokenResource.submit({
				user_id: user.value,
				token: tokenString,
				device_id: deviceId,
			})

			console.log('Push token registration result:', result)
			alert('Push token registration successful: ' + JSON.stringify(result))
		} catch (error) {
			console.error('Error registering push token:', error)
			alert('Error registering push token: ' + error.message)
		}
	}

	// Check and register push token on page load if user is logged in
	if (isLoggedIn.value) {
		registerPushToken()
	}

	return {
		user,
		isLoggedIn,
		login,
		logout,
		brand,
		branding,
		sidebarSettings,
		registerPushToken,
		pushTokenResource,
	}
})
