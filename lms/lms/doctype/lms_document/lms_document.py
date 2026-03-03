# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class LMSDocument(Document):
	def before_save(self):
		if self.file:
			self.set_file_info()

	def set_file_info(self):
		"""Auto-detect file type and size from the attached file."""
		file_doc = frappe.db.get_value(
			"File",
			{"file_url": self.file},
			["file_name", "file_size"],
			as_dict=True,
		)

		if file_doc:
			# Extract file extension
			file_name = file_doc.get("file_name", "")
			if "." in file_name:
				self.file_type = file_name.rsplit(".", 1)[1].upper()
			else:
				self.file_type = "Unknown"

			# Set file size
			file_size = file_doc.get("file_size", 0)
			self.file_size = self.format_file_size(file_size)

	def format_file_size(self, size):
		"""Format file size to human readable format."""
		if not size:
			return "0 B"

		size = int(size)
		if size >= 1048576:  # 1 MB
			return f"{size / 1048576:.2f} MB"
		elif size >= 1024:  # 1 KB
			return f"{size / 1024:.2f} KB"
		else:
			return f"{size} B"

	def validate(self):
		if not self.title:
			frappe.throw(_("Title is required"))

		if not self.file:
			frappe.throw(_("File is required"))
