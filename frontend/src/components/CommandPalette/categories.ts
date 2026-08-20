import {
	BookOpen,
	Briefcase,
	CircleHelp,
	Code,
	GraduationCap,
	Home,
	Pencil,
	Route,
	TrendingUp,
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

function offeredRoutes(sidebarLinks: SidebarGroup[]): Set<string | undefined> {
	return new Set(
		(sidebarLinks ?? [])
			.flatMap((group) => group.items ?? [])
			.map((item) => item.to)
	)
}

/** Categories whose page this user is being offered in the sidebar. */
export function visibleCategories(sidebarLinks: SidebarGroup[]): Category[] {
	const offered = offeredRoutes(sidebarLinks)
	return CATEGORIES.filter((category) => offered.has(category.listRoute))
}

export function categoryById(id: string | null): Category | undefined {
	if (!id) return undefined
	return CATEGORIES.find((category) => category.id === id)
}

export interface NavTarget {
	id: string
	label: string
	icon: Component
	/** Route name. Selecting the row goes straight here. */
	route: string
}

/**
 * Sidebar pages with no records behind them, so there is nothing to scope a
 * search to — the row navigates instead of drilling in.
 *
 * Listed by hand rather than derived from the sidebar, because a sidebar `to`
 * is not always a route name: Contact Us carries a URL or a mailto address,
 * and pushing either as a route name lands nowhere.
 */
export const NAV_TARGETS: NavTarget[] = [
	{ id: 'home', label: 'Home', icon: Home, route: 'Home' },
	{
		id: 'certifications',
		label: 'Certifications',
		icon: GraduationCap,
		route: 'CertifiedParticipants',
	},
	{
		id: 'statistics',
		label: 'Statistics',
		icon: TrendingUp,
		route: 'Statistics',
	},
	{
		id: 'programming-exercises',
		label: 'Programming Exercises',
		icon: Code,
		route: 'ProgrammingExercises',
	},
]

/** Nav targets whose page this user is being offered in the sidebar. */
export function visibleNavTargets(sidebarLinks: SidebarGroup[]): NavTarget[] {
	const offered = offeredRoutes(sidebarLinks)
	return NAV_TARGETS.filter((target) => offered.has(target.route))
}
