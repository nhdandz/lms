<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
		<Button v-if="isInstructor" @click="openNewDialog" variant="solid">
			<template #prefix>
				<Plus class="h-4 w-4 stroke-1.5" />
			</template>
			{{ __('New') }}
		</Button>
	</header>

	<div v-if="roadmaps.data?.length" class="py-10 w-3/4 mx-auto">
		<div class="text-lg font-semibold text-ink-gray-9 mb-5">
			{{ roadmaps.data.length }}
			{{ roadmaps.data.length === 1 ? __('Roadmap') : __('Roadmaps') }}
		</div>
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
			<div
				v-for="roadmap in roadmaps.data"
				:key="roadmap.name"
				class="border rounded-md p-4 hover:border-outline-gray-3 cursor-pointer space-y-2 relative"
				@click="openRoadmap(roadmap)"
			>
				<img
					v-if="roadmap.thumbnail"
					:src="roadmap.thumbnail"
					class="w-full h-32 object-cover rounded mb-2"
				/>
				<div class="text-base font-semibold text-ink-gray-9">{{ roadmap.title }}</div>
				<div v-if="roadmap.description" class="text-sm text-ink-gray-6 line-clamp-2">
					{{ roadmap.description }}
				</div>
				<div class="flex items-center gap-2 mt-2">
					<span
						v-if="!roadmap.published"
						class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500"
					>Draft</span>
					<span
						v-else
						class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700"
					>Published</span>
				</div>

				<!-- Actions: Edit + Delete (chỉ instructor) -->
				<div v-if="isInstructor" class="absolute top-3 right-3 flex items-center gap-1.5">
					<button
						class="text-ink-gray-5 hover:text-ink-gray-9 p-1 rounded hover:bg-surface-gray-2"
						:title="__('Edit')"
						@click.stop="editRoadmap(roadmap)"
					>
						<Pencil class="h-4 w-4" />
					</button>
					<button
						class="text-ink-gray-5 hover:text-red-600 p-1 rounded hover:bg-red-50"
						:title="__('Delete')"
						@click.stop="confirmDelete(roadmap)"
					>
						<Trash2 class="h-4 w-4" />
					</button>
				</div>
			</div>
		</div>
	</div>

	<div v-else-if="!roadmaps.loading" class="py-20 text-center text-ink-gray-5">
		<Map class="h-12 w-12 mx-auto mb-3 opacity-30" />
		<div class="text-base">{{ __('No Roadmaps yet') }}</div>
		<Button v-if="isInstructor" class="mt-4" @click="openNewDialog" variant="solid">
			{{ __('Create Roadmap') }}
		</Button>
	</div>

	<!-- New Roadmap Dialog -->
	<Dialog v-model="showNewDialog" :options="{ title: __('New Roadmap') }">
		<template #body-content>
			<div class="space-y-3">
				<div>
					<label class="text-sm font-medium text-ink-gray-7 block mb-1">{{ __('Title') }}</label>
					<Input v-model="newTitle" :placeholder="__('Roadmap title')" />
				</div>
				<div>
					<label class="text-sm font-medium text-ink-gray-7 block mb-1">{{ __('Description') }}</label>
					<Input v-model="newDescription" :placeholder="__('Optional description')" />
				</div>
			</div>
		</template>
		<template #actions>
			<Button variant="solid" :loading="creating" @click="createRoadmap">
				{{ __('Create') }}
			</Button>
		</template>
	</Dialog>

	<!-- Delete Confirm Dialog -->
	<Dialog
		v-model="showDeleteDialog"
		:options="{
			title: __('Delete Roadmap'),
			message: __('Are you sure you want to delete \'{0}\'? This cannot be undone.').format(deletingRoadmap?.title),
			actions: [
				{
					label: __('Delete'),
					theme: 'red',
					variant: 'solid',
					loading: deleting,
					onClick: doDelete,
				},
			],
		}"
	/>
</template>
<script setup>
import { Breadcrumbs, Button, Dialog, Input, usePageMeta, createResource } from 'frappe-ui'
import { computed, inject, onMounted, ref } from 'vue'
import { Plus, Pencil, Trash2, Map } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import { useRouter } from 'vue-router'

const { brand } = sessionStore()
const user = inject('$user')
const router = useRouter()

const showNewDialog = ref(false)
const newTitle = ref('')
const newDescription = ref('')
const creating = ref(false)

const showDeleteDialog = ref(false)
const deletingRoadmap = ref(null)
const deleting = ref(false)

const isInstructor = computed(
	() => user.data?.is_moderator || user.data?.is_instructor
)

onMounted(() => {
	if (!user.data) {
		window.location.href = '/login'
		return
	}
	roadmaps.reload()
})

const roadmaps = createResource({
	url: 'lms.lms.api.get_roadmaps',
	auto: false,
})

function openRoadmap(roadmap) {
	router.push({ name: 'RoadmapView', params: { roadmapName: roadmap.name } })
}

function editRoadmap(roadmap) {
	router.push({ name: 'RoadmapEditor', params: { roadmapName: roadmap.name } })
}

function openNewDialog() {
	newTitle.value = ''
	newDescription.value = ''
	showNewDialog.value = true
}

async function createRoadmap() {
	if (!newTitle.value.trim()) return
	creating.value = true
	const res = createResource({
		url: 'lms.lms.api.create_roadmap',
		params: { title: newTitle.value.trim(), description: newDescription.value.trim() },
		auto: false,
	})
	try {
		await res.fetch()
		showNewDialog.value = false
		creating.value = false
		router.push({ name: 'RoadmapEditor', params: { roadmapName: res.data } })
	} catch {
		creating.value = false
	}
}

function confirmDelete(roadmap) {
	deletingRoadmap.value = roadmap
	showDeleteDialog.value = true
}

async function doDelete() {
	if (!deletingRoadmap.value) return
	deleting.value = true
	const res = createResource({
		url: 'frappe.client.delete',
		params: {
			doctype: 'LMS Roadmap',
			name: deletingRoadmap.value.name,
		},
		auto: false,
	})
	try {
		await res.fetch()
		showDeleteDialog.value = false
		deletingRoadmap.value = null
		roadmaps.reload()
	} finally {
		deleting.value = false
	}
}

const breadcrumbs = computed(() => [{ label: __('Roadmaps') }])

usePageMeta(() => ({
	title: __('Roadmaps'),
	icon: brand.favicon,
}))
</script>
