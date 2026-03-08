# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LMSDocumentCategory(Document):
	def validate(self):
		self.validate_unique_name_in_parent()

	def validate_unique_name_in_parent(self):
		filters = {
			"category_name": self.category_name,
			"parent_category": self.parent_category,
			"name": ("!=", self.name),
		}
		existing = frappe.db.exists("LMS Document Category", filters)
		if existing:
			parent_label = self.parent_category or _("root")
			frappe.throw(
				_("A folder named '{0}' already exists in '{1}'").format(
					self.category_name, parent_label
				)
			)
