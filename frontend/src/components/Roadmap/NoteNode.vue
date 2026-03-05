<template>
	<div
		class="note-node rounded-lg border-2 px-4 py-3 min-w-[160px] max-w-[220px] shadow-sm"
		:class="selected ? 'border-yellow-500 bg-yellow-100' : 'border-yellow-300 bg-yellow-50'"
	>
		<Handle type="target" :position="Position.Left" />
		<Handle type="source" :position="Position.Right" />
		<div class="flex items-center gap-2 mb-1">
			<StickyNote class="h-4 w-4 shrink-0 text-yellow-600" />
			<span class="text-xs font-semibold uppercase tracking-wide text-yellow-700">Note</span>
		</div>
		<div class="text-sm text-yellow-900 leading-snug whitespace-pre-wrap break-words">{{ data.label || 'Note' }}</div>
	</div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { StickyNote } from 'lucide-vue-next'

defineProps({
	data: { type: Object, default: () => ({}) },
	selected: Boolean,
})
</script>
