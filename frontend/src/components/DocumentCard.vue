<template>
	<!-- Grid View -->
	<div
		v-if="viewMode === 'grid'"
		class="flex flex-col border rounded-lg p-4 h-full hover:border-outline-gray-3 hover:shadow-sm transition-all cursor-pointer"
		@click="handleCardClick"
	>
		<div class="flex items-start space-x-3 mb-3">
			<div
				class="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center"
				:class="iconBgClass"
			>
				<component
					:is="fileIcon"
					class="w-5 h-5"
					:class="iconColorClass"
				/>
			</div>
			<div class="flex-1 min-w-0">
				<h3
					class="text-sm font-semibold text-ink-gray-9 truncate"
					:title="document.title"
				>
					{{ document.title }}
				</h3>
				<div class="flex items-center space-x-2 mt-1">
					<span v-if="isLink" class="text-xs text-blue-500 truncate max-w-[140px]">
						{{ document.file }}
					</span>
					<span v-else class="text-xs text-ink-gray-5">
						{{ document.file_type }}
						{{ document.file_size ? `- ${document.file_size}` : '' }}
					</span>
				</div>
			</div>
		</div>

		<p
			v-if="strippedDescription"
			class="text-sm text-ink-gray-6 line-clamp-2 mb-3 flex-1"
		>
			{{ strippedDescription }}
		</p>

		<div
			class="flex items-center justify-between mt-auto pt-3 border-t"
		>
			<div
				class="flex items-center space-x-3 text-xs text-ink-gray-5"
			>
				<span class="flex items-center space-x-1">
					<Eye class="w-3 h-3" />
					<span>{{ document.view_count || 0 }}</span>
				</span>
				<span class="flex items-center space-x-1">
					<Download class="w-3 h-3" />
					<span>{{ document.download_count || 0 }}</span>
				</span>
			</div>

			<div class="flex items-center space-x-1">
				<Button
					v-if="canPreview && !isLink"
					variant="ghost"
					size="sm"
					@click.stop="$emit('preview', document)"
					:title="__('Preview')"
				>
					<Eye class="w-4 h-4" />
				</Button>
				<Button
					v-if="isLink"
					variant="ghost"
					size="sm"
					@click.stop="handleCardClick"
					:title="__('Open link')"
				>
					<ExternalLink class="w-4 h-4 text-blue-500" />
				</Button>
				<Button
					v-else
					variant="ghost"
					size="sm"
					@click.stop="$emit('download', document)"
					:title="__('Download')"
				>
					<Download class="w-4 h-4" />
				</Button>
				<Button
					v-if="canDelete"
					variant="ghost"
					size="sm"
					@click.stop="$emit('delete', document)"
					:title="__('Delete')"
				>
					<Trash2 class="w-4 h-4 text-red-500" />
				</Button>
			</div>
		</div>
	</div>

	<!-- List View -->
	<div
		v-else
		class="group flex items-center px-3 py-2 rounded-lg hover:bg-surface-gray-1 cursor-pointer transition-colors"
		@click="handleCardClick"
	>
		<component
			:is="fileIcon"
			class="w-5 h-5 mr-3 flex-shrink-0"
			:class="iconColorClass"
		/>
		<span
			class="flex-1 text-sm font-medium text-ink-gray-9 truncate mr-4"
		>
			{{ document.title }}
		</span>
		<span class="text-xs text-ink-gray-5 mr-4 hidden sm:block">
			{{ document.file_type }}
		</span>
		<span class="text-xs text-ink-gray-5 mr-4 hidden md:block">
			{{ document.file_size }}
		</span>
		<div
			class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity"
		>
			<button
				v-if="canPreview && !isLink"
				class="p-1.5 rounded hover:bg-surface-gray-2"
				@click.stop="$emit('preview', document)"
				:title="__('Preview')"
			>
				<Eye class="w-4 h-4 text-ink-gray-6" />
			</button>
			<button
				v-if="isLink"
				class="p-1.5 rounded hover:bg-surface-gray-2"
				@click.stop="handleCardClick"
				:title="__('Open link')"
			>
				<ExternalLink class="w-4 h-4 text-blue-500" />
			</button>
			<button
				v-else
				class="p-1.5 rounded hover:bg-surface-gray-2"
				@click.stop="$emit('download', document)"
				:title="__('Download')"
			>
				<Download class="w-4 h-4 text-ink-gray-6" />
			</button>
			<button
				v-if="canDelete"
				class="p-1.5 rounded hover:bg-surface-gray-2"
				@click.stop="$emit('delete', document)"
				:title="__('Delete')"
			>
				<Trash2 class="w-4 h-4 text-red-500" />
			</button>
		</div>
	</div>
</template>

<script setup>
import { computed, inject } from 'vue'
import { Button } from 'frappe-ui'
import {
	FileText,
	FileImage,
	File,
	Eye,
	Download,
	Trash2,
	FileSpreadsheet,
	FileCode,
	FileArchive,
	FileVideo,
	FileAudio,
	ExternalLink,
} from 'lucide-vue-next'

const user = inject('$user')

const props = defineProps({
	document: {
		type: Object,
		required: true,
	},
	viewMode: {
		type: String,
		default: 'grid',
	},
})

const emit = defineEmits(['preview', 'download', 'delete'])

const isLink = computed(() => (props.document.file_type || '').toLowerCase() === 'link')

// Click on card to preview (if supported) or download
const handleCardClick = () => {
	if (isLink.value && props.document.file) {
		window.open(props.document.file, '_blank', 'noopener')
		return
	}
	if (canPreview.value) {
		emit('preview', props.document)
	} else {
		emit('download', props.document)
	}
}

const fileType = computed(() => {
	return (props.document.file_type || '').toLowerCase()
})

const fileIcon = computed(() => {
	const type = fileType.value
	if (type === 'link') return ExternalLink
	if (type === 'pdf') return FileText
	if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tiff', 'tif'].includes(type))
		return FileImage
	if (['xls', 'xlsx', 'csv', 'ods'].includes(type)) return FileSpreadsheet
	if (['js', 'ts', 'py', 'html', 'css', 'json', 'xml', 'php', 'java', 'c', 'cpp', 'h', 'rb', 'go', 'rs', 'swift', 'kt', 'sh', 'bash', 'sql', 'yml', 'yaml', 'md', 'vue', 'jsx', 'tsx'].includes(type))
		return FileCode
	if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'tgz'].includes(type)) return FileArchive
	if (['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv', 'flv', 'm4v', '3gp'].includes(type)) return FileVideo
	if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'].includes(type)) return FileAudio
	return File
})

const iconBgClass = computed(() => {
	const type = fileType.value
	if (type === 'link') return 'bg-blue-50'
	if (type === 'pdf') return 'bg-red-50'
	if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tiff', 'tif'].includes(type))
		return 'bg-purple-50'
	if (['xls', 'xlsx', 'csv', 'ods'].includes(type)) return 'bg-green-50'
	if (['doc', 'docx', 'odt', 'rtf'].includes(type)) return 'bg-blue-50'
	if (['ppt', 'pptx', 'odp'].includes(type)) return 'bg-orange-50'
	if (['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv', 'flv', 'm4v', '3gp'].includes(type)) return 'bg-pink-50'
	if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'].includes(type)) return 'bg-cyan-50'
	if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'tgz'].includes(type)) return 'bg-yellow-50'
	if (['js', 'ts', 'py', 'html', 'css', 'json', 'xml', 'php', 'java', 'c', 'cpp', 'h', 'rb', 'go', 'rs', 'swift', 'kt', 'sh', 'bash', 'sql', 'yml', 'yaml', 'md', 'vue', 'jsx', 'tsx'].includes(type)) return 'bg-indigo-50'
	return 'bg-gray-50'
})

const iconColorClass = computed(() => {
	const type = fileType.value
	if (type === 'link') return 'text-blue-500'
	if (type === 'pdf') return 'text-red-500'
	if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tiff', 'tif'].includes(type))
		return 'text-purple-500'
	if (['xls', 'xlsx', 'csv', 'ods'].includes(type)) return 'text-green-500'
	if (['doc', 'docx', 'odt', 'rtf'].includes(type)) return 'text-blue-500'
	if (['ppt', 'pptx', 'odp'].includes(type)) return 'text-orange-500'
	if (['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv', 'flv', 'm4v', '3gp'].includes(type)) return 'text-pink-500'
	if (['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'].includes(type)) return 'text-cyan-500'
	if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'tgz'].includes(type)) return 'text-yellow-600'
	if (['js', 'ts', 'py', 'html', 'css', 'json', 'xml', 'php', 'java', 'c', 'cpp', 'h', 'rb', 'go', 'rs', 'swift', 'kt', 'sh', 'bash', 'sql', 'yml', 'yaml', 'md', 'vue', 'jsx', 'tsx'].includes(type)) return 'text-indigo-500'
	return 'text-gray-500'
})

const canPreview = computed(() => {
	const type = fileType.value
	// PDF and images
	if (type === 'pdf' || ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(type)) return true
	// Video files
	if (['mp4', 'webm', 'ogg'].includes(type)) return true
	// Audio files
	if (['mp3', 'wav', 'ogg', 'aac', 'm4a'].includes(type)) return true
	return false
})

const canDelete = computed(() => {
	if (!user.data) return false
	return (
		props.document.owner === user.data.name ||
		user.data.is_moderator ||
		user.data.is_system_manager
	)
})

const strippedDescription = computed(() => {
	if (!props.document.description) return ''
	const div = window.document.createElement('div')
	div.innerHTML = props.document.description
	return div.textContent || div.innerText || ''
})
</script>

<style scoped>
.line-clamp-2 {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}
</style>
