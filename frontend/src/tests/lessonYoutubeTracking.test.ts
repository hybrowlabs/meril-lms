import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Plyr is mocked the same way as plyr.test.ts: this suite only cares that
// enablePlyr finds the markup LessonContent renders, not what the player does.
const plyrCtor = vi.hoisted(() =>
	vi.fn(function FakePlyr(this: { on: () => void }) {
		this.on = () => {}
	})
)
vi.mock('plyr', () => ({ default: plyrCtor }))
vi.mock('plyr/dist/plyr.css', () => ({}))
vi.mock('@/stores/settings', () => ({
	useSettings: () => ({ settings: { data: {} } }),
}))
vi.mock('@/components/QuizBlock.vue', () => ({
	default: { props: ['quiz'], template: '<div class="quiz-stub" />' },
}))
vi.mock('@/components/PdfBlock.vue', () => ({
	default: { props: ['file'], template: '<div class="pdf-stub" />' },
}))

import LessonContent from '@/components/LessonContent.vue'
import { enablePlyr } from '@/utils/plyr'
import { shouldStartDwellTimer } from '@/utils/lessonProgress'

vi.stubGlobal('__', (s: string) => s)

const mountContent = (props: { content: string; youtube?: string }) =>
	mount(LessonContent, { props, attachTo: document.body })

describe('LessonContent renders tracked Plyr markup for YouTube', () => {
	beforeEach(() => {
		plyrCtor.mockClear()
		document.body.innerHTML = ''
	})

	it('renders the youtube field as a .video-player, not a bare iframe', () => {
		const wrapper = mountContent({
			content: 'Some intro text',
			youtube: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
		})

		const player = wrapper.get('.video-player')
		expect(player.attributes('data-plyr-provider')).toBe('youtube')
		expect(player.attributes('data-plyr-embed-id')).toBe('dQw4w9WgXcQ')
		expect(wrapper.find('iframe.youtube-video').exists()).toBe(false)
	})

	it.each([
		['https://www.youtube.com/watch?v=abc123XYZ_-', 'abc123XYZ_-'],
		['https://youtu.be/abc123XYZ_-', 'abc123XYZ_-'],
		['https://www.youtube.com/embed/abc123XYZ_-', 'abc123XYZ_-'],
		['https://www.youtube.com/watch?v=abc123XYZ_-&t=42s', 'abc123XYZ_-'],
		['abc123XYZ_-', 'abc123XYZ_-'],
	])('extracts the embed id from %s', (url, expected) => {
		const wrapper = mountContent({ content: 'text', youtube: url })
		expect(wrapper.get('.video-player').attributes('data-plyr-embed-id')).toBe(
			expected
		)
	})

	it('renders a {{ YouTubeVideo }} block as the same tracked markup', () => {
		const wrapper = mountContent({
			content: '{{ YouTubeVideo("https://www.youtube.com/watch?v=vid12345") }}',
		})

		const player = wrapper.get('.video-player')
		expect(player.attributes('data-plyr-provider')).toBe('youtube')
		expect(player.attributes('data-plyr-embed-id')).toBe('vid12345')
		expect(wrapper.find('iframe.youtube-video').exists()).toBe(false)
	})

	it('accepts a bare video id in the macro argument', () => {
		const wrapper = mountContent({ content: '{{ YouTubeVideo("vid12345") }}' })
		expect(wrapper.get('.video-player').attributes('data-plyr-embed-id')).toBe(
			'vid12345'
		)
	})

	it('renders nothing for a malformed macro rather than an empty player', () => {
		// An empty-id player would still count as a video and suppress the dwell
		// timer, leaving the lesson uncompletable.
		const wrapper = mountContent({ content: '{{ YouTubeVideo() }}' })
		expect(wrapper.find('.video-player').exists()).toBe(false)
	})

	it('renders no player when the lesson has no youtube field', () => {
		const wrapper = mountContent({ content: 'Just some prose.' })
		expect(wrapper.find('.video-player').exists()).toBe(false)
	})
})

describe('enforce_video_completion gates youtube-field lessons', () => {
	beforeEach(() => {
		plyrCtor.mockClear()
		document.body.innerHTML = ''
	})

	// Mirrors Lesson.vue: hasVideoListener = plyr instances || a <video> element.
	const hasVideoListener = (plyrSources: unknown[]) =>
		plyrSources.length > 0 || !!document.querySelector('video')

	it('suppresses the dwell timer for a youtube-field lesson', async () => {
		mountContent({
			content: 'Watch this.',
			youtube: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
		})

		const plyrSources = await enablePlyr()

		expect(plyrSources).toHaveLength(1)
		expect(
			shouldStartDwellTimer({
				hasVideo: hasVideoListener(plyrSources),
				enforceVideo: 1,
			})
		).toBe(false)
	})

	it('suppresses the dwell timer for a {{ YouTubeVideo }} lesson', async () => {
		mountContent({
			content: '{{ YouTubeVideo("https://www.youtube.com/watch?v=vid12345") }}',
		})

		const plyrSources = await enablePlyr()

		expect(plyrSources).toHaveLength(1)
		expect(
			shouldStartDwellTimer({
				hasVideo: hasVideoListener(plyrSources),
				enforceVideo: 1,
			})
		).toBe(false)
	})

	it('still runs the dwell timer for a lesson with no video at all', async () => {
		mountContent({ content: 'Just some prose.' })

		const plyrSources = await enablePlyr()

		expect(plyrSources).toHaveLength(0)
		expect(
			shouldStartDwellTimer({
				hasVideo: hasVideoListener(plyrSources),
				enforceVideo: 1,
			})
		).toBe(true)
	})
})
