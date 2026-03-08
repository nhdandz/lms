<template>
	<div
		class="course-node relative bg-white rounded shadow-sm border border-gray-200 w-[220px] cursor-pointer select-none"
		:class="[accentClass, selected ? 'ring-2 ring-blue-500 ring-offset-1' : '']"
		style="border-left-width: 3px;"
	>
		<Handle type="target" :position="Position.Left" />
		<Handle type="source" :position="Position.Right" />

		<div class="px-3 py-2.5">
			<!-- Header row -->
			<div class="flex items-center justify-between mb-1.5">
				<div class="flex items-center gap-1.5">
					<BookOpen class="h-3.5 w-3.5 text-gray-400 shrink-0" />
					<span class="text-[10px] font-semibold uppercase tracking-wide text-gray-400">Course</span>
				</div>
				<span
					v-if="statusBadge"
					class="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
					:class="statusBadge.class"
				>{{ statusBadge.label }}</span>
			</div>

			<!-- Title -->
			<div class="font-semibold text-sm text-gray-800 leading-tight line-clamp-2">
				{{ data.label || data.courseTitle || data.course || 'Untitled Course' }}
			</div>

			<!-- Progress bar -->
			<div v-if="data.progress !== undefined" class="mt-2 space-y-0.5">
				<div class="h-1.5 rounded-full bg-gray-100 overflow-hidden">
					<div
						class="h-full rounded-full transition-all"
						:class="progressBarClass"
						:style="{ width: data.progress + '%' }"
					/>
				</div>
				<div class="text-[10px] text-gray-400">{{ Math.round(data.progress) }}%</div>
			</div>

			<!-- Resources count -->
			<div v-if="data.resources?.length" class="flex items-center gap-1 mt-1.5">
				<Paperclip class="h-3 w-3 text-gray-400" />
				<span class="text-[10px] text-gray-400">{{ data.resources.length }} resource{{ data.resources.length > 1 ? 's' : '' }}</span>
			</div>
		</div>
	</div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { BookOpen, Paperclip } from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps({
	data: { type: Object, default: () => ({}) },
	selected: Boolean,
})

const accentClass = computed(() => {
	const status = props.data.status
	if (status === 'completed') return 'border-l-green-500'
	if (status === 'in_progress') return 'border-l-blue-500'
	return 'border-l-gray-300'
})

const statusBadge = computed(() => {
	const status = props.data.status
	if (status === 'completed') return { label: 'Done', class: 'bg-green-100 text-green-700' }
	if (status === 'in_progress') return { label: 'In Progress', class: 'bg-blue-100 text-blue-700' }
	return null
})

const progressBarClass = computed(() => {
	if (props.data.status === 'completed') return 'bg-green-500'
	return 'bg-blue-500'
})
</script>
