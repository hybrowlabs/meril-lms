import { config } from '@vue/test-utils'
import safeHtml from '../directives/safeHtml'

// main.js registers v-safe-html on the app, so a component that uses it renders
// nothing under a bare mount() and the failure looks like missing data rather
// than a missing directive. Registering it here keeps component tests rendering
// what the app renders.
config.global.directives = {
	...config.global.directives,
	'safe-html': safeHtml,
}
