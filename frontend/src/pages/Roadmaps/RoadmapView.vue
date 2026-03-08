<template>
	<div class="flex flex-col h-screen">
		<!-- Header -->
		<header
			class="sticky top-0 z-20 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5 shrink-0"
		>
			<div class="flex items-center gap-3">
				<Breadcrumbs :items="breadcrumbs" />
				<span v-if="roadmap.data" class="font-semibold text-ink-gray-9">{{ roadmap.data.title }}</span>
			</div>
			<Button
				v-if="isInstructor"
				@click="$router.push({ name: 'RoadmapEditor', params: { roadmapName } })"
				variant="outline"
				size="sm"
			>
				<template #prefix><Pencil class="h-3.5 w-3.5" /></template>
				{{ __('Edit') }}
			</Button>
		</header>

		<div class="flex-1 relative" v-if="roadmap.data">
			<VueFlow
				:nodes="nodes"
				:edges="edges"
				:node-types="customNodeTypes"
				fit-view-on-init
				:nodes-draggable="false"
				:nodes-connectable="false"
				:elements-selectable="true"
				class="h-full"
				@node-click="onNodeClick"
			>
				<Background />
				<Controls :show-interactive="false" />
				<MiniMap />
			</VueFlow>

			<NodeDetailDrawer
				:node="selectedNode"
				@close="selectedNode = null"
				@go-to-course="goToCourse"
			/>
		</div>
	</div>
</template>
<script setup>
import { ref, computed, inject, onMounted, markRaw } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { Breadcrumbs, Button, createResource } from 'frappe-ui'
import { Pencil } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import CourseNode from '@/components/Roadmap/CourseNode.vue'
import NoteNode from '@/components/Roadmap/NoteNode.vue'
import MilestoneNode from '@/components/Roadmap/MilestoneNode.vue'
import LinkNode from '@/components/Roadmap/LinkNode.vue'
import DocumentNode from '@/components/Roadmap/DocumentNode.vue'
import NodeDetailDrawer from '@/components/Roadmap/NodeDetailDrawer.vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const props = defineProps({ roadmapName: { type: String, required: true } })
const user = inject('$user')
const router = useRouter()

const nodes = ref([])
const edges = ref([])
const selectedNode = ref(null)

const customNodeTypes = {
	course: markRaw(CourseNode),
	note: markRaw(NoteNode),
	milestone: markRaw(MilestoneNode),
	link: markRaw(LinkNode),
	document: markRaw(DocumentNode),
}

const roadmap = createResource({
	url: 'lms.lms.api.get_roadmap',
	params: { roadmap_name: props.roadmapName },
	auto: false,
	onSuccess(data) {
		nodes.value = data.nodes || []
		edges.value = data.edges || []
	},
})

onMounted(() => {
	roadmap.reload()
})

const isInstructor = computed(() => user.data?.is_moderator || user.data?.is_instructor)

function onNodeClick({ node }) {
	if (node.type === 'course' && node.data?.course) {
		selectedNode.value = node
	} else if (node.type === 'link' && node.data?.url) {
		window.open(node.data.url, '_blank', 'noopener')
	} else if (node.type === 'document' && node.data?.file) {
		window.open(node.data.file, '_blank', 'noopener')
	} else if (node.type === 'document' && node.data?.document) {
		const res = createResource({
			url: 'frappe.client.get_value',
			params: {
				doctype: 'LMS Document',
				fieldname: 'file',
				filters: { name: node.data.document },
			},
			auto: false,
			onSuccess(data) {
				if (data?.file) window.open(data.file, '_blank', 'noopener')
			},
		})
		res.fetch()
	}
}

function goToCourse(courseName) {
	selectedNode.value = null
	router.push({ name: 'CourseDetail', params: { courseName } })
}

const breadcrumbs = computed(() => [
	{ label: __('Roadmaps'), route: { name: 'RoadmapList' } },
	{ label: roadmap.data?.title || props.roadmapName },
])
</script>
