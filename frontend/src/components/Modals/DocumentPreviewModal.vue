<template>
	<Dialog
		v-model="show"
		:options="{
			title: docData?.title || __('Document Preview'),
			size: '4xl',
		}"
	>
		<template #body-content>
			<div class="min-h-[60vh]">
				<div v-if="isPDF" class="h-[70vh]">
					<iframe
						:src="docData?.file"
						class="w-full h-full border-0 rounded-lg"
						:title="docData?.title"
					/>
				</div>

				<div
					v-else-if="isImage"
					class="flex items-center justify-center h-[70vh] bg-gray-50 rounded-lg"
				>
					<img
						:src="docData?.file"
						:alt="docData?.title"
						class="max-w-full max-h-full object-contain"
					/>
				</div>

				<div
					v-else-if="isVideo"
					class="flex items-center justify-center h-[70vh] bg-gray-900 rounded-lg"
				>
					<video
						:src="docData?.file"
						controls
						class="max-w-full max-h-full"
						:title="docData?.title"
					>
						{{ __('Your browser does not support the video tag.') }}
					</video>
				</div>

				<div
					v-else-if="isAudio"
					class="flex flex-col items-center justify-center h-[40vh] bg-gray-50 rounded-lg"
				>
					<FileAudio class="w-24 h-24 text-cyan-500 mb-6" />
					<p class="text-lg font-medium text-ink-gray-7 mb-4">
						{{ docData?.title }}
					</p>
					<audio
						:src="docData?.file"
						controls
						class="w-full max-w-md"
						:title="docData?.title"
					>
						{{ __('Your browser does not support the audio tag.') }}
					</audio>
				</div>

				<div
					v-else
					class="flex flex-col items-center justify-center h-[60vh] text-center"
				>
					<FileQuestion class="w-16 h-16 text-ink-gray-4 mb-4" />
					<p class="text-lg font-medium text-ink-gray-7 mb-2">
						{{ __('Preview not available') }}
					</p>
					<p class="text-sm text-ink-gray-5 mb-4">
						{{
							__(
								'This file type cannot be previewed. Please download to view.'
							)
						}}
					</p>
					<Button variant="solid" @click="downloadFile">
						<template #prefix>
							<Download class="w-4 h-4" />
						</template>
						{{ __('Download File') }}
					</Button>
				</div>
			</div>

			<div
				v-if="docData"
				class="mt-4 pt-4 border-t flex items-center justify-between"
			>
				<div class="flex items-center space-x-4 text-sm text-ink-gray-5">
					<span class="flex items-center space-x-1">
						<Eye class="w-4 h-4" />
						<span>{{ docData.view_count || 0 }} {{ __('views') }}</span>
					</span>
					<span class="flex items-center space-x-1">
						<Download class="w-4 h-4" />
						<span
							>{{ docData.download_count || 0 }}
							{{ __('downloads') }}</span
						>
					</span>
					<span v-if="docData.file_type">
						{{ docData.file_type }}
						{{ docData.file_size ? `- ${docData.file_size}` : '' }}
					</span>
				</div>

				<Button variant="subtle" @click="downloadFile">
					<template #prefix>
						<Download class="w-4 h-4" />
					</template>
					{{ __('Download') }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, toRef } from 'vue'
import { Button, Dialog, createResource, toast } from 'frappe-ui'
import { Download, Eye, FileQuestion, FileAudio } from 'lucide-vue-next'

const show = defineModel()

const props = defineProps({
	document: {
		type: Object,
		default: null,
	},
})

const docData = toRef(props, 'document')

const fileType = computed(() => {
	return (docData.value?.file_type || '').toLowerCase()
})

const isPDF = computed(() => {
	return fileType.value === 'pdf'
})

const isImage = computed(() => {
	return ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(fileType.value)
})

const isVideo = computed(() => {
	return ['mp4', 'webm', 'ogg'].includes(fileType.value)
})

const isAudio = computed(() => {
	return ['mp3', 'wav', 'ogg', 'aac', 'm4a'].includes(fileType.value)
})

const downloadFile = async () => {
	if (!docData.value) return

	try {
		const response = await createResource({
			url: 'lms.lms.api.track_document_download',
			params: { document_name: docData.value.name },
		}).fetch()

		if (response.file_url) {
			const link = window.document.createElement('a')
			link.href = response.file_url
			link.download = docData.value.title
			link.target = '_blank'
			window.document.body.appendChild(link)
			link.click()
			window.document.body.removeChild(link)
		}
	} catch (error) {
		toast.error(__('Failed to download document'))
	}
}
</script>
