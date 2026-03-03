<template>
	<div class="folder-item">
		<!-- Folder Row -->
		<div
			class="flex items-center space-x-1 px-2 py-1.5 rounded-lg cursor-pointer transition-colors group"
			:class="[
				isSelected
					? 'bg-surface-gray-3 text-ink-gray-9'
					: 'hover:bg-surface-gray-2 text-ink-gray-7',
			]"
			:style="{ paddingLeft: `${level * 12 + 8}px` }"
			@click.stop="$emit('select', folder.name)"
		>
			<!-- Drag Handle -->
			<div
				v-if="canEdit"
				class="drag-handle cursor-grab opacity-0 group-hover:opacity-100 transition-opacity"
			>
				<GripVertical class="w-3 h-3 text-ink-gray-4" />
			</div>

			<!-- Expand/Collapse -->
			<button
				v-if="hasChildren"
				class="p-0.5 rounded hover:bg-surface-gray-3"
				@click.stop="$emit('toggle', folder.name)"
			>
				<ChevronRight
					class="w-3 h-3 text-ink-gray-5 transition-transform"
					:class="{ 'rotate-90': isExpanded }"
				/>
			</button>
			<div v-else class="w-4"></div>

			<!-- Icon -->
			<component
				:is="getIcon()"
				class="w-4 h-4 flex-shrink-0"
				:class="folder.is_ranking_enabled ? 'text-yellow-500' : 'text-ink-gray-5'"
			/>

			<!-- Label -->
			<span class="text-sm font-medium truncate flex-1">
				{{ folder.label }}
			</span>

			<!-- Ranking indicator -->
			<Trophy
				v-if="folder.is_ranking_enabled"
				class="w-3 h-3 text-yellow-500 flex-shrink-0"
			/>

			<!-- Count badge -->
			<span
				v-if="folder.document_count || folder.submission_count"
				class="text-xs text-ink-gray-5 bg-surface-gray-2 px-1.5 rounded"
			>
				{{ folder.is_ranking_enabled ? folder.submission_count : folder.document_count }}
			</span>

			<!-- Context Menu Button -->
			<button
				v-if="canEdit"
				class="p-0.5 rounded hover:bg-surface-gray-3 opacity-0 group-hover:opacity-100 transition-opacity"
				@click.stop="$emit('create-subfolder', folder)"
			>
				<Plus class="w-3 h-3 text-ink-gray-5" />
			</button>
		</div>

		<!-- Children (Nested Draggable) -->
		<div v-if="isExpanded && hasChildren" class="children-container">
			<Draggable
				v-model="folder.children"
				:disabled="!canEdit"
				item-key="name"
				group="folders"
				:animation="200"
				ghost-class="drag-ghost"
				drag-class="drag-active"
				handle=".drag-handle"
				@end="onChildDragEnd"
			>
				<template #item="{ element }">
					<DraggableFolderItem
						:folder="element"
						:currentFolder="currentFolder"
						:expandedFolders="expandedFolders"
						:level="level + 1"
						:canEdit="canEdit"
						@select="(name) => $emit('select', name)"
						@toggle="(name) => $emit('toggle', name)"
						@create-subfolder="(f) => $emit('create-subfolder', f)"
						@reorder="$emit('reorder')"
						@move="(name, parent) => $emit('move', name, parent)"
					/>
				</template>
			</Draggable>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import {
	Folder,
	FolderOpen,
	ChevronRight,
	GripVertical,
	Plus,
	Trophy,
	FileText,
	Book,
	Image,
	Video,
	Music,
	Code,
	Archive,
} from 'lucide-vue-next'
import Draggable from 'vuedraggable'

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
	canEdit: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['select', 'toggle', 'create-subfolder', 'reorder', 'move'])

const isSelected = computed(() => props.currentFolder === props.folder.name)
const isExpanded = computed(() => props.expandedFolders.has(props.folder.name))
const hasChildren = computed(() => props.folder.children?.length > 0)

const iconMap = {
	Folder: Folder,
	FolderOpen: FolderOpen,
	FileText: FileText,
	Book: Book,
	Image: Image,
	Video: Video,
	Music: Music,
	Code: Code,
	Archive: Archive,
}

const getIcon = () => {
	if (props.folder.icon && iconMap[props.folder.icon]) {
		return iconMap[props.folder.icon]
	}
	return isExpanded.value && hasChildren.value ? FolderOpen : Folder
}

const onChildDragEnd = () => {
	emit('reorder')
}
</script>

<style scoped>
.folder-item {
	user-select: none;
}

.drag-handle {
	cursor: grab;
}

.drag-handle:active {
	cursor: grabbing;
}
</style>
