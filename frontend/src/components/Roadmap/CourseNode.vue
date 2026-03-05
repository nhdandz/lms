<template>
	<div
		class="course-node rounded-lg border-2 px-4 py-3 min-w-[180px] max-w-[240px] shadow-sm cursor-pointer"
		:class="nodeClass"
	>
		<Handle type="target" :position="Position.Left" />
		<Handle type="source" :position="Position.Right" />
		<div class="flex items-center gap-2 mb-1.5">
			<BookOpen class="h-4 w-4 shrink-0" />
			<span class="text-xs font-semibold uppercase tracking-wide opacity-60">Course</span>
		</div>
		<div class="font-semibold text-sm leading-tight">
			{{ data.label || data.courseTitle || data.course || 'Untitled Course' }}
		</div>
		<div v-if="data.course && data.label !== data.course" class="text-xs opacity-50 mt-0.5 truncate">
			{{ data.course }}
		</div>
		<div v-if="data.progress !== undefined" class="mt-2 space-y-0.5">
			<div class="h-1.5 rounded-full bg-black/10 overflow-hidden">
				<div
					class="h-full rounded-full transition-all"
					:class="progressBarClass"
					:style="{ width: data.progress + '%' }"
				/>
			</div>
			<div class="text-xs opacity-60">{{ Math.round(data.progress) }}%</div>
		</div>
	</div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { BookOpen } from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps({
	data: { type: Object, default: () => ({}) },
	selected: Boolean,
})

const nodeClass = computed(() => {
	const status = props.data.status
	if (status === 'completed') return 'border-green-500 bg-green-50 text-green-900'
	if (status === 'in_progress') return 'border-blue-500 bg-blue-50 text-blue-900'
	if (props.selected) return 'border-blue-500 bg-blue-50 text-blue-900'
	return 'border-blue-300 bg-white text-blue-900'
})

const progressBarClass = computed(() => {
	if (props.data.status === 'completed') return 'bg-green-500'
	return 'bg-blue-500'
})
</script>
