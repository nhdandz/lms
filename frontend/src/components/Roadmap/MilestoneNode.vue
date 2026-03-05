<template>
	<div
		class="milestone-node rounded-lg border-2 px-4 py-3 min-w-[160px] max-w-[220px] shadow-sm"
		:class="selected ? 'border-green-600 bg-green-100' : 'border-green-400 bg-green-50'"
	>
		<Handle type="target" :position="Position.Left" />
		<Handle type="source" :position="Position.Right" />
		<div class="flex items-center gap-2 mb-1">
			<Trophy class="h-4 w-4 shrink-0 text-green-600" />
			<span class="text-xs font-semibold uppercase tracking-wide text-green-700">Milestone</span>
		</div>
		<div class="font-semibold text-sm text-green-900 leading-tight">{{ data.label || 'Milestone' }}</div>
		<div v-if="data.description" class="text-xs text-green-700 mt-1">{{ data.description }}</div>
	</div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { Trophy } from 'lucide-vue-next'

defineProps({
	data: { type: Object, default: () => ({}) },
	selected: Boolean,
})
</script>
