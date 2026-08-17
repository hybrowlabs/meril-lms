import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import LockedLessonNotice from '@/components/LockedLessonNotice.vue'

// Mirrors src/translation.js: a message carrying {0}-style placeholders returns
// a { format } object, not a string, and takes no replacement argument. A plain
// passthrough stub would let a real `__(...).format is not a function` crash
// through.
const __ = (message: string) => {
	if (!/{\d+}/.test(message)) return message
	return {
		format: (...args: unknown[]) =>
			message.replace(/{(\d+)}/g, (match, number) =>
				typeof args[number] !== 'undefined' ? String(args[number]) : match
			),
	}
}

const mountNotice = (props = {}) =>
	mount(LockedLessonNotice, {
		props,
		global: { mocks: { __ } },
	})

beforeEach(() => {
	vi.stubGlobal('__', __)
	vi.useFakeTimers()
})

afterEach(() => {
	vi.useRealTimers()
})

describe('LockedLessonNotice', () => {
	it('hides the ticking counter from assistive technology', () => {
		const wrapper = mountNotice()
		const counter = wrapper.get('.tabular-nums')

		expect(counter.attributes('aria-hidden')).toBe('true')
		expect(counter.attributes('role')).toBeUndefined()
		expect(counter.attributes('aria-live')).toBeUndefined()
		expect(counter.text()).toContain('3')
	})

	it('announces the reason once, not once per second', async () => {
		const wrapper = mountNotice()
		const status = wrapper.get('[role="status"]')

		expect(status.classes()).toContain('sr-only')
		expect(status.text()).toBe('')

		await nextTick()
		const announced = status.text()
		expect(announced).toBe(
			'This lesson is locked. Taking you to your current lesson in 3 seconds.'
		)

		vi.advanceTimersByTime(2000)
		await nextTick()
		expect(status.text()).toBe(announced)
	})

	it('carries exactly one live region', () => {
		const wrapper = mountNotice()

		expect(wrapper.findAll('[role="status"]')).toHaveLength(1)
		expect(wrapper.findAll('[aria-live]')).toHaveLength(0)
	})

	it('emits done when the countdown reaches zero', async () => {
		const wrapper = mountNotice()

		vi.advanceTimersByTime(2000)
		expect(wrapper.emitted('done')).toBeUndefined()

		vi.advanceTimersByTime(1000)
		expect(wrapper.emitted('done')).toHaveLength(1)
	})

	it('renders no countdown and no live region when redirect is off', () => {
		const wrapper = mountNotice({ redirect: false })

		expect(wrapper.find('.tabular-nums').exists()).toBe(false)
		expect(wrapper.find('[role="status"]').exists()).toBe(false)
		expect(wrapper.text()).toContain('This lesson is locked')
	})

	it('reports the configured duration in the announcement', async () => {
		const wrapper = mountNotice({ seconds: 10 })

		await nextTick()
		expect(wrapper.get('[role="status"]').text()).toContain('in 10 seconds')
	})
})
