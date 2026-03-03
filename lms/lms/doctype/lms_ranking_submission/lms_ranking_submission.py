# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class LMSRankingSubmission(Document):
	def before_save(self):
		self.calculate_percentage()
		self.auto_approve_if_not_required()

	def calculate_percentage(self):
		"""Calculate percentage based on score and max_score"""
		if self.score and self.max_score and self.max_score > 0:
			self.percentage = (self.score / self.max_score) * 100
		else:
			self.percentage = 0

	def auto_approve_if_not_required(self):
		"""Auto-approve if the category doesn't require approval"""
		if self.is_new():
			category = frappe.get_doc("LMS Document Category", self.category)
			if not category.require_approval:
				self.status = "Approved"
				self.approved_by = frappe.session.user
				self.approved_on = now_datetime()

	def validate(self):
		self.validate_category()
		self.validate_duplicate()
		self.validate_deadline()

	def validate_category(self):
		"""Ensure the category has ranking enabled"""
		category = frappe.get_doc("LMS Document Category", self.category)
		if not category.is_ranking_enabled:
			frappe.throw("This folder does not have ranking enabled")

	def validate_duplicate(self):
		"""Check for duplicate submissions from same member"""
		if self.is_new():
			existing = frappe.db.exists(
				"LMS Ranking Submission",
				{
					"category": self.category,
					"member": self.member,
					"name": ("!=", self.name)
				}
			)
			if existing:
				frappe.throw(
					f"You have already submitted a score for this contest. "
					f"Please update your existing submission instead."
				)

	def validate_deadline(self):
		"""Check if submission is within deadline"""
		category = frappe.get_doc("LMS Document Category", self.category)
		if category.submission_deadline:
			if now_datetime() > category.submission_deadline:
				frappe.throw("The submission deadline has passed")

	def on_update(self):
		"""Clear cache when submission is updated"""
		frappe.cache().delete_key(f"ranking_leaderboard_{self.category}")
