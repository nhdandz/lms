<template>
	<div
		class="doc-node rounded-lg border-2 px-4 py-3 min-w-[180px] max-w-[240px] shadow-sm cursor-pointer"
		:class="selected ? 'border-orange-500 bg-orange-50 text-orange-900' : 'border-orange-300 bg-white text-orange-900'"
	>
		<Handle type="target" :position="Position.Left" />
		<Handle type="source" :position="Position.Right" />
		<div class="flex items-center gap-2 mb-1.5">
			<FileText class="h-4 w-4 shrink-0" />
			<span class="text-xs font-semibold uppercase tracking-wide opacity-60">Document</span>
		</div>
		<div class="font-semibold text-sm leading-tight">
			{{ data.label || data.documentTitle || data.document || 'Untitled Document' }}
		</div>
		<div v-if="data.fileType" class="text-xs opacity-50 mt-0.5 uppercase">
			{{ data.fileType }}
		</div>
	</div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { FileText } from 'lucide-vue-next'

defineProps({
	data: { type: Object, default: () => ({}) },
	selected: Boolean,
})
</script>
