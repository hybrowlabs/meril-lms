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
			return null
		}
		try {
			// Using the exact API as provided in the sample code
			const token = await window.nativeInterface.execute('getPushToken')
			console.log('Token', token)
			return token
		} catch (error) {
			console.error('Error getting push token:', error)
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