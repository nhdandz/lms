<template>
	<div
		class="link-node rounded-lg border-2 px-4 py-3 min-w-[160px] max-w-[220px] shadow-sm"
		:class="selected ? 'border-purple-600 bg-purple-100' : 'border-purple-400 bg-purple-50'"
	>
		<Handle type="target" :position="Position.Left" />
		<Handle type="source" :position="Position.Right" />
		<div class="flex items-center gap-2 mb-1">
			<Link2 class="h-4 w-4 shrink-0 text-purple-600" />
			<span class="text-xs font-semibold uppercase tracking-wide text-purple-700">Link</span>
		</div>
		<div class="font-semibold text-sm text-purple-900 leading-tight">{{ data.label || 'Link' }}</div>
		<div v-if="data.url" class="text-xs text-purple-500 mt-1 truncate">{{ data.url }}</div>
	</div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { Link2 } from 'lucide-vue-next'

defineProps({
	data: { type: Object, default: () => ({}) },
	selected: Boolean,
})
</script>
