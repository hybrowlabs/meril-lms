export const nativeInterface = {
	isAvailable() {
		return typeof window !== 'undefined' && window.nativeInterface
	},

	async getDeviceId() {
		if (!this.isAvailable()) {
			console.warn('Native interface not available')
			return null
		}
		try {
			const deviceId = await window.nativeInterface.execute('getDeviceId')
			return deviceId
		} catch (error) {
			console.error('Error getting device ID:', error)
			return null
		}
	},

	async getPushToken() {
		if (!this.isAvailable()) {
			console.warn('Native interface not available')
			alert('Native interface not available in getPushToken')
			return null
		}
		try {
			alert('Calling window.nativeInterface.execute(getPushToken)...')
			// Using the exact API as provided in the sample code
			const response = await window.nativeInterface.execute('getPushToken')

			alert('Raw response from native: ' + JSON.stringify(response))
			console.log('Raw response from native interface:', response)

			// Handle the response - it might be a string or already parsed
			let token = response

			// If response is an object with a token property
			if (typeof response === 'object' && response !== null && response.token) {
				token = response.token
				alert('Token extracted from response.token: ' + token)
			}
			// If response is a JSON string, try to parse it
			else if (typeof response === 'string' && response.startsWith('{')) {
				try {
					const parsed = JSON.parse(response)
					token = parsed.token || parsed
					alert('Token parsed from JSON: ' + token)
				} catch (parseError) {
					// If parsing fails, use the response as is
					console.log('Could not parse token response, using as string:', response)
					alert('Could not parse, using raw: ' + response)
					token = response
				}
			}

			console.log('Token received:', token)
			alert('Final token to return: ' + token)
			return token
		} catch (error) {
			console.error('Error getting push token:', error)
			alert('Error in getPushToken: ' + error.message)
			return null
		}
	},

	async requestNotificationPermission() {
		if (!this.isAvailable()) {
			console.warn('Native interface not available')
			return false
		}
		try {
			// Request permission for notifications
			const permission = await window.nativeInterface.execute(
				'requestNotificationPermission'
			)
			return permission === 'granted' || permission === true
		} catch (error) {
			console.error('Error requesting notification permission:', error)
			// Try to get token anyway as permission might already be granted
			return true
		}
	},

	async checkNotificationPermission() {
		if (!this.isAvailable()) {
			return false
		}
		try {
			const permission = await window.nativeInterface.execute(
				'checkNotificationPermission'
			)
			return permission === 'granted' || permission === true
		} catch (error) {
			console.error('Error checking notification permission:', error)
			// Assume permission is needed
			return false
		}
	},
}