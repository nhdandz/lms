import frappe

no_cache = 1


def get_context(context):
	lms_path = (frappe.conf.get("lms_path") or "lms").strip("/")
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = f"/{lms_path}/"
