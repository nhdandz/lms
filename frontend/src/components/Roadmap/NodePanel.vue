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
					<label class="text-xs font-medium text-ink-gray-7 block mb-1">Custom Label (optional)</label>
					<input
						v-model="localData.label"
						class="w-full border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
						placeholder="Overrides course title"
						@input="emitUpdate"
					/>
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
import { X, Trash2 } from 'lucide-vue-next'
import { createResource } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const props = defineProps({
	node: { type: Object, default: null },
})
const emit = defineEmits(['update', 'close', 'delete'])

const localData = ref({})

watch(
	() => props.node,
	(n) => {
		if (n) localData.value = { ...n.data }
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

function emitUpdate() {
	emit('update', { ...localData.value })
}
</script>
