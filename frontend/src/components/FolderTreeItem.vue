<template>
	<div>
		<div
			class="group flex items-center space-x-1 px-2 py-1.5 rounded-lg cursor-pointer transition-colors"
			:class="[
				isSelected
					? 'bg-surface-gray-3 text-ink-gray-9'
					: 'hover:bg-surface-gray-2 text-ink-gray-7',
			]"
			:style="{ paddingLeft: `${level * 12 + 8}px` }"
			@click="$emit('select', folder.name)"
		>
			<!-- Expand/Collapse Toggle -->
			<button
				v-if="hasChildren"
				class="p-0.5 hover:bg-surface-gray-3 rounded"
				@click.stop="$emit('toggle', folder.name)"
			>
				<ChevronRight
					class="w-3.5 h-3.5 transition-transform"
					:class="{ 'rotate-90': isExpanded }"
				/>
			</button>
			<div v-else class="w-4" />

			<!-- Folder Icon -->
			<component
				:is="folderIcon"
				class="w-4 h-4 flex-shrink-0"
				:class="isExpanded || isSelected ? 'text-yellow-500' : 'text-ink-gray-5'"
			/>

			<!-- Folder Name -->
			<span class="text-sm truncate flex-1">{{ folder.label }}</span>

			<!-- Document Count Badge -->
			<span
				v-if="folder.document_count > 0"
				class="text-xs text-ink-gray-4 bg-surface-gray-2 px-1.5 py-0.5 rounded"
			>
				{{ folder.document_count }}
			</span>

			<!-- Create Subfolder Button -->
			<button
				v-if="canCreate"
				class="p-1 hover:bg-surface-gray-3 rounded opacity-0 group-hover:opacity-100 transition-opacity"
				@click.stop="$emit('create-subfolder', folder)"
				:title="__('Create subfolder')"
			>
				<FolderPlus class="w-3.5 h-3.5 text-ink-gray-5" />
			</button>
		</div>

		<!-- Children -->
		<div v-if="hasChildren && isExpanded">
			<FolderTreeItem
				v-for="child in folder.children"
				:key="child.name"
				:folder="child"
				:currentFolder="currentFolder"
				:expandedFolders="expandedFolders"
				:level="level + 1"
				@select="(name) => $emit('select', name)"
				@toggle="(name) => $emit('toggle', name)"
				@create-subfolder="(f) => $emit('create-subfolder', f)"
			/>
		</div>
	</div>
</template>

<script setup>
import { computed, inject } from 'vue'
import {
	Folder,
	FolderOpen,
	FolderPlus,
	ChevronRight,
} from 'lucide-vue-next'

const user = inject('$user')

const props = defineProps({
	folder: {
		type: Object,
		required: true,
	},
	currentFolder: {
		type: String,
		default: null,
	},
	expandedFolders: {
		type: Set,
		required: true,
	},
	level: {
		type: Number,
		default: 0,
	},
})

defineEmits(['select', 'toggle', 'create-subfolder'])

const hasChildren = computed(() => {
	return props.folder.children && props.folder.children.length > 0
})

const isExpanded = computed(() => {
	return props.expandedFolders.has(props.folder.name)
})

const isSelected = computed(() => {
	return props.currentFolder === props.folder.name
})

const folderIcon = computed(() => {
	return isExpanded.value || isSelected.value ? FolderOpen : Folder
})

const canCreate = computed(() => {
	return (
		user.data?.is_instructor ||
		user.data?.is_moderator ||
		user.data?.is_system_manager
	)
})
</script>
