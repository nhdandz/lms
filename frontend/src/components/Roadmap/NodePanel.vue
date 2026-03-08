<template>
	<div class="w-72 border-l bg-white flex flex-col overflow-y-auto shrink-0">
		<div class="flex items-center justify-between px-4 py-3 border-b">
			<span class="font-semibold text-sm text-ink-gray-9">Edit Node</span>
			<button @click="$emit('close')" class="text-ink-gray-5 hover:text-ink-gray-9">
				<X class="h-4 w-4" />
			</button>
		</div>

		<div class="p-4 space-y-4 flex-1">
			<!-- Course type: search from DB -->
			<template v-if="localData.type === 'course'">
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Course</label>
					<Link
						doctype="LMS Course"
						:modelValue="localData.course || ''"
						placeholder="Search courses..."
						@update:modelValue="onCourseSelected"
					/>
					<p v-if="localData.label" class="text-xs text-ink-gray-5 mt-1">
						Label: {{ localData.label }}
					</p>
				</div>
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Description (optional)</label>
					<textarea
						v-model="localData.description"
						rows="3"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
						placeholder="Brief description of this course..."
						@input="emitUpdate"
					/>
				</div>
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Custom Label (optional)</label>
					<input
						v-model="localData.label"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
						placeholder="Overrides course title"
						@input="emitUpdate"
					/>
				</div>

				<!-- Resources section -->
				<div>
					<div class="flex items-center justify-between mb-2">
						<label class="text-xs font-medium text-ink-gray-7">Resources</label>
						<button
							v-if="!showAddResource"
							class="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
							@click="showAddResource = true"
						>
							<Plus class="h-3.5 w-3.5" />
							Add
						</button>
					</div>

					<!-- Existing resources list -->
					<div v-if="localData.resources?.length" class="space-y-1.5 mb-2">
						<div
							v-for="(res, idx) in localData.resources"
							:key="idx"
							class="flex items-center gap-2 bg-gray-50 rounded px-2 py-1.5"
						>
							<component :is="resourceIcon(res.type)" class="h-3.5 w-3.5 shrink-0" :class="resourceIconColor(res.type)" />
							<span class="text-xs text-gray-700 flex-1 truncate">{{ res.label || res.url || res.name }}</span>
							<span class="text-[10px] text-gray-400 capitalize">{{ res.type }}</span>
							<button @click="removeResource(idx)" class="text-gray-300 hover:text-red-500 ml-1">
								<X class="h-3 w-3" />
							</button>
						</div>
					</div>
					<p v-else-if="!showAddResource" class="text-xs text-gray-400">No resources added yet.</p>

					<!-- Add resource inline form -->
					<div v-if="showAddResource" class="border rounded p-3 space-y-2 bg-gray-50">
						<div>
							<label class="text-xs text-gray-600 block mb-1">Type</label>
							<select
								v-model="newResource.type"
								class="w-full border rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400 bg-white"
								@change="newResource.name = ''; newResource.url = ''; newResource.label = ''"
							>
								<option value="link">External Link</option>
								<option value="document">Document</option>
								<option value="folder">Folder</option>
							</select>
						</div>

						<!-- Link fields -->
						<template v-if="newResource.type === 'link'">
							<div>
								<label class="text-xs text-gray-600 block mb-1">URL</label>
								<input
									v-model="newResource.url"
									class="w-full border rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
									placeholder="https://..."
								/>
							</div>
							<div>
								<label class="text-xs text-gray-600 block mb-1">Label</label>
								<input
									v-model="newResource.label"
									class="w-full border rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
									placeholder="Display name"
								/>
							</div>
						</template>

						<!-- Document fields -->
						<template v-else-if="newResource.type === 'document'">
							<div>
								<label class="text-xs text-gray-600 block mb-1">Document</label>
								<Link
									doctype="LMS Document"
									:modelValue="newResource.name || ''"
									placeholder="Search documents..."
									@update:modelValue="onResourceDocumentSelected"
								/>
							</div>
							<div v-if="newResource.label">
								<label class="text-xs text-gray-600 block mb-1">Label</label>
								<input
									v-model="newResource.label"
									class="w-full border rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
								/>
							</div>
						</template>

						<!-- Folder fields -->
						<template v-else-if="newResource.type === 'folder'">
							<div>
								<label class="text-xs text-gray-600 block mb-1">Folder</label>
								<Link
									doctype="LMS Document Category"
									:modelValue="newResource.name || ''"
									placeholder="Search folders..."
									@update:modelValue="onResourceFolderSelected"
								/>
							</div>
							<div v-if="newResource.label">
								<label class="text-xs text-gray-600 block mb-1">Label</label>
								<input
									v-model="newResource.label"
									class="w-full border rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
								/>
							</div>
						</template>

						<div class="flex gap-2 pt-1">
							<button
								class="flex-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded py-1.5 transition-colors"
								@click="confirmResource"
							>
								Confirm
							</button>
							<button
								class="flex-1 text-xs border rounded py-1.5 text-gray-600 hover:bg-gray-100 transition-colors"
								@click="cancelResource"
							>
								Cancel
							</button>
						</div>
					</div>
				</div>
			</template>

			<!-- Note type -->
			<template v-else-if="localData.type === 'note'">
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Content</label>
					<textarea
						v-model="localData.label"
						rows="4"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-yellow-400 resize-none"
						placeholder="Write your note..."
						@input="emitUpdate"
					/>
				</div>
			</template>

			<!-- Link type -->
			<template v-else-if="localData.type === 'link'">
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Label</label>
					<input
						v-model="localData.label"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-purple-400"
						placeholder="Link label"
						@input="emitUpdate"
					/>
				</div>
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">URL</label>
					<input
						v-model="localData.url"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-purple-400"
						placeholder="https://..."
						@input="emitUpdate"
					/>
				</div>
			</template>

			<!-- Milestone type -->
			<template v-else-if="localData.type === 'milestone'">
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Title</label>
					<input
						v-model="localData.label"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-green-400"
						placeholder="Milestone title"
						@input="emitUpdate"
					/>
				</div>
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Description</label>
					<textarea
						v-model="localData.description"
						rows="3"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-green-400 resize-none"
						placeholder="Optional description"
						@input="emitUpdate"
					/>
				</div>
			</template>

			<!-- Document type: tìm từ LMS Document -->
			<template v-else-if="localData.type === 'document'">
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Document</label>
					<Link
						doctype="LMS Document"
						:modelValue="localData.document || ''"
						placeholder="Search documents..."
						@update:modelValue="onDocumentSelected"
					/>
					<p v-if="localData.fileType" class="text-xs text-ink-gray-5 mt-1 uppercase">
						{{ localData.fileType }}
					</p>
				</div>
				<div>
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Custom Label (optional)</label>
					<input
						v-model="localData.label"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-orange-400"
						placeholder="Overrides document title"
						@input="emitUpdate"
					/>
				</div>
			</template>
		</div>

		<div class="px-4 py-3 border-t">
			<button
				@click="$emit('delete')"
				class="flex items-center gap-2 text-sm text-red-500 hover:text-red-700"
			>
				<Trash2 class="h-4 w-4" />
				Delete Node
			</button>
		</div>
	</div>
</template>
<script setup>
import { ref, watch } from 'vue'
import { X, Trash2, Plus, FolderOpen, ExternalLink, FileText } from 'lucide-vue-next'
import { createResource } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const props = defineProps({
	node: { type: Object, default: null },
})
const emit = defineEmits(['update', 'close', 'delete'])

const localData = ref({})
const showAddResource = ref(false)
const newResource = ref({ type: 'link', url: '', label: '', name: '' })

watch(
	() => props.node,
	(n) => {
		if (n) localData.value = { ...n.data, resources: [...(n.data.resources || [])] }
		showAddResource.value = false
	},
	{ immediate: true, deep: true }
)

async function onCourseSelected(courseName) {
	localData.value.course = courseName
	if (courseName) {
		const res = createResource({
			url: 'frappe.client.get_value',
			params: { doctype: 'LMS Course', fieldname: 'title', filters: { name: courseName } },
			auto: false,
		})
		await res.fetch()
		const title = res.data?.title || courseName
		if (!localData.value.label || localData.value.label === localData.value.course) {
			localData.value.label = title
		}
		localData.value.courseTitle = title
	}
	emitUpdate()
}

async function onDocumentSelected(docName) {
	localData.value.document = docName
	if (docName) {
		const res = createResource({
			url: 'frappe.client.get_value',
			params: {
				doctype: 'LMS Document',
				fieldname: ['title', 'file', 'file_type'],
				filters: { name: docName },
			},
			auto: false,
		})
		await res.fetch()
		const data = res.data || {}
		if (!localData.value.label || localData.value.label === localData.value.document) {
			localData.value.label = data.title || docName
		}
		localData.value.documentTitle = data.title || docName
		localData.value.file = data.file || ''
		localData.value.fileType = data.file_type || ''
	}
	emitUpdate()
}

async function onResourceDocumentSelected(docName) {
	newResource.value.name = docName
	if (docName) {
		const res = createResource({
			url: 'frappe.client.get_value',
			params: { doctype: 'LMS Document', fieldname: 'title', filters: { name: docName } },
			auto: false,
		})
		await res.fetch()
		newResource.value.label = res.data?.title || docName
	}
}

async function onResourceFolderSelected(folderName) {
	newResource.value.name = folderName
	if (folderName) {
		const res = createResource({
			url: 'frappe.client.get_value',
			params: { doctype: 'LMS Document Category', fieldname: 'category_name', filters: { name: folderName } },
			auto: false,
		})
		await res.fetch()
		newResource.value.label = res.data?.category_name || folderName
	}
}

function confirmResource() {
	const r = newResource.value
	if (r.type === 'link' && !r.url) return
	if ((r.type === 'document' || r.type === 'folder') && !r.name) return

	if (!localData.value.resources) localData.value.resources = []
	localData.value.resources = [
		...localData.value.resources,
		{ ...r },
	]
	emitUpdate()
	cancelResource()
}

function cancelResource() {
	showAddResource.value = false
	newResource.value = { type: 'link', url: '', label: '', name: '' }
}

function removeResource(idx) {
	localData.value.resources = localData.value.resources.filter((_, i) => i !== idx)
	emitUpdate()
}

function resourceIcon(type) {
	if (type === 'folder') return FolderOpen
	if (type === 'document') return FileText
	return ExternalLink
}
function resourceIconColor(type) {
	if (type === 'folder') return 'text-amber-600'
	if (type === 'document') return 'text-orange-600'
	return 'text-blue-600'
}

function emitUpdate() {
	emit('update', { ...localData.value })
}
</script>
