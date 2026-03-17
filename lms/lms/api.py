"""API methods for the LMS."""

import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from datetime import timedelta
from xml.dom.minidom import parseString

import frappe
from frappe import _
from frappe.integrations.frappe_providers.frappecloud_billing import (
	current_site_info,
	is_fc_site,
)
from frappe.translate import get_all_translations
from frappe.utils import (
	add_days,
	cint,
	date_diff,
	flt,
	format_date,
	get_datetime,
	getdate,
	now,
)
from frappe.utils.response import Response
from pypika import functions as fn

from lms.lms.doctype.course_lesson.course_lesson import save_progress
from lms.lms.utils import (
	can_modify_batch,
	can_modify_course,
	get_average_rating,
	get_batch_details,
	get_course_details,
	get_instructors,
	get_lesson_count,
	get_lms_route,
	has_course_instructor_role,
	has_evaluator_role,
	has_moderator_role,
)


@frappe.whitelist()
def get_user_info():
	if frappe.session.user == "Guest":
		return None

	user = frappe.db.get_value(
		"User",
		frappe.session.user,
		["name", "email", "enabled", "user_image", "full_name", "user_type", "username"],
		as_dict=1,
	)
	user["roles"] = frappe.get_roles(user.name)
	user.is_instructor = "Course Creator" in user.roles
	user.is_moderator = "Moderator" in user.roles
	user.is_evaluator = "Batch Evaluator" in user.roles
	user.is_student = not user.is_instructor and not user.is_moderator and not user.is_evaluator
	user.is_fc_site = is_fc_site()
	user.is_system_manager = "System Manager" in user.roles
	user.sitename = frappe.local.site
	user.developer_mode = frappe.conf.developer_mode
	if user.is_fc_site and user.is_system_manager:
		user.site_info = current_site_info()
	return user


@frappe.whitelist(allow_guest=True)
def get_translations():
	if frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")
	return get_all_translations(language)


@frappe.whitelist()
def validate_billing_access(billing_type, name):
	doctype = "LMS Batch" if billing_type == "batch" else "LMS Course"
	access, message = verify_billing_access(doctype, name, billing_type)

	address = frappe.db.get_value(
		"Address",
		{"email_id": frappe.session.user},
		[
			"name",
			"address_title as billing_name",
			"address_line1",
			"address_line2",
			"city",
			"state",
			"country",
			"pincode",
			"phone",
		],
		as_dict=1,
	)

	return {"access": access, "message": message, "address": address}


def verify_billing_access(doctype, name, billing_type):
	access = True
	message = ""

	if frappe.session.user == "Guest":
		access = False
		message = _("Please login to continue with payment.")

	if access and billing_type not in ["course", "batch", "certificate"]:
		access = False
		message = _("Module is incorrect.")

	if access and not frappe.db.exists(doctype, name):
		access = False
		message = _("Module Name is incorrect or does not exist.")

	if access and billing_type == "course":
		membership = frappe.db.exists("LMS Enrollment", {"member": frappe.session.user, "course": name})
		if membership:
			access = False
			message = _("You are already enrolled for this course.")

	elif access and billing_type == "batch":
		membership = frappe.db.exists("LMS Batch Enrollment", {"member": frappe.session.user, "batch": name})
		if membership:
			access = False
			message = _("You are already enrolled for this batch.")

		seat_count = frappe.get_cached_value("LMS Batch", name, "seat_count")
		number_of_students = frappe.db.count("LMS Batch Enrollment", {"batch": name})
		if seat_count <= number_of_students:
			access = False
			message = _("Batch is sold out.")

		start_date = frappe.get_cached_value("LMS Batch", name, "start_date")
		if start_date and date_diff(start_date, now()) < 0:
			access = False
			message = _("Batch has already started.")

	elif access and billing_type == "certificate":
		purchased_certificate = frappe.db.exists(
			"LMS Enrollment",
			{
				"course": name,
				"member": frappe.session.user,
				"purchased_certificate": 1,
			},
		)
		if purchased_certificate:
			access = False
			message = _("You have already purchased the certificate for this course.")

	return access, message


@frappe.whitelist(allow_guest=True)
def get_job_details(job):
	return frappe.db.get_value(
		"Job Opportunity",
		job,
		[
			"job_title",
			"location",
			"country",
			"type",
			"work_mode",
			"company_name",
			"company_logo",
			"company_website",
			"name",
			"creation",
			"description",
			"owner",
		],
		as_dict=1,
	)


@frappe.whitelist(allow_guest=True)
def get_job_opportunities(filters=None, orFilters=None):
	if not filters:
		filters = {}

	jobs = frappe.get_all(
		"Job Opportunity",
		filters=filters,
		or_filters=orFilters,
		fields=[
			"job_title",
			"location",
			"country",
			"type",
			"work_mode",
			"company_name",
			"company_logo",
			"name",
			"creation",
			"description",
		],
		order_by="creation desc",
	)

	for job in jobs:
		job.description = frappe.utils.strip_html_tags(job.description)
		job.applicants = frappe.db.count("LMS Job Application", {"job": job.name})
	return jobs


@frappe.whitelist(allow_guest=True)
def get_chart_details():
	details = frappe._dict()
	details.enrollments = frappe.db.count("LMS Enrollment")
	details.courses = frappe.db.count(
		"LMS Course",
		{
			"published": 1,
			"upcoming": 0,
		},
	)
	details.users = frappe.db.count("User", {"enabled": 1, "name": ["not in", ("Administrator", "Guest")]})
	details.completions = frappe.db.count("LMS Enrollment", {"progress": ["like", "%100%"]})
	details.certifications = frappe.db.count("LMS Certificate", {"published": 1})
	return details


def get_file_info(file_url):
	"""Get file info for the given file URL."""
	file_info = frappe.db.get_value(
		"File", {"file_url": file_url}, ["file_name", "file_size", "file_url"], as_dict=1
	)
	return file_info


@frappe.whitelist(allow_guest=True)
def get_branding():
	"""Get branding details."""
	fields = ["app_name"]
	image_fields = ["banner_image", "footer_logo", "favicon", "app_logo"]
	fields = fields + image_fields
	settings = frappe._dict()

	for field in fields:
		value = frappe.get_cached_value("Website Settings", None, field)
		if field in image_fields and value:
			file_info = get_file_info(value)
			settings.update({field: json.loads(json.dumps(file_info))})
		else:
			settings.update({field: value})

	return settings


@frappe.whitelist()
def get_unsplash_photos(keyword=None):
	from lms.unsplash import get_by_keyword, get_list

	if keyword:
		return get_by_keyword(keyword)

	return frappe.cache().get_value("unsplash_photos", generator=get_list)


@frappe.whitelist()
def get_evaluator_details(evaluator):
	frappe.only_for("Batch Evaluator")

	if not frappe.db.exists("Google Calendar", {"user": evaluator}):
		calendar = frappe.new_doc("Google Calendar")
		calendar.update({"user": evaluator, "calendar_name": evaluator})
		calendar.insert()
	else:
		calendar = frappe.db.get_value(
			"Google Calendar", {"user": evaluator}, ["name", "authorization_code"], as_dict=1
		)

	if frappe.db.exists("Course Evaluator", {"evaluator": evaluator}):
		doc = frappe.get_doc("Course Evaluator", evaluator)
	else:
		doc = frappe.new_doc("Course Evaluator")
		doc.evaluator = evaluator
		doc.insert()

	return {
		"slots": doc.as_dict(),
		"calendar": calendar.name,
		"is_authorised": calendar.authorization_code,
	}


@frappe.whitelist()
def get_certified_participants(filters=None, start=0, page_length=100):
	query = get_certification_query(filters)
	query = query.orderby("issue_date", order=frappe.qb.desc).offset(start).limit(page_length)
	participants = query.run(as_dict=True)

	for participant in participants:
		details = get_certified_participant_details(participant.member)
		participant.update(details)

	return participants


def get_certified_participant_details(member):
	count = frappe.db.count("LMS Certificate", {"member": member})
	details = frappe.db.get_value(
		"User",
		member,
		["full_name", "user_image", "username", "country", "headline", "open_to"],
		as_dict=1,
	)
	details["certificate_count"] = count
	return details


def get_certification_query(filters):
	Certificate = frappe.qb.DocType("LMS Certificate")
	User = frappe.qb.DocType("User")

	query = (
		frappe.qb.from_(Certificate)
		.select(Certificate.member)
		.distinct()
		.join(User)
		.on(Certificate.member == User.name)
		.where(Certificate.published == 1)
		.where(User.enabled == 1)
	)

	if filters:
		for field, value in filters.items():
			if field == "category":
				query = query.where(
					Certificate.course_title.like(f"%{value}%") | Certificate.batch_title.like(f"%{value}%")
				)
			if field == "member_name":
				query = query.where(Certificate.member_name.like(value[1]))
			if field == "open_to_work":
				query = query.where(User.open_to == "Work")
			if field == "hiring":
				query = query.where(User.open_to == "Hiring")
	return query


@frappe.whitelist()
def get_count_of_certified_members(filters=None):
	query = get_certification_query(filters)
	result = query.run(as_dict=True)
	return len(result) or 0


@frappe.whitelist()
def get_certification_categories():
	categories = []
	seen = set()
	docs = frappe.get_all(
		"LMS Certificate",
		filters={
			"published": 1,
		},
		fields=["course_title", "batch_title"],
	)

	for doc in docs:
		category = doc.course_title if doc.course_title else doc.batch_title
		if not category or category in seen:
			continue

		seen.add(category)
		categories.append({"label": category, "value": category})
	return categories


@frappe.whitelist()
def get_all_users():
	frappe.only_for(["Moderator", "Course Creator", "Batch Evaluator"])
	users = frappe.get_all(
		"User",
		{
			"enabled": 1,
		},
		["name", "full_name", "user_image"],
	)

	return {user.name: user for user in users}


@frappe.whitelist(allow_guest=True)
def get_sidebar_settings():
	lms_settings = frappe.get_single("LMS Settings")
	if not lms_settings.allow_guest_access:
		return []

	sidebar_items = frappe._dict()
	items = [
		"courses",
		"batches",
		"certifications",
		"jobs",
		"statistics",
		"notifications",
		"programming_exercises",
		"documents",
	]
	for item in items:
		sidebar_items[item] = lms_settings.get(item)

	if len(lms_settings.sidebar_items):
		web_pages = frappe.get_all(
			"LMS Sidebar Item",
			{"parenttype": "LMS Settings", "parentfield": "sidebar_items"},
			["web_page", "route", "title as label", "icon", "name"],
		)
		for page in web_pages:
			page.to = page.route

		sidebar_items.web_pages = web_pages

	return sidebar_items


@frappe.whitelist()
def update_sidebar_item(webpage, icon):
	frappe.only_for("Moderator")
	filters = {
		"web_page": webpage,
		"parenttype": "LMS Settings",
		"parentfield": "sidebar_items",
		"parent": "LMS Settings",
	}

	if frappe.db.exists("LMS Sidebar Item", filters):
		frappe.db.set_value("LMS Sidebar Item", filters, "icon", icon)
	else:
		doc = frappe.new_doc("LMS Sidebar Item")
		doc.update(filters)
		doc.icon = icon
		doc.insert()


@frappe.whitelist()
def delete_sidebar_item(webpage):
	frappe.only_for("Moderator")
	return frappe.db.delete(
		"LMS Sidebar Item",
		{
			"web_page": webpage,
			"parenttype": "LMS Settings",
			"parentfield": "sidebar_items",
			"parent": "LMS Settings",
		},
	)


@frappe.whitelist()
def delete_lesson(lesson, chapter):
	course = frappe.db.get_value("Course Chapter", chapter, "course")
	if not can_modify_course(course):
		frappe.throw(_("You do not have permission to delete this lesson."), frappe.PermissionError)

	lessons = frappe.get_all(
		"Lesson Reference",
		{"parent": chapter},
		pluck="lesson",
		order_by="idx",
	)
	lessons.remove(lesson)
	frappe.db.delete("Lesson Reference", {"parent": chapter, "lesson": lesson})
	update_index(lessons, chapter)

	frappe.db.delete("LMS Course Progress", {"lesson": lesson})
	frappe.db.delete("Course Lesson", lesson)


@frappe.whitelist()
def update_lesson_index(lesson, sourceChapter, targetChapter, idx):
	course = frappe.db.get_value("Course Chapter", sourceChapter, "course")
	if not can_modify_course(course):
		frappe.throw(_("You do not have permission to modify this lesson."), frappe.PermissionError)

	hasMoved = sourceChapter == targetChapter
	update_source_chapter(lesson, sourceChapter, idx, hasMoved)
	if not hasMoved:
		update_target_chapter(lesson, targetChapter, idx)


def update_source_chapter(lesson, chapter, idx, hasMoved=False):
	lessons = frappe.get_all(
		"Lesson Reference",
		{
			"parent": chapter,
		},
		pluck="lesson",
		order_by="idx",
	)

	lessons.remove(lesson)
	if not hasMoved:
		frappe.db.delete("Lesson Reference", {"parent": chapter, "lesson": lesson})
	else:
		lessons.insert(idx, lesson)

	update_index(lessons, chapter)


def update_target_chapter(lesson, chapter, idx):
	lessons = frappe.get_all(
		"Lesson Reference",
		{
			"parent": chapter,
		},
		pluck="lesson",
		order_by="idx",
	)

	lessons.insert(idx, lesson)
	new_lesson_reference = frappe.new_doc("Lesson Reference")
	new_lesson_reference.update(
		{
			"lesson": lesson,
			"parent": chapter,
			"parenttype": "Course Chapter",
			"parentfield": "lessons",
		}
	)
	new_lesson_reference.insert()
	update_index(lessons, chapter)


def update_index(lessons, chapter):
	for row in lessons:
		frappe.db.set_value(
			"Lesson Reference", {"lesson": row, "parent": chapter}, "idx", lessons.index(row) + 1
		)


@frappe.whitelist()
def update_chapter_index(chapter, course, idx):
	"""Update the index of a chapter within a course"""

	if not can_modify_course(course):
		frappe.throw(_("You do not have permission to modify this chapter."), frappe.PermissionError)

	chapters = frappe.get_all(
		"Chapter Reference",
		{"parent": course},
		pluck="chapter",
		order_by="idx",
	)

	if chapter in chapters:
		chapters.remove(chapter)

	chapters.insert(idx, chapter)

	for i, chapter_name in enumerate(chapters):
		frappe.db.set_value("Chapter Reference", {"chapter": chapter_name, "parent": course}, "idx", i + 1)


@frappe.whitelist()
def get_members(start=0, search=""):
	frappe.only_for(["Moderator"])
	filters = {"enabled": 1, "name": ["not in", ["Administrator", "Guest"]]}
	or_filters = {}

	if search:
		or_filters["full_name"] = ["like", f"%{search}%"]
		or_filters["email"] = ["like", f"%{search}%"]

	members = frappe.get_all(
		"User",
		filters=filters,
		fields=["name", "full_name", "user_image", "username", "last_active"],
		or_filters=or_filters,
		page_length=20,
		start=start,
	)

	for member in members:
		roles = frappe.get_all(
			"Has Role",
			{
				"parent": member.name,
				"parenttype": "User",
			},
			pluck="role",
		)
		if "Moderator" in roles:
			member.role = "Moderator"
		elif "Course Creator" in roles:
			member.role = "Course Creator"
		elif "Batch Evaluator" in roles:
			member.role = "Batch Evaluator"
		elif "LMS Student" in roles:
			member.role = "LMS Student"

	return members


def check_app_permission():
	"""Check if the user has permission to access the app."""
	if frappe.session.user == "Administrator":
		return True

	roles = frappe.get_roles()
	lms_roles = ["Moderator", "Course Creator", "Batch Evaluator", "LMS Student"]
	if any(role in roles for role in lms_roles):
		return True

	return False


@frappe.whitelist()
def save_evaluation_details(
	member,
	course,
	batch_name,
	evaluator,
	date,
	start_time,
	end_time,
	status,
	rating,
	summary,
):
	"""
	Save evaluation details for a member against a course.
	"""
	frappe.only_for(["Batch Evaluator", "Moderator"])
	evaluation = frappe.db.exists("LMS Certificate Evaluation", {"member": member, "course": course})

	details = {
		"date": date,
		"start_time": start_time,
		"end_time": end_time,
		"status": status,
		"rating": rating / 5,
		"summary": summary,
		"batch_name": batch_name,
	}

	if evaluation:
		frappe.db.set_value("LMS Certificate Evaluation", evaluation, details)
		return evaluation
	else:
		doc = frappe.new_doc("LMS Certificate Evaluation")
		details.update(
			{
				"member": member,
				"course": course,
				"evaluator": evaluator,
			}
		)
		doc.update(details)
		doc.insert()
		return doc.name


@frappe.whitelist()
def save_certificate_details(
	member,
	course,
	batch_name,
	evaluator,
	issue_date,
	expiry_date,
	template,
	published=True,
):
	"""
	Save certificate details for a member against a course.
	"""
	frappe.only_for(["Batch Evaluator", "Moderator"])
	certificate = frappe.db.exists("LMS Certificate", {"member": member, "course": course})

	details = {
		"published": published,
		"issue_date": issue_date,
		"expiry_date": expiry_date,
		"template": template,
		"batch_name": batch_name,
	}

	if certificate:
		frappe.db.set_value("LMS Certificate", certificate, details)
		return certificate
	else:
		doc = frappe.new_doc("LMS Certificate")
		details.update(
			{
				"member": member,
				"course": course,
				"evaluator": evaluator,
			}
		)
		doc.update(details)
		doc.insert()
		return doc.name


@frappe.whitelist()
def delete_documents(doctype, documents):
	frappe.only_for("Moderator")
	for doc in documents:
		frappe.delete_doc(doctype, doc)


@frappe.whitelist()
def get_payment_gateway_details(payment_gateway):
	frappe.only_for("Moderator")
	gateway = frappe.get_doc("Payment Gateway", payment_gateway)

	if gateway.gateway_controller is None:
		try:
			data = frappe.get_doc(f"{payment_gateway} Settings").as_dict()
			meta = frappe.get_meta(f"{payment_gateway} Settings").fields
			doctype = f"{payment_gateway} Settings"
			docname = f"{payment_gateway} Settings"
		except Exception:
			frappe.throw(_("{0} Settings not found").format(payment_gateway))
	else:
		try:
			data = frappe.get_doc(gateway.gateway_settings, gateway.gateway_controller).as_dict()
			meta = frappe.get_meta(gateway.gateway_settings).fields
			doctype = gateway.gateway_settings
			docname = gateway.gateway_controller
		except Exception:
			frappe.throw(_("{0} Settings not found").format(payment_gateway))

	gateway_fields = get_transformed_fields(meta, data)

	return {
		"fields": gateway_fields,
		"data": data,
		"doctype": doctype,
		"docname": docname,
	}


def get_transformed_fields(meta, data=None):
	transformed_fields = []
	for row in meta:
		if row.fieldtype not in ["Column Break", "Section Break"]:
			if row.fieldtype in ["Attach", "Attach Image"]:
				fieldtype = "Upload"
				if data and data.get(row.fieldname):
					data[row.fieldname] = get_file_info(data.get(row.fieldname))
			elif row.fieldtype == "Check":
				fieldtype = "checkbox"
			else:
				fieldtype = row.fieldtype

			transformed_fields.append(
				{
					"label": row.label,
					"name": row.fieldname,
					"type": fieldtype,
				}
			)

	return transformed_fields


@frappe.whitelist()
def get_new_gateway_fields(doctype):
	frappe.only_for("Moderator")
	try:
		meta = frappe.get_meta(doctype).fields
	except Exception:
		frappe.throw(_("{0} not found").format(doctype))

	transformed_fields = get_transformed_fields(meta)

	return transformed_fields


def update_course_statistics():
	courses = frappe.get_all("LMS Course", fields=["name"])

	for course in courses:
		lessons = get_lesson_count(course.name)

		enrollments = frappe.db.count("LMS Enrollment", {"course": course.name, "member_type": "Student"})

		avg_rating = get_average_rating(course.name) or 0
		avg_rating = flt(avg_rating, frappe.get_system_settings("float_precision") or 3)

		frappe.db.set_value(
			"LMS Course",
			course.name,
			{"lessons": lessons, "enrollments": enrollments, "rating": avg_rating},
		)


@frappe.whitelist()
def get_announcements(batch):
	roles = frappe.get_roles()
	is_batch_student = frappe.db.exists(
		"LMS Batch Enrollment", {"batch": batch, "member": frappe.session.user}
	)
	is_moderator = "Moderator" in roles
	is_evaluator = "Batch Evaluator" in roles

	if not (is_batch_student or is_moderator or is_evaluator):
		frappe.throw(
			_("You do not have permission to access announcements for this batch."), frappe.PermissionError
		)

	communications = frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": "LMS Batch",
			"reference_name": batch,
		},
		fields=[
			"subject",
			"content",
			"recipients",
			"cc",
			"communication_date",
			"sender",
			"sender_full_name",
		],
		order_by="communication_date desc",
	)

	for communication in communications:
		communication.image = frappe.get_cached_value("User", communication.sender, "user_image")

	return communications


@frappe.whitelist()
def delete_course(course):
	if not can_modify_course(course):
		frappe.throw(_("You do not have permission to delete this course."), frappe.PermissionError)

	frappe.db.delete("LMS Enrollment", {"course": course})
	frappe.db.delete("LMS Course Progress", {"course": course})
	frappe.db.set_value("LMS Quiz", {"course": course}, "course", None)
	frappe.db.set_value("LMS Quiz Submission", {"course": course}, "course", None)

	chapters = frappe.get_all("Course Chapter", {"course": course}, pluck="name")
	frappe.db.delete("Chapter Reference", {"parent": course})

	for chapter in chapters:
		lessons = frappe.get_all("Course Lesson", {"chapter": chapter}, pluck="name")

		frappe.db.delete("Lesson Reference", {"parent": chapter})

		for lesson in lessons:
			topics = frappe.get_all(
				"Discussion Topic",
				{"reference_doctype": "Course Lesson", "reference_docname": lesson},
				pluck="name",
			)

			for topic in topics:
				frappe.db.delete("Discussion Reply", {"topic": topic})
				frappe.db.delete("Discussion Topic", topic)

			frappe.delete_doc("Course Lesson", lesson)

	for chapter in chapters:
		frappe.delete_doc("Course Chapter", chapter)

	frappe.delete_doc("LMS Course", course)


@frappe.whitelist()
def delete_batch(batch):
	if not can_modify_batch(batch):
		frappe.throw(_("You do not have permission to delete this batch."), frappe.PermissionError)

	frappe.db.delete("LMS Batch Enrollment", {"batch": batch})
	frappe.db.delete("Batch Course", {"parent": batch, "parenttype": "LMS Batch"})
	frappe.db.delete("LMS Assessment", {"parent": batch, "parenttype": "LMS Batch"})
	frappe.db.delete("LMS Batch Timetable", {"parent": batch, "parenttype": "LMS Batch"})
	frappe.db.delete("LMS Batch Feedback", {"batch": batch})
	delete_batch_discussions(batch)
	frappe.db.delete("LMS Batch", batch)


def delete_batch_discussions(batch):
	topics = frappe.get_all(
		"Discussion Topic",
		{"reference_doctype": "LMS Batch", "reference_docname": batch},
		pluck="name",
	)

	for topic in topics:
		frappe.db.delete("Discussion Reply", {"topic": topic})
		frappe.db.delete("Discussion Topic", topic)


def give_discussions_permission():
	doctypes = ["Discussion Topic", "Discussion Reply"]
	roles = ["LMS Student", "Course Creator", "Moderator", "Batch Evaluator"]
	for doctype in doctypes:
		for role in roles:
			if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
				frappe.get_doc(
					{
						"doctype": "Custom DocPerm",
						"parent": doctype,
						"role": role,
						"read": 1,
						"write": 1,
						"create": 1,
						"delete": 1,
						"if_owner": 0 if role == "Moderator" else 1,
					}
				).save(ignore_permissions=True)


@frappe.whitelist()
def upsert_chapter(title, course, is_scorm_package, scorm_package, name=None):
	if not can_modify_course(course):
		frappe.throw(_("You do not have permission to modify this chapter."), frappe.PermissionError)

	values = frappe._dict({"title": title, "course": course, "is_scorm_package": is_scorm_package})

	if is_scorm_package:
		scorm_package = frappe._dict(scorm_package)
		extract_path = extract_package(course, title, scorm_package)

		values.update(
			{
				"scorm_package": scorm_package.name,
				"scorm_package_path": extract_path.split("public")[1],
				"manifest_file": get_manifest_file(extract_path).split("public")[1],
				"launch_file": get_launch_file(extract_path).split("public")[1],
			}
		)

	if name:
		chapter = frappe.get_doc("Course Chapter", name)
	else:
		chapter = frappe.new_doc("Course Chapter")

	chapter.update(values)
	chapter.save()

	if is_scorm_package and not len(chapter.lessons):
		add_lesson(title, chapter.name, course, 1)

	return chapter


def extract_package(course, title, scorm_package):
	package = frappe.get_doc("File", scorm_package.name)
	zip_path = package.get_full_path()
	# check_for_malicious_code(zip_path)
	extract_path = frappe.get_site_path("public", "scorm", course, title)
	zipfile.ZipFile(zip_path).extractall(extract_path)
	return extract_path


def check_for_malicious_code(zip_path):
	suspicious_patterns = [
		# Unsafe inline JavaScript
		r'on(click|load|mouseover|error|submit|focus|blur|change|keyup|keydown|keypress|resize)=".*?"',  # Inline event handlers (e.g., onerror, onclick)
		r'<script.*?src=["\']http',  # External script tags
		r"eval\(",  # Usage of eval()
		r"Function\(",  # Usage of Function constructor
		r"(btoa|atob)\(",  # Base64 encoding/decoding
		# Dangerous XML patterns
		r"<!ENTITY",  # XXE-related
		r"<\?xml-stylesheet .*?>",  # External stylesheets in XML
	]

	with zipfile.ZipFile(zip_path, "r") as zf:
		for file_name in zf.namelist():
			if file_name.endswith((".html", ".js", ".xml")):
				with zf.open(file_name) as file:
					content = file.read().decode("utf-8", errors="ignore")
					for pattern in suspicious_patterns:
						if re.search(pattern, content):
							frappe.throw(_("Suspicious pattern found in {0}: {1}").format(file_name, pattern))


def get_manifest_file(extract_path):
	manifest_file = None
	for root, _dirs, files in os.walk(extract_path):
		for file in files:
			if file == "imsmanifest.xml":
				manifest_file = os.path.join(root, file)
				break
		if manifest_file:
			break
	return manifest_file


def get_launch_file(extract_path):
	launch_file = None
	manifest_file = get_manifest_file(extract_path)

	if manifest_file:
		with open(manifest_file) as file:
			data = file.read()
			dom = parseString(data)
			resource = dom.getElementsByTagName("resource")
			for res in resource:
				if (
					res.getAttribute("adlcp:scormtype") == "sco"
					or res.getAttribute("adlcp:scormType") == "sco"
				):
					launch_file = res.getAttribute("href")
					break

		if launch_file:
			launch_file = os.path.join(os.path.dirname(manifest_file), launch_file)

	return launch_file


def add_lesson(title, chapter, course, idx):
	lesson = frappe.new_doc("Course Lesson")
	lesson.update(
		{
			"title": title,
			"chapter": chapter,
			"course": course,
		}
	)
	lesson.insert()

	lesson_reference = frappe.new_doc("Lesson Reference")
	lesson_reference.update(
		{
			"lesson": lesson.name,
			"idx": idx,
			"parent": chapter,
			"parenttype": "Course Chapter",
			"parentfield": "lessons",
		}
	)
	lesson_reference.insert()


@frappe.whitelist()
def delete_chapter(chapter):
	course = frappe.db.get_value("Course Chapter", chapter, "course")
	if not can_modify_course(course):
		frappe.throw(_("You do not have permission to delete this chapter."), frappe.PermissionError)

	chapterInfo = frappe.db.get_value(
		"Course Chapter", chapter, ["is_scorm_package", "scorm_package_path"], as_dict=True
	)

	if chapterInfo.is_scorm_package:
		delete_scorm_package(chapterInfo.scorm_package_path)

	course = frappe.db.get_value("Chapter Reference", {"chapter": chapter}, "parent")

	frappe.db.delete("Chapter Reference", {"chapter": chapter})
	frappe.db.delete("Lesson Reference", {"parent": chapter})
	frappe.db.delete("Course Lesson", {"chapter": chapter})
	frappe.db.delete("Course Chapter", chapter)

	# reset chapter reference index after deletion
	if course:
		chapters = frappe.get_all(
			"Chapter Reference", filters={"parent": course}, fields=["name"], order_by="idx asc"
		)

		i = 1
		for chapter in chapters:
			frappe.db.set_value("Chapter Reference", chapter.name, "idx", i)
			i += 1


def delete_scorm_package(scorm_package_path):
	scorm_package_path = frappe.get_site_path("public", scorm_package_path[1:])
	if os.path.exists(scorm_package_path):
		shutil.rmtree(scorm_package_path)


@frappe.whitelist()
def mark_lesson_progress(course, chapter_number, lesson_number):
	chapter_name = frappe.get_value("Chapter Reference", {"parent": course, "idx": chapter_number}, "chapter")
	lesson_name = frappe.get_value(
		"Lesson Reference", {"parent": chapter_name, "idx": lesson_number}, "lesson"
	)
	save_progress(lesson_name, course)


@frappe.whitelist()
def get_heatmap_data(member, base_days=200):
	if not (has_course_instructor_role() or has_moderator_role() or has_evaluator_role()):
		frappe.throw(_("You do not have permission to access heatmap data."), frappe.PermissionError)

	base_date, start_date, number_of_days, days = calculate_date_ranges(base_days)
	date_count = initialize_date_count(days)

	lesson_completions, quiz_submissions, assignment_submissions = fetch_activity_data(member, start_date)
	count_dates(lesson_completions, date_count)
	count_dates(quiz_submissions, date_count)
	count_dates(assignment_submissions, date_count)

	heatmap_data, labels, total_activities, weeks = prepare_heatmap_data(
		start_date, number_of_days, date_count
	)

	return {
		"heatmap_data": heatmap_data,
		"labels": labels,
		"total_activities": total_activities,
		"weeks": weeks,
	}


def calculate_date_ranges(base_days):
	today = format_date(now(), "YYYY-MM-dd")
	day_today = get_datetime(today).strftime("%w")
	padding_end = 6 - cint(day_today)

	base_date = add_days(today, -base_days)
	day_of_base_date = cint(get_datetime(base_date).strftime("%w"))
	start_date = add_days(base_date, -day_of_base_date)
	number_of_days = base_days + day_of_base_date + padding_end
	days = [add_days(start_date, i) for i in range(number_of_days + 1)]

	return base_date, start_date, number_of_days, days


def initialize_date_count(days):
	return {format_date(day, "YYYY-MM-dd"): 0 for day in days}


def fetch_activity_data(member, start_date):
	lesson_completions = frappe.get_all(
		"LMS Course Progress",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date], "status": "Complete"},
	)

	quiz_submissions = frappe.get_all(
		"LMS Quiz Submission",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date]},
	)

	assignment_submissions = frappe.get_all(
		"LMS Assignment Submission",
		fields=["creation"],
		filters={"member": member, "creation": [">=", start_date]},
	)

	return lesson_completions, quiz_submissions, assignment_submissions


def count_dates(data, date_count):
	for entry in data:
		date = format_date(entry.creation, "YYYY-MM-dd")
		if date in date_count:
			date_count[date] += 1


def prepare_heatmap_data(start_date, number_of_days, date_count):
	days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
	heatmap_data = {day: [] for day in days_of_week}
	week_count = -(number_of_days // -7)
	labels = [None] * week_count
	last_seen_month = None
	sorted_dates = sorted(date_count.keys())

	for date in sorted_dates:
		activity_count = date_count[date]
		day_of_week = get_datetime(date).strftime("%a")
		current_month = get_datetime(date).strftime("%b")
		column_index = get_week_difference(start_date, date)

		if 0 <= column_index < week_count:
			heatmap_data[day_of_week].append(
				{
					"date": date,
					"count": activity_count,
					"label": f"{activity_count} activities on {format_date(date, 'dd MMM')}",
				}
			)

			if last_seen_month != current_month:
				labels[column_index] = current_month
				last_seen_month = current_month

	for index, label in enumerate(labels):
		if not label:
			labels[index] = ""

	formatted_heatmap_data = [{"name": day, "data": heatmap_data[day]} for day in days_of_week]

	total_activities = sum(date_count.values())
	return formatted_heatmap_data, labels, total_activities, week_count


def get_week_difference(start_date, current_date):
	diff_in_days = date_diff(current_date, start_date)
	return diff_in_days // 7


@frappe.whitelist()
def get_notifications(filters):
	filters = frappe._dict(filters or {})
	filters.for_user = frappe.session.user
	notifications = frappe.get_all(
		"Notification Log",
		filters,
		[
			"subject",
			"from_user",
			"link",
			"read",
			"name",
			"creation",
			"document_type",
			"document_name",
			"type",
			"email_content",
		],
		order_by="creation desc",
	)

	for notification in notifications:
		notification = update_document_details(notification)
		notification = update_user_details(notification)

	return notifications


def update_user_details(notification):
	if (
		notification.document_details
		and len(notification.document_details.get("instructors", []))
		and not is_mention(notification)
	):
		from_user_details = notification.document_details["instructors"][0]
	else:
		from_user_details = frappe.db.get_value(
			"User", notification.from_user, ["full_name", "user_image"], as_dict=1
		)
	notification["from_user_details"] = from_user_details
	return notification


def is_mention(notification):
	if notification.type == "Mention":
		return True
	if "mentioned you" in notification.subject.lower():
		return True
	return False


def update_document_details(notification):
	if notification.document_type == "LMS Course":
		details = frappe.db.get_value(
			"LMS Course", notification.document_name, ["title", "video_link", "short_introduction"], as_dict=1
		)
		instructors = get_instructors("LMS Course", notification.document_name)
		details["instructors"] = instructors
		notification["document_details"] = details

	elif notification.document_type == "LMS Batch":
		details = frappe.db.get_value(
			"LMS Batch",
			notification.document_name,
			[
				"title",
				"description as short_introduction",
				"video_link",
				"start_date",
				"end_date",
				"start_time",
				"timezone",
			],
			as_dict=1,
		)
		instructors = get_instructors("LMS Batch", notification.document_name)
		details["instructors"] = instructors
		notification["document_details"] = details
	return notification


@frappe.whitelist(allow_guest=True)
def get_lms_settings():
	allowed_fields = [
		"allow_guest_access",
		"prevent_skipping_videos",
		"contact_us_email",
		"contact_us_url",
		"livecode_url",
		"disable_pwa",
	]

	settings = frappe._dict()
	for field in allowed_fields:
		settings[field] = frappe.get_cached_value("LMS Settings", None, field)

	return settings


@frappe.whitelist()
def cancel_evaluation(evaluation):
	evaluation = frappe._dict(evaluation)
	if evaluation.member != frappe.session.user:
		frappe.throw(_("You do not have permission to cancel this evaluation."), frappe.PermissionError)

	frappe.db.set_value("LMS Certificate Request", evaluation.name, "status", "Cancelled")
	events = frappe.get_all(
		"Event Participants",
		{
			"email": evaluation.member,
		},
		["parent", "name"],
	)

	for event in events:
		info = frappe.db.get_value("Event", event.parent, ["starts_on", "subject"], as_dict=1)
		date = str(info.starts_on).split(" ")[0]

		if date == str(evaluation.date.format("YYYY-MM-DD")) and evaluation.member_name in info.subject:
			communication = frappe.db.get_value(
				"Communication",
				{"reference_doctype": "Event", "reference_name": event.parent},
				"name",
			)
			if communication:
				frappe.delete_doc("Communication", communication, ignore_permissions=True)

			frappe.delete_doc("Event Participants", event.name, ignore_permissions=True)
			frappe.delete_doc("Event", event.parent, ignore_permissions=True)


@frappe.whitelist()
def get_certification_details(course):
	membership = None
	filters = {"course": course, "member": frappe.session.user}

	if frappe.db.exists("LMS Enrollment", filters):
		membership = frappe.db.get_value(
			"LMS Enrollment",
			filters,
			["name", "purchased_certificate"],
			as_dict=1,
		)

	paid_certificate = frappe.db.get_value("LMS Course", course, "paid_certificate")
	certificate = frappe.db.get_value(
		"LMS Certificate",
		{"member": frappe.session.user, "course": course},
		["name", "template"],
		as_dict=1,
	)

	return {
		"membership": membership,
		"paid_certificate": paid_certificate,
		"certificate": certificate,
	}


@frappe.whitelist()
def save_role(user, role, value):
	frappe.only_for("Moderator")
	if cint(value):
		doc = frappe.get_doc(
			{
				"doctype": "Has Role",
				"parent": user,
				"role": role,
				"parenttype": "User",
				"parentfield": "roles",
			}
		)
		doc.save(ignore_permissions=True)
	else:
		frappe.db.delete("Has Role", {"parent": user, "role": role})
	frappe.clear_cache(user=user)
	return True


@frappe.whitelist()
def add_an_evaluator(email):
	frappe.only_for("Moderator")
	if not frappe.db.exists("User", email):
		user = frappe.new_doc("User")
		user.update(
			{
				"email": email,
				"first_name": email.split("@")[0].capitalize(),
				"enabled": 1,
			}
		)
		user.insert()
		user.add_roles("Batch Evaluator")

	evaluator = frappe.new_doc("Course Evaluator")
	evaluator.evaluator = email
	evaluator.insert()

	return evaluator


@frappe.whitelist()
def capture_user_persona(responses):
	frappe.only_for("System Manager")
	data = frappe.parse_json(responses)
	data = json.dumps(data)
	response = frappe.integrations.utils.make_post_request(
		"https://school.frappe.io/api/method/capture-persona",
		data={"response": data},
	)
	if response.get("message").get("name"):
		frappe.db.set_single_value("LMS Settings", "persona_captured", True)
	return response


@frappe.whitelist()
def get_meta_info(type, route):
	if frappe.db.exists("Website Meta Tag", {"parent": f"{type}/{route}"}):
		meta_tags = frappe.get_all(
			"Website Meta Tag",
			{
				"parent": f"{type}/{route}",
			},
			["name", "key", "value"],
		)

		return meta_tags

	return []


@frappe.whitelist()
def update_meta_info(meta_type, route, meta_tags):
	frappe.only_for(["Course Creator", "Batch Evaluator", "Moderator"])
	validate_meta_data_permissions(meta_type)
	validate_meta_tags(meta_tags)

	parent_name = f"{meta_type}/{route}"
	for tag in meta_tags:
		existing_tag = frappe.db.exists(
			"Website Meta Tag",
			{
				"parent": parent_name,
				"parenttype": "Website Route Meta",
				"parentfield": "meta_tags",
				"key": tag["key"],
			},
		)
		if existing_tag:
			if not tag.get("value"):
				frappe.db.delete("Website Meta Tag", existing_tag)
				continue
			frappe.db.set_value("Website Meta Tag", existing_tag, "value", tag["value"])
		elif tag.get("value"):
			tag_properties = {
				"parent": parent_name,
				"parenttype": "Website Route Meta",
				"parentfield": "meta_tags",
				"key": tag["key"],
				"value": tag["value"],
			}

			parent_exists = frappe.db.exists("Website Route Meta", parent_name)
			if not parent_exists:
				create_meta(parent_name, tag_properties)
			else:
				create_meta_tag(tag_properties)


def validate_meta_tags(meta_tags):
	if not isinstance(meta_tags, list):
		frappe.throw(_("Meta tags should be a list."))


def create_meta(parent_name, tag_properties):
	route_meta = frappe.new_doc("Website Route Meta")
	route_meta.update(
		{
			"__newname": parent_name,
		}
	)
	route_meta.append("meta_tags", tag_properties)
	route_meta.insert()


def create_meta_tag(tag_properties):
	new_tag = frappe.new_doc("Website Meta Tag")
	new_tag.update(tag_properties)
	new_tag.insert()


def validate_meta_data_permissions(meta_type):
	roles = frappe.get_roles()

	if meta_type == "courses":
		if not ("Course Creator" in roles or "Moderator" in roles):
			frappe.throw(_("You do not have permission to update meta tags."))

	elif meta_type == "batches":
		if not ("Batch Evaluator" in roles or "Moderator" in roles):
			frappe.throw(_("You do not have permission to update meta tags."))


@frappe.whitelist()
def create_programming_exercise_submission(exercise, submission, code, test_cases):
	if submission == "new":
		return make_new_exercise_submission(exercise, code, test_cases)
	else:
		update_exercise_submission(submission, code, test_cases)


def make_new_exercise_submission(exercise, code, test_cases):
	submission = frappe.new_doc("LMS Programming Exercise Submission")
	submission.exercise = exercise
	submission.member = frappe.session.user
	submission.code = code

	for test_case in test_cases:
		submission.append(
			"test_cases",
			{
				"input": test_case.get("input"),
				"output": test_case.get("output"),
				"expected_output": test_case.get("expected_output"),
				"status": test_case.get("status", test_case.get("status", "Failed")),
			},
		)

	submission.status = get_exercise_status(test_cases)
	submission.insert()
	return submission.name


def update_exercise_submission(submission, code, test_cases):
	member = frappe.db.get_value("LMS Programming Exercise Submission", submission, "member")
	if member != frappe.session.user:
		frappe.throw(_("You do not have permission to update this submission."), frappe.PermissionError)

	update_test_cases(test_cases, submission)
	status = get_exercise_status(test_cases)
	frappe.db.set_value("LMS Programming Exercise Submission", submission, {"status": status, "code": code})


def get_exercise_status(test_cases):
	if not test_cases:
		return "Failed"

	if all(row.get("status", "Failed") == "Passed" for row in test_cases):
		return "Passed"
	else:
		return "Failed"


def update_test_cases(test_cases, submission):
	frappe.db.delete("LMS Test Case Submission", {"parent": submission})
	for row in test_cases:
		test_case = frappe.new_doc("LMS Test Case Submission")
		test_case.update(
			{
				"parent": submission,
				"parenttype": "LMS Programming Exercise Submission",
				"parentfield": "test_cases",
				"input": row.get("input"),
				"output": row.get("output"),
				"expected_output": row.get("expected_output"),
				"status": row.get("status", "Failed"),
			}
		)
		test_case.insert()


@frappe.whitelist()
def track_video_watch_duration(lesson, videos):
	"""
	Track the watch duration of videos in a lesson.
	"""
	if not isinstance(videos, list):
		videos = json.loads(videos)

	for video in videos:
		filters = {
			"lesson": lesson,
			"source": video.get("source"),
			"member": frappe.session.user,
		}
		existing_record = frappe.db.get_value(
			"LMS Video Watch Duration", filters, ["name", "watch_time"], as_dict=True
		)
		if existing_record and flt(existing_record.watch_time) < flt(video.get("watch_time")):
			frappe.db.set_value(
				"LMS Video Watch Duration",
				filters,
				"watch_time",
				video.get("watch_time"),
			)
		elif not existing_record:
			track_new_watch_time(lesson, video)


def track_new_watch_time(lesson, video):
	doc = frappe.new_doc("LMS Video Watch Duration")
	doc.lesson = lesson
	doc.source = video.get("source")
	doc.watch_time = video.get("watch_time")
	doc.member = frappe.session.user
	doc.save()


@frappe.whitelist()
def get_course_progress_distribution(course):
	if not can_modify_course(course):
		frappe.throw(
			_("You do not have permission to access this course's progress data."), frappe.PermissionError
		)

	all_progress = frappe.get_all(
		"LMS Enrollment",
		{
			"course": course,
		},
		pluck="progress",
	)

	average_progress = get_average_course_progress(all_progress)
	progress_distribution = get_progress_distribution(all_progress)

	return {
		"average_progress": average_progress,
		"progress_distribution": progress_distribution,
	}


def get_average_course_progress(progress_list):
	if not progress_list:
		return 0
	average_progress = sum(progress_list) / len(progress_list)
	return flt(average_progress, frappe.get_system_settings("float_precision") or 3)


def get_progress_distribution(progressList):
	distribution = [
		{
			"name": "Just Started (0-30%)",
			"value": len([p for p in progressList if 0 <= p < 30]),
		},
		{
			"name": "In Progress (30-60%)",
			"value": len([p for p in progressList if 30 <= p < 60]),
		},
		{
			"name": "Advanced (60-100%)",
			"value": len([p for p in progressList if 60 <= p <= 100]),
		},
	]

	return distribution


@frappe.whitelist(allow_guest=True)
def get_pwa_manifest():
	title = frappe.db.get_single_value("Website Settings", "app_name") or "Frappe Learning"
	banner_image = frappe.db.get_single_value("Website Settings", "banner_image")

	manifest = {
		"name": title,
		"short_name": title,
		"description": "Easy to use, 100% open source Learning Management System",
		"start_url": get_lms_route(),
		"icons": [
			{
				"src": banner_image or "/assets/lms/frontend/manifest/manifest-icon-192.maskable.png",
				"sizes": "192x192",
				"type": "image/png",
				"purpose": "maskable any",
			}
		],
	}

	return Response(json.dumps(manifest), status=200, content_type="application/manifest+json")


@frappe.whitelist()
def get_profile_details(username):
	details = frappe.db.get_value(
		"User",
		{"username": username},
		[
			"first_name",
			"last_name",
			"full_name",
			"name",
			"username",
			"user_image",
			"bio",
			"headline",
			"language",
			"cover_image",
			"open_to",
			"linkedin",
			"github",
			"twitter",
		],
		as_dict=True,
	)

	details.roles = frappe.get_roles(details.name)
	return details


@frappe.whitelist()
def get_streak_info():
	all_dates = fetch_activity_dates(frappe.session.user)
	streak, longest_streak = calculate_streaks(all_dates)
	current_streak = calculate_current_streak(all_dates, streak)

	return {
		"current_streak": current_streak,
		"longest_streak": longest_streak,
	}


def fetch_activity_dates(user):
	doctypes = [
		"LMS Course Progress",
		"LMS Quiz Submission",
		"LMS Assignment Submission",
		"LMS Programming Exercise Submission",
	]

	all_dates = []
	for dt in doctypes:
		all_dates.extend(frappe.get_all(dt, {"member": user}, pluck="creation"))

	return sorted({d.date() if hasattr(d, "date") else d for d in all_dates})


def calculate_streaks(all_dates):
	streak = 0
	longest_streak = 0
	prev_day = None

	for d in all_dates:
		if d.weekday() in (5, 6):
			continue

		if prev_day:
			expected = prev_day + timedelta(days=1)
			while expected.weekday() in (5, 6):
				expected += timedelta(days=1)

			streak = streak + 1 if d == expected else 1
		else:
			streak = 1

		longest_streak = max(longest_streak, streak)
		prev_day = d

	return streak, longest_streak


def calculate_current_streak(all_dates, streak):
	if not all_dates:
		return 0

	last_date = all_dates[-1]
	today = getdate()

	ref_day = today
	while ref_day.weekday() in (5, 6):
		ref_day -= timedelta(days=1)

	if last_date == ref_day or last_date == ref_day - timedelta(days=1):
		return streak
	return 0


@frappe.whitelist()
def get_my_live_classes():
	my_live_classes = []

	batches = frappe.get_all(
		"LMS Batch Enrollment",
		{
			"member": frappe.session.user,
		},
		order_by="creation desc",
		pluck="batch",
	)

	live_class_details = frappe.get_all(
		"LMS Live Class",
		filters={
			"date": [">=", getdate()],
			"batch_name": ["in", batches],
		},
		fields=[
			"name",
			"title",
			"description",
			"time",
			"date",
			"duration",
			"attendees",
			"start_url",
			"join_url",
			"owner",
		],
		limit=2,
		order_by="date",
	)

	if len(live_class_details):
		for live_class in live_class_details:
			live_class.course_title = frappe.db.get_value("LMS Course", live_class.course, "title")

			my_live_classes.append(live_class)

	return my_live_classes


@frappe.whitelist()
def get_created_courses():
	created_courses = []

	CourseInstructor = frappe.qb.DocType("Course Instructor")
	Course = frappe.qb.DocType("LMS Course")

	query = (
		frappe.qb.from_(CourseInstructor)
		.join(Course)
		.on(CourseInstructor.parent == Course.name)
		.select(Course.name)
		.where(CourseInstructor.instructor == frappe.session.user)
		.orderby(Course.published_on, order=frappe.qb.desc)
		.limit(3)
	)

	results = query.run(as_dict=True)
	courses = [row["name"] for row in results]

	for course in courses:
		course_details = get_course_details(course)
		created_courses.append(course_details)

	return created_courses


@frappe.whitelist()
def get_created_batches():
	created_batches = []

	CourseInstructor = frappe.qb.DocType("Course Instructor")
	Batch = frappe.qb.DocType("LMS Batch")

	query = (
		frappe.qb.from_(CourseInstructor)
		.join(Batch)
		.on(CourseInstructor.parent == Batch.name)
		.select(Batch.name)
		.where(CourseInstructor.instructor == frappe.session.user)
		.where(Batch.start_date >= getdate())
		.orderby(Batch.start_date, order=frappe.qb.asc)
		.limit(4)
	)

	results = query.run(as_dict=True)
	batches = [row["name"] for row in results]

	for batch in batches:
		batch_details = get_batch_details(batch)
		created_batches.append(batch_details)

	return created_batches


@frappe.whitelist()
def get_admin_live_classes():
	CourseInstructor = frappe.qb.DocType("Course Instructor")
	LMSLiveClass = frappe.qb.DocType("LMS Live Class")

	query = (
		frappe.qb.from_(CourseInstructor)
		.join(LMSLiveClass)
		.on(CourseInstructor.parent == LMSLiveClass.batch_name)
		.select(
			LMSLiveClass.name,
			LMSLiveClass.title,
			LMSLiveClass.description,
			LMSLiveClass.time,
			LMSLiveClass.date,
			LMSLiveClass.duration,
			LMSLiveClass.attendees,
			LMSLiveClass.start_url,
			LMSLiveClass.join_url,
			LMSLiveClass.owner,
		)
		.where(CourseInstructor.instructor == frappe.session.user)
		.where(LMSLiveClass.date >= getdate())
		.orderby(LMSLiveClass.date, order=frappe.qb.asc)
		.limit(4)
	)
	results = query.run(as_dict=True)
	return results


@frappe.whitelist()
def get_admin_evals():
	evals = frappe.get_all(
		"LMS Certificate Request",
		{
			"evaluator": frappe.session.user,
			"date": [">=", getdate()],
		},
		[
			"name",
			"date",
			"start_time",
			"course",
			"evaluator",
			"google_meet_link",
			"member",
			"member_name",
		],
		limit=4,
		order_by="date asc",
	)

	for evaluation in evals:
		evaluation.course_title = frappe.db.get_value("LMS Course", evaluation.course, "title")

	return evals


@frappe.whitelist()
def get_my_courses():
	my_courses = []
	courses = get_my_latest_courses()

	if not len(courses):
		courses = get_featured_home_courses()

	if not len(courses):
		courses = get_popular_courses()

	for course in courses:
		my_courses.append(get_course_details(course))

	return my_courses


def get_my_latest_courses():
	return frappe.get_all(
		"LMS Enrollment",
		{
			"member": frappe.session.user,
		},
		order_by="modified desc",
		limit=3,
		pluck="course",
	)


def get_featured_home_courses():
	return frappe.get_all(
		"LMS Course",
		{"published": 1, "featured": 1},
		order_by="published_on desc",
		limit=3,
		pluck="name",
	)


def get_popular_courses():
	return frappe.get_all(
		"LMS Course",
		{
			"published": 1,
		},
		order_by="enrollments desc",
		limit=3,
		pluck="name",
	)


@frappe.whitelist()
def get_my_batches():
	my_batches = []
	batches = get_my_latest_batches()

	if not len(batches):
		batches = get_upcoming_batches()

	for batch in batches:
		batch_details = get_batch_details(batch)
		if batch_details:
			my_batches.append(batch_details)

	return my_batches


def get_my_latest_batches():
	return frappe.get_all(
		"LMS Batch Enrollment",
		{
			"member": frappe.session.user,
		},
		order_by="creation desc",
		limit=4,
		pluck="batch",
	)


def get_upcoming_batches():
	return frappe.get_all(
		"LMS Batch",
		{
			"published": 1,
			"start_date": [">=", getdate()],
		},
		order_by="start_date asc",
		limit=4,
		pluck="name",
	)


@frappe.whitelist()
def delete_programming_exercise(exercise):
	frappe.only_for(["Moderator", "Course Creator"])
	frappe.db.delete("LMS Programming Exercise Submission", {"exercise": exercise})
	frappe.db.delete("LMS Programming Exercise", exercise)


@frappe.whitelist(allow_guest=True)
def get_roadmaps():
	is_instructor_or_moderator = has_course_instructor_role() or has_moderator_role()
	filters = {}
	if not is_instructor_or_moderator:
		filters["published"] = 1
	return frappe.get_all(
		"LMS Roadmap",
		filters=filters,
		fields=["name", "title", "description", "thumbnail", "published", "owner", "creation"],
		order_by="creation desc",
	)


@frappe.whitelist(allow_guest=True)
def get_roadmap(roadmap_name):
	roadmap = frappe.get_doc("LMS Roadmap", roadmap_name)
	data = {
		"name": roadmap.name,
		"title": roadmap.title,
		"description": roadmap.description,
		"thumbnail": roadmap.thumbnail,
		"published": roadmap.published,
		"owner": roadmap.owner,
		"roadmap_json": roadmap.roadmap_json,
	}

	if not roadmap.roadmap_json:
		data["nodes"] = []
		data["edges"] = []
		return data

	try:
		graph = json.loads(roadmap.roadmap_json)
	except Exception:
		data["nodes"] = []
		data["edges"] = []
		return data

	nodes = graph.get("nodes", [])
	edges = graph.get("edges", [])

	user = frappe.session.user
	if user and user != "Guest":
		for node in nodes:
			node_data = node.get("data", {})
			if node_data.get("type") == "course":
				course_name = node_data.get("course")
				if course_name:
					enrollment = frappe.db.get_value(
						"LMS Enrollment",
						{"member": user, "course": course_name},
						["name", "progress"],
						as_dict=True,
					)
					if enrollment:
						node_data["progress"] = flt(enrollment.progress)
						if flt(enrollment.progress) >= 100:
							node_data["status"] = "completed"
						elif flt(enrollment.progress) > 0:
							node_data["status"] = "in_progress"
						else:
							node_data["status"] = "not_started"
					else:
						node_data["progress"] = 0
						node_data["status"] = "not_started"

	data["nodes"] = nodes
	data["edges"] = edges
	return data


@frappe.whitelist()
def save_roadmap(roadmap_name, title, description, roadmap_json):
	if not has_course_instructor_role() and not has_moderator_role():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = frappe.get_doc("LMS Roadmap", roadmap_name)
	doc.title = title
	doc.description = description
	doc.roadmap_json = roadmap_json
	doc.save(ignore_permissions=True)
	return {"success": True}


@frappe.whitelist()
def create_roadmap(title, description=""):
	if not has_course_instructor_role() and not has_moderator_role():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = frappe.new_doc("LMS Roadmap")
	doc.title = title
	doc.description = description
	doc.published = 0
	doc.roadmap_json = json.dumps({"nodes": [], "edges": []})
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def get_lesson_completion_stats(course):
	roles = frappe.get_roles()
	if "Course Creator" not in roles and "Moderator" not in roles:
		frappe.throw(_("You do not have permission to access lesson completion stats."))

	CourseProgress = frappe.qb.DocType("LMS Course Progress")
	LessonReference = frappe.qb.DocType("Lesson Reference")
	ChapterReference = frappe.qb.DocType("Chapter Reference")
	Lesson = frappe.qb.DocType("Course Lesson")

	rows = (
		frappe.qb.from_(CourseProgress)
		.join(LessonReference)
		.on(CourseProgress.lesson == LessonReference.lesson)
		.join(ChapterReference)
		.on(LessonReference.parent == ChapterReference.chapter)
		.join(Lesson)
		.on(CourseProgress.lesson == Lesson.name)
		.select(
			LessonReference.idx,
			ChapterReference.idx.as_("chapter_idx"),
			CourseProgress.lesson,
			Lesson.title,
			Lesson.name.as_("lesson_name"),
			fn.Count(CourseProgress.name).as_("completion_count"),
		)
		.where((CourseProgress.course == course) & (CourseProgress.status == "Complete"))
		.groupby(CourseProgress.lesson)
		.orderby(ChapterReference.idx, LessonReference.idx)
		.run(as_dict=True)
	)

	return rows


@frappe.whitelist(allow_guest=True)
def get_documents(filters=None, start=0, page_length=20):
	"""Get list of documents with access control."""
	filters = frappe._dict(filters or {})
	user = frappe.session.user
	roles = frappe.get_roles(user) if user != "Guest" else []

	# Build base filters
	doc_filters = {"published": 1}

	# Apply access control
	access_levels = ["Public"]

	if user != "Guest":
		access_levels.append("Logged In")

		if "Moderator" in roles or "System Manager" in roles:
			access_levels.extend(["Moderators Only", "Course Creators Only"])
		elif "Course Creator" in roles:
			access_levels.append("Course Creators Only")

	doc_filters["access_level"] = ["in", access_levels]

	# Apply category filter
	if filters.get("category"):
		doc_filters["category"] = filters.get("category")

	# Apply search filter
	or_filters = {}
	if filters.get("search"):
		or_filters = {
			"title": ["like", f"%{filters.get('search')}%"],
			"description": ["like", f"%{filters.get('search')}%"],
		}

	# Get documents
	documents = frappe.get_all(
		"LMS Document",
		filters=doc_filters,
		or_filters=or_filters if or_filters else None,
		fields=[
			"name",
			"title",
			"category",
			"file",
			"file_type",
			"file_size",
			"description",
			"access_level",
			"download_count",
			"view_count",
			"owner",
			"creation",
			"modified",
		],
		order_by="creation desc",
		start=int(start),
		limit_page_length=int(page_length),
	)

	# Get owner details
	for doc in documents:
		doc.owner_name = frappe.db.get_value("User", doc.owner, "full_name")
		doc.owner_image = frappe.db.get_value("User", doc.owner, "user_image")

	return documents


@frappe.whitelist(allow_guest=True)
def get_document_detail(document_name):
	"""Get document detail and increment view count."""
	if not frappe.db.exists("LMS Document", document_name):
		frappe.throw(_("Document not found"), frappe.DoesNotExistError)

	doc = frappe.get_doc("LMS Document", document_name)

	# Check access
	if not check_document_access(doc):
		frappe.throw(_("You do not have permission to access this document"), frappe.PermissionError)

	# Increment view count
	frappe.db.set_value("LMS Document", document_name, "view_count", doc.view_count + 1)

	# Get owner details
	owner_details = frappe.db.get_value(
		"User", doc.owner, ["full_name", "user_image"], as_dict=True
	)

	return {
		"name": doc.name,
		"title": doc.title,
		"category": doc.category,
		"file": doc.file,
		"file_type": doc.file_type,
		"file_size": doc.file_size,
		"description": doc.description,
		"access_level": doc.access_level,
		"download_count": doc.download_count,
		"view_count": doc.view_count + 1,
		"owner": doc.owner,
		"owner_name": owner_details.get("full_name") if owner_details else None,
		"owner_image": owner_details.get("user_image") if owner_details else None,
		"creation": doc.creation,
		"modified": doc.modified,
	}


def check_document_access(doc):
	"""Check if current user has access to the document."""
	if not doc.published:
		# Only owner, moderators, and system managers can see unpublished documents
		user = frappe.session.user
		roles = frappe.get_roles(user)
		if doc.owner == user or "Moderator" in roles or "System Manager" in roles:
			return True
		return False

	user = frappe.session.user
	roles = frappe.get_roles(user) if user != "Guest" else []
	access_level = doc.access_level

	if access_level == "Public":
		return True
	elif access_level == "Logged In":
		return user != "Guest"
	elif access_level == "Moderators Only":
		return "Moderator" in roles or "System Manager" in roles
	elif access_level == "Course Creators Only":
		return "Course Creator" in roles or "Moderator" in roles or "System Manager" in roles

	return False


@frappe.whitelist()
def track_document_download(document_name):
	"""Track document download and return file URL."""
	if not frappe.db.exists("LMS Document", document_name):
		frappe.throw(_("Document not found"), frappe.DoesNotExistError)

	doc = frappe.get_doc("LMS Document", document_name)

	# Check access
	if not check_document_access(doc):
		frappe.throw(_("You do not have permission to download this document"), frappe.PermissionError)

	# Increment download count
	frappe.db.set_value("LMS Document", document_name, "download_count", doc.download_count + 1)

	return {"file_url": doc.file}


@frappe.whitelist()
def delete_document(document_name):
	"""Delete a document with permission check."""
	if not frappe.db.exists("LMS Document", document_name):
		frappe.throw(_("Document not found"), frappe.DoesNotExistError)

	doc = frappe.get_doc("LMS Document", document_name)
	user = frappe.session.user
	roles = frappe.get_roles(user)

	# Check if user can delete
	can_delete = (
		doc.owner == user
		or "Moderator" in roles
		or "System Manager" in roles
	)

	if not can_delete:
		frappe.throw(_("You do not have permission to delete this document"), frappe.PermissionError)

	frappe.delete_doc("LMS Document", document_name)
	return {"message": "Document deleted successfully"}


@frappe.whitelist(allow_guest=True)
def get_document_categories():
	"""Get all document categories."""
	categories = frappe.get_all(
		"LMS Document Category",
		fields=["name", "category_name", "description", "icon", "parent_category", "is_group"],
		order_by="category_name asc",
	)
	return categories


@frappe.whitelist(allow_guest=True)
def get_folder_tree():
	"""Get folder tree structure for documents sidebar."""
	categories = frappe.get_all(
		"LMS Document Category",
		fields=[
			"name", "category_name", "description", "icon",
			"parent_category", "is_group", "sort_order",
			"is_ranking_enabled", "ranking_type", "external_contest_url",
			"contest_type",
		],
		order_by="sort_order asc, category_name asc",
	)

	# Count documents in each category
	for cat in categories:
		cat.document_count = frappe.db.count(
			"LMS Document",
			{"category": cat.name, "published": 1}
		)
		# Count ranking submissions if ranking enabled
		if cat.is_ranking_enabled:
			cat.submission_count = frappe.db.count(
				"LMS Ranking Submission",
				{"category": cat.name, "status": "Approved"}
			)

	# Build tree structure
	tree = build_folder_tree(categories)
	return tree


def build_folder_tree(categories, parent=None):
	"""Recursively build folder tree."""
	tree = []
	for cat in categories:
		if cat.parent_category == parent:
			node = {
				"name": cat.name,
				"label": cat.category_name,
				"icon": cat.icon or "Folder",
				"is_group": cat.is_group,
				"document_count": cat.document_count,
				"sort_order": cat.sort_order or 0,
				"is_ranking_enabled": cat.is_ranking_enabled,
				"ranking_type": cat.ranking_type,
				"contest_type": cat.contest_type,
				"submission_count": cat.get("submission_count", 0),
				"children": build_folder_tree(categories, cat.name),
			}
			tree.append(node)
	return tree


@frappe.whitelist(allow_guest=True)
def get_folder_contents(folder=None):
	"""Get subfolders and documents in a folder."""
	user = frappe.session.user
	roles = frappe.get_roles(user) if user != "Guest" else []

	# Get subfolders
	subfolders = frappe.get_all(
		"LMS Document Category",
		filters={"parent_category": folder} if folder else {"parent_category": ["is", "not set"]},
		fields=["name", "category_name", "icon", "is_group"],
		order_by="category_name asc",
	)

	for subfolder in subfolders:
		subfolder.document_count = frappe.db.count(
			"LMS Document",
			{"category": subfolder.name, "published": 1}
		)

	# Build access control
	access_levels = ["Public"]
	if user != "Guest":
		access_levels.append("Logged In")
		if "Moderator" in roles or "System Manager" in roles:
			access_levels.extend(["Moderators Only", "Course Creators Only"])
		elif "Course Creator" in roles:
			access_levels.append("Course Creators Only")

	# Get documents in current folder
	doc_filters = {
		"published": 1,
		"access_level": ["in", access_levels],
	}

	if folder:
		doc_filters["category"] = folder
	else:
		doc_filters["category"] = ["is", "not set"]

	documents = frappe.get_all(
		"LMS Document",
		filters=doc_filters,
		fields=[
			"name",
			"title",
			"category",
			"file",
			"file_type",
			"file_size",
			"description",
			"access_level",
			"download_count",
			"view_count",
			"owner",
			"creation",
			"modified",
		],
		order_by="title asc",
	)

	for doc in documents:
		doc.owner_name = frappe.db.get_value("User", doc.owner, "full_name")

	# Get current folder info with ranking fields
	current_folder_info = None
	if folder:
		current_folder_info = frappe.db.get_value(
			"LMS Document Category",
			folder,
			[
				"name", "category_name", "parent_category",
				"folder_notes",
				"is_ranking_enabled", "ranking_type", "external_contest_url",
				"max_score", "submission_deadline", "allow_self_submission", "require_approval",
				"contest_type", "organizer_name", "contest_difficulty", "contest_tags",
				"contest_prize_info", "contest_description", "contest_problem_statement",
				"contest_dataset_info", "contest_evaluation_metric",
				"contest_submission_format", "contest_rules",
			],
			as_dict=True
		)

	return {
		"folders": subfolders,
		"documents": documents,
		"current_folder": current_folder_info,
	}


@frappe.whitelist()
def get_my_documents(start=0, page_length=20):
	"""Get documents uploaded by the current user."""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please login to view your documents"), frappe.PermissionError)

	documents = frappe.get_all(
		"LMS Document",
		filters={"owner": user},
		fields=[
			"name",
			"title",
			"category",
			"file",
			"file_type",
			"file_size",
			"description",
			"access_level",
			"published",
			"download_count",
			"view_count",
			"creation",
			"modified",
		],
		order_by="creation desc",
		start=int(start),
		limit_page_length=int(page_length),
	)

	return documents


# ============================================
# Ranking / Leaderboard APIs
# ============================================

@frappe.whitelist(allow_guest=True)
def get_folder_leaderboard(category, limit=50):
	"""Get leaderboard for a ranking-enabled folder."""
	# Check if folder has ranking enabled
	folder = frappe.db.get_value(
		"LMS Document Category",
		category,
		["is_ranking_enabled", "ranking_type", "max_score", "external_contest_url"],
		as_dict=True
	)

	if not folder or not folder.is_ranking_enabled:
		frappe.throw(_("This folder does not have ranking enabled"))

	# Determine sort order based on ranking type
	# For "Rank" type, lower is better
	# For "Score" and "Points", higher is better
	if folder.ranking_type == "Rank":
		order_by = "rank asc, score desc"
	else:
		order_by = "score desc, rank asc"

	submissions = frappe.get_all(
		"LMS Ranking Submission",
		filters={
			"category": category,
			"status": "Approved"
		},
		fields=[
			"name", "member", "member_name", "score", "rank",
			"external_username", "proof_url", "submission_date",
			"percentage", "max_score"
		],
		order_by=order_by,
		limit_page_length=int(limit)
	)

	# Add position/ranking
	for idx, sub in enumerate(submissions, 1):
		sub.position = idx
		# Get member avatar
		sub.member_image = frappe.db.get_value("User", sub.member, "user_image")

	return {
		"submissions": submissions,
		"folder": folder,
		"total_count": frappe.db.count("LMS Ranking Submission", {
			"category": category,
			"status": "Approved"
		})
	}


@frappe.whitelist()
def submit_ranking_score(category, score=None, rank=None, external_username=None, proof_url=None, proof_screenshot=None):
	"""Submit or update score for a ranking folder."""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please login to submit your score"), frappe.PermissionError)

	# Check if folder allows self-submission
	folder = frappe.db.get_value(
		"LMS Document Category",
		category,
		["is_ranking_enabled", "allow_self_submission", "require_approval"],
		as_dict=True
	)

	if not folder or not folder.is_ranking_enabled:
		frappe.throw(_("This folder does not have ranking enabled"))

	if not folder.allow_self_submission:
		frappe.throw(_("Self-submission is not allowed for this contest"))

	# Check if user already has a submission
	existing = frappe.db.get_value(
		"LMS Ranking Submission",
		{"category": category, "member": user},
		"name"
	)

	if existing:
		# Update existing submission
		doc = frappe.get_doc("LMS Ranking Submission", existing)
		if score is not None:
			doc.score = float(score)
		if rank is not None:
			doc.rank = float(rank)
		if external_username:
			doc.external_username = external_username
		if proof_url:
			doc.proof_url = proof_url
		if proof_screenshot:
			doc.proof_screenshot = proof_screenshot
		# Reset status to pending if require_approval
		if folder.require_approval:
			doc.status = "Pending"
		doc.save()
		return {"message": "Submission updated", "name": doc.name, "is_update": True}
	else:
		# Create new submission
		doc = frappe.get_doc({
			"doctype": "LMS Ranking Submission",
			"category": category,
			"member": user,
			"score": float(score) if score else 0,
			"rank": float(rank) if rank else None,
			"external_username": external_username,
			"proof_url": proof_url,
			"proof_screenshot": proof_screenshot,
		})
		doc.insert()
		return {"message": "Submission created", "name": doc.name, "is_update": False}


@frappe.whitelist()
def get_my_ranking_submission(category):
	"""Get current user's submission for a category."""
	user = frappe.session.user
	if user == "Guest":
		return None

	submission = frappe.db.get_value(
		"LMS Ranking Submission",
		{"category": category, "member": user},
		["name", "score", "rank", "external_username", "proof_url",
		 "proof_screenshot", "status", "submission_date", "remarks"],
		as_dict=True
	)

	return submission


@frappe.whitelist()
def approve_ranking_submission(submission_name, status, remarks=None):
	"""Approve or reject a ranking submission (moderator only)."""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Moderator" not in roles and "System Manager" not in roles:
		frappe.throw(_("Only moderators can approve submissions"), frappe.PermissionError)

	if status not in ["Approved", "Rejected"]:
		frappe.throw(_("Invalid status"))

	doc = frappe.get_doc("LMS Ranking Submission", submission_name)
	doc.status = status
	doc.approved_by = user
	doc.approved_on = frappe.utils.now_datetime()
	if remarks:
		doc.remarks = remarks
	doc.save()

	return {"message": f"Submission {status.lower()}", "name": doc.name}


@frappe.whitelist()
def get_pending_submissions(category=None):
	"""Get pending submissions for approval (moderator only)."""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Moderator" not in roles and "System Manager" not in roles:
		frappe.throw(_("Only moderators can view pending submissions"), frappe.PermissionError)

	filters = {"status": "Pending"}
	if category:
		filters["category"] = category

	submissions = frappe.get_all(
		"LMS Ranking Submission",
		filters=filters,
		fields=[
			"name", "category", "member", "member_name", "score", "rank",
			"external_username", "proof_url", "proof_screenshot",
			"submission_date", "remarks"
		],
		order_by="submission_date desc"
	)

	# Add category name
	for sub in submissions:
		sub.category_name = frappe.db.get_value(
			"LMS Document Category", sub.category, "category_name"
		)

	return submissions


# ============================================
# Folder Drag & Drop / Reorder APIs
# ============================================

@frappe.whitelist()
def reorder_folder(folder_name, new_parent=None, new_order=None):
	"""Move folder to new parent and/or update sort order."""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Moderator" not in roles and "System Manager" not in roles:
		frappe.throw(_("Only moderators can reorganize folders"), frappe.PermissionError)

	doc = frappe.get_doc("LMS Document Category", folder_name)

	# Prevent circular reference
	if new_parent:
		if new_parent == folder_name:
			frappe.throw(_("A folder cannot be its own parent"))
		# Check if new_parent is a descendant of this folder
		if is_descendant(new_parent, folder_name):
			frappe.throw(_("Cannot move folder into its own descendant"))

	# Update parent
	if new_parent is not None:
		doc.parent_category = new_parent if new_parent else None

	# Update sort order
	if new_order is not None:
		doc.sort_order = int(new_order)

	doc.save()

	# Clear cache
	frappe.cache().delete_key("folder_tree")

	return {"message": "Folder updated", "name": doc.name}


def is_descendant(folder_name, potential_ancestor):
	"""Check if folder_name is a descendant of potential_ancestor."""
	current = folder_name
	visited = set()

	while current:
		if current in visited:
			break  # Prevent infinite loop
		visited.add(current)

		if current == potential_ancestor:
			return True

		current = frappe.db.get_value(
			"LMS Document Category", current, "parent_category"
		)

	return False


@frappe.whitelist()
def bulk_reorder_folders(folder_orders):
	"""Batch update folder orders.

	Args:
		folder_orders: JSON string or list of {name, parent_category, sort_order}
	"""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Moderator" not in roles and "System Manager" not in roles:
		frappe.throw(_("Only moderators can reorganize folders"), frappe.PermissionError)

	if isinstance(folder_orders, str):
		folder_orders = json.loads(folder_orders)

	for item in folder_orders:
		frappe.db.set_value(
			"LMS Document Category",
			item["name"],
			{
				"parent_category": item.get("parent_category") or None,
				"sort_order": item.get("sort_order", 0)
			},
			update_modified=False
		)

	frappe.db.commit()

	# Clear cache
	frappe.cache().delete_key("folder_tree")

	return {"message": f"Updated {len(folder_orders)} folders"}


@frappe.whitelist()
def create_folder(category_name, parent_category=None, is_ranking_enabled=False, ranking_type="Score", external_contest_url=None):
	"""Create a new folder/category."""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Moderator" not in roles and "System Manager" not in roles and "Course Creator" not in roles:
		frappe.throw(_("You don't have permission to create folders"), frappe.PermissionError)

	# Get max sort_order for siblings
	siblings = frappe.get_all(
		"LMS Document Category",
		filters={"parent_category": parent_category} if parent_category else {"parent_category": ["is", "not set"]},
		fields=["sort_order"],
		order_by="sort_order desc",
		limit=1
	)
	max_order = siblings[0].sort_order if siblings else 0

	doc = frappe.get_doc({
		"doctype": "LMS Document Category",
		"category_name": category_name,
		"parent_category": parent_category,
		"is_group": 1,
		"sort_order": max_order + 1,
		"is_ranking_enabled": 1 if is_ranking_enabled else 0,
		"ranking_type": ranking_type if is_ranking_enabled else "Score",
		"external_contest_url": external_contest_url if is_ranking_enabled else None,
	})
	doc.insert()

	return {"message": "Folder created", "name": doc.name}


@frappe.whitelist()
def update_folder_ranking_settings(
	folder_name, is_ranking_enabled, ranking_type=None,
	external_contest_url=None, max_score=None, submission_deadline=None,
	allow_self_submission=True, require_approval=False,
	contest_type=None, organizer_name=None, contest_difficulty=None,
	contest_tags=None, contest_prize_info=None, contest_description=None,
	contest_problem_statement=None, contest_dataset_info=None,
	contest_evaluation_metric=None, contest_submission_format=None,
	contest_rules=None
):
	"""Update ranking settings for a folder."""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	if "Moderator" not in roles and "System Manager" not in roles:
		frappe.throw(_("Only moderators can update ranking settings"), frappe.PermissionError)

	doc = frappe.get_doc("LMS Document Category", folder_name)
	doc.is_ranking_enabled = 1 if is_ranking_enabled else 0

	if is_ranking_enabled:
		doc.ranking_type = ranking_type or "Score"
		doc.external_contest_url = external_contest_url
		doc.max_score = float(max_score) if max_score else None
		doc.submission_deadline = submission_deadline
		doc.allow_self_submission = 1 if allow_self_submission else 0
		doc.require_approval = 1 if require_approval else 0
		doc.contest_type = contest_type
		doc.organizer_name = organizer_name
		doc.contest_difficulty = contest_difficulty
		doc.contest_tags = contest_tags
		doc.contest_prize_info = contest_prize_info
		doc.contest_description = contest_description
		doc.contest_problem_statement = contest_problem_statement
		doc.contest_dataset_info = contest_dataset_info
		doc.contest_evaluation_metric = contest_evaluation_metric
		doc.contest_submission_format = contest_submission_format
		doc.contest_rules = contest_rules

	doc.save()

	return {"message": "Ranking settings updated", "name": doc.name}


@frappe.whitelist()
def update_folder_notes(folder_name, notes):
	"""Update folder notes/announcements. Moderators only."""
	roles = frappe.get_roles(frappe.session.user)
	if "Moderator" not in roles and "System Manager" not in roles:
		frappe.throw(_("Only moderators can update folder notes"))
	doc = frappe.get_doc("LMS Document Category", folder_name)
	doc.folder_notes = notes
	doc.save(ignore_permissions=True)
	return {"message": "Notes updated"}
