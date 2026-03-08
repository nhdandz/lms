<template>
	<Teleport to="body">
		<Transition name="fade">
			<div
				v-if="node"
				class="fixed inset-0 z-40 lg:hidden bg-black/30"
				@click="$emit('close')"
			/>
		</Transition>

		<Transition name="slide-right">
			<div
				v-if="node"
				class="fixed right-0 top-0 h-full w-[380px] z-50 bg-white shadow-xl flex flex-col"
			>
				<!-- Close button -->
				<div class="flex items-center justify-end px-4 py-3 shrink-0">
					<button
						@click="$emit('close')"
						class="text-gray-400 hover:text-gray-700 transition-colors"
					>
						<X class="h-5 w-5" />
					</button>
				</div>

				<!-- Course image -->
				<div class="shrink-0">
					<div v-if="courseData?.image" class="h-44 bg-gray-100 overflow-hidden">
						<img :src="courseData.image" class="w-full h-full object-cover" />
					</div>
					<div v-else class="h-28 bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
						<BookOpen class="h-12 w-12 text-blue-300" />
					</div>
				</div>

				<!-- Scrollable content -->
				<div class="flex-1 overflow-y-auto">
					<div class="px-5 py-4 space-y-4">
						<!-- Title & status -->
						<div>
							<h2 class="text-lg font-semibold text-gray-900 leading-snug">
								{{ nodeData.label || nodeData.courseTitle || nodeData.course || 'Course' }}
							</h2>
							<div class="flex items-center gap-3 mt-1.5">
								<span
									v-if="statusBadge"
									class="text-xs font-medium px-2 py-0.5 rounded-full"
									:class="statusBadge.class"
								>{{ statusBadge.label }}</span>
								<span v-if="courseData?.enrollments !== undefined" class="text-xs text-gray-500">
									{{ courseData.enrollments }} enrolled
								</span>
							</div>
						</div>

						<!-- Progress -->
						<div v-if="nodeData.progress !== undefined" class="space-y-1">
							<div class="flex justify-between text-xs text-gray-600">
								<span>Progress</span>
								<span class="font-medium">{{ Math.round(nodeData.progress) }}%</span>
							</div>
							<div class="h-2 rounded-full bg-gray-100 overflow-hidden">
								<div
									class="h-full rounded-full transition-all"
									:class="nodeData.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'"
									:style="{ width: nodeData.progress + '%' }"
								/>
							</div>
						</div>

						<!-- Tabs -->
						<div class="border-b flex gap-0">
							<button
								class="text-sm px-1 py-2 mr-4 font-medium transition-colors border-b-2 -mb-px"
								:class="activeTab === 'overview' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
								@click="activeTab = 'overview'"
							>
								Overview
							</button>
							<button
								v-if="hasResources"
								class="text-sm px-1 py-2 font-medium transition-colors border-b-2 -mb-px"
								:class="activeTab === 'resources' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
								@click="activeTab = 'resources'"
							>
								Resources
								<span class="ml-1 text-xs bg-gray-100 text-gray-600 rounded-full px-1.5 py-0.5">{{ nodeData.resources.length }}</span>
							</button>
						</div>

						<!-- Tab: Overview -->
						<div v-if="activeTab === 'overview'">
							<div v-if="loading" class="text-sm text-gray-400 py-4 text-center">Loading...</div>
							<div v-else-if="courseData?.short_introduction" class="text-sm text-gray-700 leading-relaxed">
								{{ courseData.short_introduction }}
							</div>
							<div v-else-if="nodeData.description" class="text-sm text-gray-700 leading-relaxed">
								{{ nodeData.description }}
							</div>
							<div v-else class="text-sm text-gray-400 py-4 text-center">No description available.</div>
						</div>

						<!-- Tab: Resources -->
						<div v-if="activeTab === 'resources' && hasResources" class="space-y-2">
							<button
								v-for="(res, idx) in nodeData.resources"
								:key="idx"
								class="w-full flex items-center gap-3 rounded-lg p-3 text-left hover:bg-gray-50 transition-colors border border-gray-100"
								@click="openResource(res)"
							>
								<div class="shrink-0 rounded-md p-2" :class="resourceIconBg(res.type)">
									<component :is="resourceIcon(res.type)" class="h-4 w-4" :class="resourceIconColor(res.type)" />
								</div>
								<div class="flex-1 min-w-0">
									<div class="text-sm font-medium text-gray-800 truncate">{{ res.label || res.name || res.url }}</div>
									<div class="text-xs text-gray-400 capitalize">{{ res.type }}</div>
								</div>
								<ExternalLink class="h-3.5 w-3.5 text-gray-300 shrink-0" />
							</button>
						</div>
					</div>
				</div>

				<!-- Sticky footer -->
				<div class="px-5 py-4 border-t shrink-0">
					<button
						class="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
						@click="$emit('go-to-course', nodeData.course)"
					>
						Go to Course
					</button>
				</div>
			</div>
		</Transition>
	</Teleport>
</template>
<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { X, BookOpen, FolderOpen, FileText, ExternalLink } from 'lucide-vue-next'

const props = defineProps({
	node: { type: Object, default: null },
})
const emit = defineEmits(['close', 'go-to-course'])

const router = useRouter()
const activeTab = ref('overview')
const loading = ref(false)
const courseData = ref(null)

const nodeData = computed(() => props.node?.data || {})
const hasResources = computed(() => nodeData.value.resources?.length > 0)

const statusBadge = computed(() => {
	const status = nodeData.value.status
	if (status === 'completed') return { label: 'Completed', class: 'bg-green-100 text-green-700' }
	if (status === 'in_progress') return { label: 'In Progress', class: 'bg-blue-100 text-blue-700' }
	return null
})

// Fetch course info when node changes
const courseResource = createResource({
	url: 'frappe.client.get',
	auto: false,
	onSuccess(data) {
		courseData.value = data
		loading.value = false
	},
	onError() {
		loading.value = false
	},
})

watch(
	() => props.node?.data?.course,
	(courseName) => {
		courseData.value = null
		activeTab.value = 'overview'
		if (courseName) {
			loading.value = true
			courseResource.update({ params: { doctype: 'LMS Course', name: courseName } })
			courseResource.reload()
		}
	},
	{ immediate: true }
)

function resourceIcon(type) {
	if (type === 'folder') return FolderOpen
	if (type === 'document') return FileText
	return ExternalLink
}
function resourceIconBg(type) {
	if (type === 'folder') return 'bg-amber-50'
	if (type === 'document') return 'bg-orange-50'
	return 'bg-blue-50'
}
function resourceIconColor(type) {
	if (type === 'folder') return 'text-amber-600'
	if (type === 'document') return 'text-orange-600'
	return 'text-blue-600'
}

async function openResource(resource) {
	if (resource.type === 'link') {
		window.open(resource.url, '_blank', 'noopener')
	} else if (resource.type === 'document') {
		const res = createResource({
			url: 'frappe.client.get_value',
			params: { doctype: 'LMS Document', fieldname: 'file', filters: { name: resource.name } },
			auto: false,
			onSuccess(data) {
				if (data?.file) window.open(data.file, '_blank', 'noopener')
			},
		})
		res.fetch()
	} else if (resource.type === 'folder') {
		router.push({ name: 'Documents' })
	}
}

function onKeydown(e) {
	if (e.key === 'Escape') emit('close')
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>
<style scoped>
.slide-right-enter-active,
.slide-right-leave-active {
	transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-right-enter-from,
.slide-right-leave-to {
	transform: translateX(100%);
}
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
