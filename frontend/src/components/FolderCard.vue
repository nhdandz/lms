<template>
	<!-- Grid View -->
	<div
		v-if="viewMode === 'grid'"
		class="group flex flex-col items-center p-4 rounded-lg border border-transparent hover:border-outline-gray-2 hover:bg-surface-gray-1 cursor-pointer transition-all"
		@click="$emit('click')"
	>
		<div class="relative mb-2">
			<Folder class="w-12 h-12" :class="folder.is_ranking_enabled ? 'text-yellow-500' : 'text-yellow-400'" />
			<Trophy
				v-if="folder.is_ranking_enabled"
				class="absolute -top-1 -left-1 w-4 h-4 text-yellow-600 bg-yellow-100 rounded-full p-0.5"
			/>
			<div
				v-if="canDelete"
				class="absolute -top-1 -right-1 flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
			>
				<button
					class="p-1 bg-white rounded-full shadow hover:bg-blue-50"
					:title="__('Rename')"
					@click.stop="$emit('rename', folder)"
				>
					<Pencil class="w-3 h-3 text-blue-500" />
				</button>
				<button
					class="p-1 bg-white rounded-full shadow hover:bg-red-50"
					:title="__('Delete')"
					@click.stop="$emit('delete', folder)"
				>
					<Trash2 class="w-3 h-3 text-red-500" />
				</button>
			</div>
		</div>
		<span class="text-sm font-medium text-ink-gray-9 text-center truncate w-full">
			{{ folder.category_name }}
		</span>
		<span class="text-xs text-ink-gray-5">
			<template v-if="folder.is_ranking_enabled">
				{{ folder.submission_count || 0 }} {{ __('submissions') }}
			</template>
			<template v-else>
				{{ folder.document_count || 0 }} {{ __('items') }}
			</template>
		</span>
	</div>

	<!-- List View -->
	<div
		v-else
		class="group flex items-center px-3 py-2 rounded-lg hover:bg-surface-gray-1 cursor-pointer transition-colors"
		@click="$emit('click')"
	>
		<div class="relative mr-3 flex-shrink-0">
			<Folder class="w-5 h-5" :class="folder.is_ranking_enabled ? 'text-yellow-500' : 'text-yellow-400'" />
			<Trophy
				v-if="folder.is_ranking_enabled"
				class="absolute -top-1 -left-1 w-3 h-3 text-yellow-600"
			/>
		</div>
		<span class="flex-1 text-sm font-medium text-ink-gray-9 truncate">
			{{ folder.category_name }}
		</span>
		<span v-if="folder.is_ranking_enabled" class="text-xs text-yellow-600 bg-yellow-100 px-2 py-0.5 rounded mr-2">
			{{ __('Leaderboard') }}
		</span>
		<span class="text-xs text-ink-gray-5 mr-2">
			<template v-if="folder.is_ranking_enabled">
				{{ folder.submission_count || 0 }} {{ __('submissions') }}
			</template>
			<template v-else>
				{{ folder.document_count || 0 }} {{ __('items') }}
			</template>
		</span>
		<div
			v-if="canDelete"
			class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
		>
			<button
				class="p-1 rounded hover:bg-blue-50"
				:title="__('Rename')"
				@click.stop="$emit('rename', folder)"
			>
				<Pencil class="w-4 h-4 text-blue-500" />
			</button>
			<button
				class="p-1 rounded hover:bg-surface-gray-2"
				:title="__('Delete')"
				@click.stop="$emit('delete', folder)"
			>
				<Trash2 class="w-4 h-4 text-red-500" />
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { Folder, Trash2, Trophy, Pencil } from 'lucide-vue-next'

const user = inject('$user')

const props = defineProps({
	folder: { type: Object, required: true },
	viewMode: { type: String, default: 'grid' },
})

defineEmits(['click', 'delete', 'rename'])

const canDelete = computed(() => {
	if (!user.data) return false
	return user.data.is_moderator || user.data.is_system_manager
})
</script>
