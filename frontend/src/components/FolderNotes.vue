<template>
	<!-- Edit mode -->
	<div
		v-if="isEditing"
		class="rounded-lg border border-amber-300 bg-amber-50 p-4 space-y-3"
	>
		<div class="flex items-center gap-2">
			<StickyNote class="w-4 h-4 text-amber-600" />
			<p class="text-xs font-semibold text-amber-700 uppercase tracking-wide">
				{{ __('Chỉnh sửa ghi chú thư mục') }}
			</p>
		</div>
		<textarea
			v-model="editValue"
			class="w-full rounded border border-amber-300 bg-white px-3 py-2 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-amber-400 resize-y"
			rows="4"
			:placeholder="__('Nhập ghi chú hoặc thông báo cho thư mục này...')"
		/>
		<div class="flex items-center justify-end gap-2">
			<Button variant="ghost" size="sm" @click="cancelEdit">
				{{ __('Hủy') }}
			</Button>
			<Button
				variant="solid"
				size="sm"
				:loading="saving"
				@click="saveNotes"
			>
				{{ __('Lưu') }}
			</Button>
		</div>
	</div>

	<!-- Display mode (has notes) -->
	<div
		v-else-if="folder?.folder_notes"
		class="rounded-lg border border-amber-200 bg-amber-50 p-4"
	>
		<div class="flex items-start justify-between gap-3">
			<div class="flex items-start gap-2 flex-1 min-w-0">
				<Megaphone class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
				<div class="flex-1 min-w-0">
					<p class="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">
						{{ __('Ghi chú thư mục') }}
					</p>
					<div
						class="text-sm text-amber-900 whitespace-pre-wrap break-words"
						v-html="renderedNotes"
					/>
				</div>
			</div>
			<Button
				v-if="isModerator"
				variant="ghost"
				size="sm"
				class="flex-shrink-0 text-amber-700 hover:bg-amber-100"
				@click="startEdit"
			>
				<template #prefix>
					<Pencil class="w-3.5 h-3.5" />
				</template>
				{{ __('Sửa') }}
			</Button>
		</div>
	</div>

	<!-- Add notes button (moderator, no notes yet) -->
	<div v-else-if="isModerator">
		<Button
			variant="ghost"
			size="sm"
			class="text-ink-gray-5 hover:text-amber-600"
			@click="startEdit"
		>
			<template #prefix>
				<StickyNote class="w-4 h-4" />
			</template>
			{{ __('Thêm ghi chú thư mục') }}
		</Button>
	</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Button, call, toast } from 'frappe-ui'
import { Megaphone, Pencil, StickyNote } from 'lucide-vue-next'
import { usersStore } from '@/stores/user'

const props = defineProps({
	folder: {
		type: Object,
		default: null,
	},
	folderName: {
		type: String,
		required: true,
	},
})

const emit = defineEmits(['updated'])

const { userResource } = usersStore()
const isModerator = computed(
	() => userResource.data?.is_moderator || userResource.data?.is_system_manager
)

const isEditing = ref(false)
const editValue = ref('')
const saving = ref(false)

const renderedNotes = computed(() => {
	const text = props.folder?.folder_notes || ''
	// Simple markdown-like rendering: bold, line breaks
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
		.replace(/\*(.+?)\*/g, '<em>$1</em>')
		.replace(/`(.+?)`/g, '<code class="bg-amber-100 px-1 rounded text-xs">$1</code>')
		.replace(/\n/g, '<br>')
})

function startEdit() {
	editValue.value = props.folder?.folder_notes || ''
	isEditing.value = true
}

function cancelEdit() {
	isEditing.value = false
	editValue.value = ''
}

async function saveNotes() {
	saving.value = true
	try {
		await call('lms.lms.api.update_folder_notes', {
			folder_name: props.folderName,
			notes: editValue.value,
		})
		toast.success(__('Đã lưu ghi chú'))
		isEditing.value = false
		emit('updated')
	} catch (error) {
		toast.error(error.messages?.[0] || __('Lưu thất bại'))
	} finally {
		saving.value = false
	}
}
</script>
