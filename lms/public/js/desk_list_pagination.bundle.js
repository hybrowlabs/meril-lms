// Reusable page-based ("Previous / Next") pagination for Frappe desk list views.
//
// Frappe's stock list view uses an incremental "Load More" control pinned to the
// bottom of the list, which forces the user to scroll. This helper replaces that
// with a fixed-page-size Previous/Next paginator mounted in the list FOOTER
// (matching the DistributorManagement / Course Management portal pages).
//
// Usage (from a <doctype>_list.js onload):
//     frappe.lms.setup_list_pagination(listview, 20);
//     frappe.lms.setup_list_pagination(listview, 20, [20, 50, 100, 500]);

frappe.provide("frappe.lms");

frappe.lms.setup_list_pagination = function (listview, page_size, page_size_options) {
	page_size = page_size || 20;

	// Selectable page sizes. Always include the initial page_size so the
	// dropdown has a valid default selected.
	page_size_options = (page_size_options || [20, 50, 100, 500]).slice();
	if (!page_size_options.includes(page_size)) {
		page_size_options.push(page_size);
		page_size_options.sort((a, b) => a - b);
	}

	// List views can re-run onload; only wire this up once.
	if (listview.__lms_pagination_ready) return;
	listview.__lms_pagination_ready = true;

	listview._lms_page = 0;
	listview._lms_page_size = page_size;
	listview._lms_total = 0;
	// Force a fixed page size instead of Frappe's large-screen default of 100.
	listview.page_length = page_size;

	const size_options_html = page_size_options
		.map(
			(size) =>
				`<option value="${size}" ${size === page_size ? "selected" : ""}>${size}</option>`
		)
		.join("");

	const $paginator = $(`
		<div class="lms-list-paginator level" style="margin: 0 15px 12px;">
			<div class="level-left">
				<span class="lms-page-info text-muted small"></span>
			</div>
			<div class="level-right">
				<span class="text-muted small" style="margin-right: 6px;">${__("Rows per page")}</span>
				<select class="form-control input-sm lms-page-size" style="width: auto; margin-right: 12px;">
					${size_options_html}
				</select>
				<button class="btn btn-default btn-sm lms-prev-page" disabled>
					${__("Previous")}
				</button>
				<span class="lms-page-indicator text-muted small" style="margin: 0 12px;"></span>
				<button class="btn btn-default btn-sm lms-next-page">
					${__("Next")}
				</button>
			</div>
		</div>
	`);
	// Mount in the footer, where Frappe's default paging area lives.
	listview.$frappe_list.append($paginator);
	listview.$lms_paginator = $paginator;

	const hide_default_paging = () => {
		if (listview.$paging_area) listview.$paging_area.hide();
	};
	hide_default_paging();

	const total_pages = () =>
		Math.max(1, Math.ceil((listview._lms_total || 0) / listview._lms_page_size));

	const update_controls = () => {
		const page = listview._lms_page;
		const total = listview._lms_total || 0;
		const tp = total_pages();
		const start = total ? page * listview._lms_page_size + 1 : 0;
		const end = Math.min((page + 1) * listview._lms_page_size, total);

		$paginator
			.find(".lms-page-info")
			.text(total ? __("Showing {0}–{1} of {2}", [start, end, total]) : __("No records"));
		$paginator.find(".lms-page-indicator").text(__("Page {0} of {1}", [page + 1, tp]));
		$paginator.find(".lms-prev-page").prop("disabled", page <= 0);
		$paginator.find(".lms-next-page").prop("disabled", page + 1 >= tp);
	};

	// Fetch and render a single page (replaces the visible rows, no appending).
	const load_page = (page) => {
		page = Math.max(0, page);
		const args = Object.assign({}, listview.get_args(), {
			start: page * listview._lms_page_size,
			page_length: listview._lms_page_size,
		});
		listview.freeze(true);
		return frappe
			.call({ method: listview.method, args: args })
			.then((r) => {
				let data = r.message || {};
				data = !Array.isArray(data) ? frappe.utils.dict(data.keys, data.values) : data;
				listview._lms_page = page;
				listview.start = 0;
				listview.data = (data || []).uniqBy((d) => d.name);
				listview.render();
				listview.$result.toggle(listview.data.length > 0);
				listview.$no_result.toggle(listview.data.length === 0);
				hide_default_paging();
				update_controls();
			})
			.always(() => listview.freeze(false));
	};

	const refresh_total = () => {
		return frappe
			.call({
				method: "frappe.client.get_count",
				args: {
					doctype: listview.doctype,
					filters: listview.get_filters_for_args(),
				},
			})
			.then((r) => {
				listview._lms_total = cint(r.message);
				update_controls();
			});
	};

	$paginator.find(".lms-prev-page").on("click", () => load_page(listview._lms_page - 1));
	$paginator.find(".lms-next-page").on("click", () => load_page(listview._lms_page + 1));

	// Changing the page size resets to the first page and reloads.
	$paginator.find(".lms-page-size").on("change", function () {
		const new_size = cint($(this).val()) || page_size;
		listview._lms_page_size = new_size;
		listview.page_length = new_size;
		load_page(0);
	});

	// Whenever the stock list refreshes (filter/sort change, manual refresh),
	// snap back to page 1 and recompute the total for the new filter set.
	const original_refresh = listview.refresh.bind(listview);
	listview.refresh = function () {
		return original_refresh().then(() => {
			listview._lms_page = 0;
			// Keep our paginator pinned to the bottom after the list re-renders.
			listview.$lms_paginator && listview.$frappe_list.append(listview.$lms_paginator);
			hide_default_paging();
			return refresh_total();
		});
	};

	// In case the first stock refresh already fired before we wrapped it.
	refresh_total();
	update_controls();
};
