<template>
	<div class="flex flex-col h-screen">
		<!-- Header -->
		<header
			class="sticky top-0 z-20 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5 shrink-0"
		>
			<div class="flex items-center gap-2">
				<Breadcrumbs :items="breadcrumbs" />
			</div>
			<div class="flex items-center gap-2">
				<span v-if="roadmap.data" class="text-sm font-medium text-ink-gray-8">
					{{ roadmap.data.title }}
				</span>
				<Button @click="togglePublish" variant="outline" size="sm" :loading="toggling">
					{{ roadmap.data?.published ? __('Unpublish') : __('Publish') }}
				</Button>
				<Button @click="saveRoadmap" variant="solid" size="sm" :loading="saving">
					{{ __('Save') }}
				</Button>
			</div>
		</header>

		<div class="flex flex-1 overflow-hidden">
			<!-- Left Toolbar: Add Node Types -->
			<div class="w-14 border-r bg-surface-white flex flex-col items-center pt-4 gap-2 shrink-0">
				<button
					v-for="type in nodeTypeList"
					:key="type.key"
					class="w-10 h-10 rounded-lg border flex items-center justify-center hover:bg-surface-gray-2 transition-colors"
					:title="type.label"
					@click="addNode(type.key)"
				>
					<component :is="type.icon" class="h-5 w-5" :class="type.colorClass" />
				</button>
			</div>

			<!-- Vue Flow Canvas -->
			<div class="flex-1 relative overflow-hidden">
				<VueFlow
					v-model:nodes="nodes"
					v-model:edges="edges"
					:node-types="customNodeTypes"
					fit-view-on-init
					class="h-full w-full bg-surface-gray-1"
					@node-click="onNodeClick"
					@pane-click="selectedNode = null"
					@connect="onConnect"
				>
					<Background pattern-color="#aaa" :gap="20" />
					<Controls />
					<MiniMap />
				</VueFlow>
			</div>

			<!-- Right Panel: Edit selected node -->
			<NodePanel
				v-if="selectedNode"
				:node="selectedNode"
				@update="onNodeDataUpdate"
				@close="selectedNode = null"
				@delete="deleteNode"
			/>
		</div>
	</div>
</template>
<script setup>
import { ref, computed, inject, onMounted, markRaw } from 'vue'
import { VueFlow, useVueFlow, addEdge } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { Breadcrumbs, Button, createResource } from 'frappe-ui'
import { BookOpen, StickyNote, Link2, Trophy, FileText } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import CourseNode from '@/components/Roadmap/CourseNode.vue'
import NoteNode from '@/components/Roadmap/NoteNode.vue'
import MilestoneNode from '@/components/Roadmap/MilestoneNode.vue'
import LinkNode from '@/components/Roadmap/LinkNode.vue'
import DocumentNode from '@/components/Roadmap/DocumentNode.vue'
import NodePanel from '@/components/Roadmap/NodePanel.vue'

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
const saving = ref(false)
const toggling = ref(false)

const customNodeTypes = {
	course: markRaw(CourseNode),
	note: markRaw(NoteNode),
	milestone: markRaw(MilestoneNode),
	link: markRaw(LinkNode),
	document: markRaw(DocumentNode),
}

const nodeTypeList = [
	{ key: 'course', label: 'Add Course', icon: BookOpen, colorClass: 'text-blue-600' },
	{ key: 'note', label: 'Add Note', icon: StickyNote, colorClass: 'text-yellow-500' },
	{ key: 'link', label: 'Add Link', icon: Link2, colorClass: 'text-purple-600' },
	{ key: 'milestone', label: 'Add Milestone', icon: Trophy, colorClass: 'text-green-600' },
	{ key: 'document', label: 'Add Document', icon: FileText, colorClass: 'text-orange-500' },
]

const roadmap = createResource({
	url: 'lms.lms.api.get_roadmap',
	params: { roadmap_name: props.roadmapName },
	auto: false,
	onSuccess(data) {
		nodes.value = (data.nodes || []).map((n) => ({
			...n,
			// Đảm bảo position hợp lệ
			position: n.position || { x: 100, y: 100 },
		}))
		edges.value = data.edges || []
	},
})

onMounted(() => {
	if (!user.data?.is_moderator && !user.data?.is_instructor) {
		router.push({ name: 'RoadmapList' })
		return
	}
	roadmap.reload()
})

let nodeCounter = 0

function addNode(type) {
	nodeCounter++
	const id = `node-${Date.now()}-${nodeCounter}`
	const defaults = {
		course: { label: '', course: '', courseTitle: '', type: 'course' },
		note: { label: 'New Note', type: 'note' },
		link: { label: 'New Link', url: '', type: 'link' },
		milestone: { label: 'New Milestone', description: '', type: 'milestone' },
		document: { label: '', document: '', documentTitle: '', file: '', fileType: '', type: 'document' },
	}
	// Tính position ngẫu nhiên trên canvas
	const x = 80 + Math.floor(nodeCounter * 50 + Math.random() * 200)
	const y = 80 + Math.floor((nodeCounter % 4) * 120)
	nodes.value = [
		...nodes.value,
		{
			id,
			type,
			position: { x, y },
			data: defaults[type],
		},
	]
	// Tự chọn node vừa thêm để mở panel edit
	selectedNode.value = nodes.value[nodes.value.length - 1]
}

function onNodeClick({ node }) {
	selectedNode.value = node
}

function onConnect(params) {
	edges.value = addEdge({ ...params, animated: false }, edges.value)
}

function onNodeDataUpdate(newData) {
	if (!selectedNode.value) return
	const id = selectedNode.value.id
	nodes.value = nodes.value.map((n) =>
		n.id === id ? { ...n, data: { ...newData } } : n
	)
	selectedNode.value = { ...selectedNode.value, data: { ...newData } }
}

function deleteNode() {
	if (!selectedNode.value) return
	const id = selectedNode.value.id
	nodes.value = nodes.value.filter((n) => n.id !== id)
	edges.value = edges.value.filter((e) => e.source !== id && e.target !== id)
	selectedNode.value = null
}

async function saveRoadmap() {
	saving.value = true
	const graphJson = JSON.stringify({ nodes: nodes.value, edges: edges.value })
	const res = createResource({
		url: 'lms.lms.api.save_roadmap',
		params: {
			roadmap_name: props.roadmapName,
			title: roadmap.data?.title || '',
			description: roadmap.data?.description || '',
			roadmap_json: graphJson,
		},
	})
	try {
		await res.fetch()
	} finally {
		saving.value = false
	}
}

async function togglePublish() {
	toggling.value = true
	const res = createResource({
		url: 'frappe.client.set_value',
		params: {
			doctype: 'LMS Roadmap',
			name: props.roadmapName,
			fieldname: 'published',
			value: roadmap.data?.published ? 0 : 1,
		},
	})
	try {
		await res.fetch()
		await roadmap.reload()
	} finally {
		toggling.value = false
	}
}

const breadcrumbs = computed(() => [
	{ label: __('Roadmaps'), route: { name: 'RoadmapList' } },
	{ label: __('Editor') },
])
</script>
