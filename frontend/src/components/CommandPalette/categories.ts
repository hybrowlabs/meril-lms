import {
	BookOpen,
	Briefcase,
	CircleHelp,
	Pencil,
	Route,
	Users,
} from 'lucide-vue-next'
import type { Component } from 'vue'

export interface Category {
	/** Sent to search_sqlite, which maps it to a doctype; never a doctype here. */
	id: string
	label: string
	icon: Component
	/** The category's own list page, and the sidebar entry it is gated by. */
	listRoute: string
}

/**
 * Visibility is taken from the sidebar rather than restated here: a category is
 * offered when the sidebar is offering its page to this user. That covers the
 * authoring surfaces (Quizzes and Assignments are instructor/moderator/evaluator
 * only) and Programs, which is hidden from guests and from students with no
 * programs, and it cannot drift from the sidebar the way a second copy of the
 * rules would. Hiding a row is a convenience either way — `get_grouped_results`
 * is what actually withholds records.
 */
export const CATEGORIES: Category[] = [
	{ id: 'courses', label: 'Courses', icon: BookOpen, listRoute: 'Courses' },
	{ id: 'batches', label: 'Batches', icon: Users, listRoute: 'Batches' },
	{ id: 'programs', label: 'Programs', icon: Route, listRoute: 'Programs' },
	{ id: 'jobs', label: 'Jobs', icon: Briefcase, listRoute: 'Jobs' },
	{ id: 'quizzes', label: 'Quizzes', icon: CircleHelp, listRoute: 'Quizzes' },
	{
		id: 'assignments',
		label: 'Assignments',
		icon: Pencil,
		listRoute: 'Assignments',
	},
]

interface SidebarItem {
	to?: string
}

interface SidebarGroup {
	items: SidebarItem[]
}

/** Categories whose page this user is being offered in the sidebar. */
export function visibleCategories(sidebarLinks: SidebarGroup[]): Category[] {
	const offered = new Set(
		(sidebarLinks ?? [])
			.flatMap((group) => group.items ?? [])
			.map((item) => item.to)
	)
	return CATEGORIES.filter((category) => offered.has(category.listRoute))
}

export function categoryById(id: string | null): Category | undefined {
	if (!id) return undefined
	return CATEGORIES.find((category) => category.id === id)
}
