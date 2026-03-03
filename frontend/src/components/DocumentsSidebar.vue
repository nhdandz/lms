<template>
	<div class="h-full flex flex-col border-r bg-surface-gray-1">
		<!-- Header -->
		<div class="p-4 border-b">
			<div class="flex items-center justify-between mb-3">
				<h3 class="font-semibold text-ink-gray-9">
					{{ __('Folders') }}
				</h3>
				<div class="flex items-center gap-1">
					<Button
						v-if="canEdit && hasChanges"
						variant="ghost"
						size="sm"
						@click="saveOrder"
						:loading="saving"
						:title="__('Save Order')"
					>
						<Save class="w-4 h-4 text-green-600" />
					</Button>
					<Button
						v-if="canCreate"
						variant="ghost"
						size="sm"
						@click="showCreateFolder = true"
						:title="__('New Folder')"
					>
						<FolderPlus class="w-4 h-4" />
					</Button>
				</div>
			</div>
			<p v-if="canEdit" class="text-xs text-ink-gray-5">
				{{ __('Drag folders to reorder') }}
			</p>
		</div>

		<!-- Folder Tree -->
		<div class="flex-1 overflow-y-auto p-2">
			<!-- All Documents -->
			<div
				class="flex items-center space-x-2 px-3 py-2 rounded-lg cursor-pointer transition-colors"
				:class="
					currentFolder === null
						? 'bg-surface-gray-3 text-ink-gray-9'
						: 'hover:bg-surface-gray-2 text-ink-gray-7'
				"
				@click="selectFolder(null)"
			>
				<Home class="w-4 h-4 flex-shrink-0" />
				<span class="text-sm font-medium truncate">{{ __('All Documents') }}</span>
			</div>

			<!-- Draggable Folder Tree -->
			<Draggable
				v-model="localFolderTree"
				:disabled="!canEdit"
				item-key="name"
				group="folders"
				:animation="200"
				ghost-class="drag-ghost"
				drag-class="drag-active"
				handle=".drag-handle"
				@end="onDragEnd"
			>
				<template #item="{ element }">
					<DraggableFolderItem
						:folder="element"
						:currentFolder="currentFolder"
						:expandedFolders="expandedFolders"
						:level="0"
						:canEdit="canEdit"
						@select="selectFolder"
						@toggle="toggleFolder"
						@create-subfolder="openCreateSubfolder"
						@reorder="onNestedReorder"
						@move="onFolderMove"
					/>
				</template>
			</Draggable>
		</div>

		<!-- Storage Info -->
		<div class="p-4 border-t">
			<div class="text-xs text-ink-gray-5">
				{{ totalDocuments }} {{ __('documents') }}
			</div>
		</div>

		<!-- Create Folder Dialog -->
		<Dialog
			v-model="showCreateFolder"
			:options="{
				title: parentForNewFolder
					? __('New Subfolder')
					: __('New Folder'),
				size: 'sm',
				actions: [
					{
						label: __('Create'),
						variant: 'solid',
						onClick: (close) => createFolder(close),
					},
				],
			}"
		>
			<template #body-content>
				<div class="space-y-4">
					<FormControl
						:label="__('Folder Name')"
						v-model="newFolderName"
						:placeholder="__('Enter folder name')"
					/>
					<FormControl
						type="checkbox"
						v-model="newFolderRanking"
						:label="__('Enable Ranking/Leaderboard')"
					/>
					<div v-if="parentForNewFolder" class="text-sm text-ink-gray-5">
						{{ __('Creating inside:') }}
						<span class="font-medium">{{ parentForNewFolder.label }}</span>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { ref, computed, inject, watch } from 'vue'
import { Button, Dialog, FormControl, createResource, toast, call } from 'frappe-ui'
import { Home, FolderPlus, Save } from 'lucide-vue-next'
import Draggable from 'vuedraggable'
import DraggableFolderItem from './DraggableFolderItem.vue'

const user = inject('$user')

const props = defineProps({
	currentFolder: {
		type: String,
		default: null,
	},
})

const emit = defineEmits(['select-folder'])

const expandedFolders = ref(new Set())
const showCreateFolder = ref(false)
const newFolderName = ref('')
const newFolderRanking = ref(false)
const parentForNewFolder = ref(null)
const localFolderTree = ref([])
const hasChanges = ref(false)
const saving = ref(false)

const canCreate = computed(() => {
	return (
		user.data?.is_instructor ||
		user.data?.is_moderator ||
		user.data?.is_system_manager
	)
})

const canEdit = computed(() => {
	return user.data?.is_moderator || user.data?.is_system_manager
})

const folderTreeResource = createResource({
	url: 'lms.lms.api.get_folder_tree',
	auto: true,
	onSuccess(data) {
		localFolderTree.value = JSON.parse(JSON.stringify(data || []))
		hasChanges.value = false
	},
})

const totalDocuments = computed(() => {
	const countDocs = (folders) => {
		let total = 0
		for (const folder of folders) {
			total += folder.document_count || 0
			if (folder.children?.length) {
				total += countDocs(folder.children)
			}
		}
		return total
	}
	return countDocs(localFolderTree.value)
})

const selectFolder = (folderName) => {
	emit('select-folder', folderName)
}

const toggleFolder = (folderName) => {
	if (expandedFolders.value.has(folderName)) {
		expandedFolders.value.delete(folderName)
	} else {
		expandedFolders.value.add(folderName)
	}
}

const openCreateSubfolder = (folder) => {
	parentForNewFolder.value = folder
	showCreateFolder.value = true
}

const onDragEnd = () => {
	hasChanges.value = true
}

const onNestedReorder = () => {
	hasChanges.value = true
}

const onFolderMove = (folderName, newParent) => {
	// This is handled by the nested draggable
	hasChanges.value = true
}

// Flatten tree for saving
const flattenTree = (folders, parent = null, order = { value: 0 }) => {
	const result = []
	for (const folder of folders) {
		result.push({
			name: folder.name,
			parent_category: parent,
			sort_order: order.value++,
		})
		if (folder.children?.length) {
			result.push(...flattenTree(folder.children, folder.name, order))
		}
	}
	return result
}

const saveOrder = async () => {
	saving.value = true
	try {
		const folderOrders = flattenTree(localFolderTree.value)
		await call('lms.lms.api.bulk_reorder_folders', {
			folder_orders: folderOrders,
		})
		toast.success(__('Folder order saved'))
		hasChanges.value = false
		folderTreeResource.reload()
	} catch (error) {
		toast.error(error.messages?.[0] || __('Failed to save order'))
	} finally {
		saving.value = false
	}
}

const createFolderResource = createResource({
	url: 'lms.lms.api.create_folder',
	onSuccess() {
		toast.success(__('Folder created successfully'))
		folderTreeResource.reload()
		newFolderName.value = ''
		newFolderRanking.value = false
		parentForNewFolder.value = null
	},
	onError(err) {
		toast.error(err.messages?.[0] || __('Failed to create folder'))
	},
})

const createFolder = (close) => {
	if (!newFolderName.value.trim()) {
		toast.error(__('Folder name is required'))
		return
	}

	createFolderResource.submit({
		category_name: newFolderName.value.trim(),
		parent_category: parentForNewFolder.value?.name || null,
		is_ranking_enabled: newFolderRanking.value,
	})
	close()
}

defineExpose({
	reload: () => folderTreeResource.reload(),
})
</script>

<style>
.drag-ghost {
	opacity: 0.5;
	background: #e2e8f0;
	border-radius: 0.5rem;
}

.drag-active {
	background: #fff;
	box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
	border-radius: 0.5rem;
}
</style>
