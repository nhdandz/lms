<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Upload Document'),
			size: 'lg',
			actions: [
				{
					label: __('Upload'),
					variant: 'solid',
					onClick: (close) => uploadDocument(close),
					loading: uploading,
				},
			],
		}"
	>
		<template #body-content>
			<div class="space-y-4 text-base">
				<FormControl
					:label="__('Title')"
					v-model="form.title"
					:required="true"
					:placeholder="__('Document title')"
				/>

				<div>
					<label class="block text-xs text-ink-gray-5 mb-1.5">
						{{ __('Category') }}
					</label>
					<Link
						doctype="LMS Document Category"
						v-model="form.category"
						:placeholder="__('Select category')"
					/>
				</div>

				<div>
					<label class="block text-xs text-ink-gray-5 mb-1.5">
						{{ __('File') }} <span class="text-red-500">*</span>
					</label>
					<FileUploader
						v-if="!form.file"
						:fileTypes="allowedFileTypes"
						@success="(file) => onFileUpload(file)"
					>
						<template
							v-slot="{ file, progress, uploading, openFileSelector }"
						>
							<div
								class="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center cursor-pointer hover:border-gray-300 transition-colors"
								@click="openFileSelector"
							>
								<Upload
									class="w-8 h-8 text-ink-gray-4 mx-auto mb-2"
								/>
								<p class="text-sm text-ink-gray-6">
									{{
										uploading
											? __('Uploading {0}%').replace(
													'{0}',
													progress
												)
											: __('Click to upload or drag and drop')
									}}
								</p>
								<p class="text-xs text-ink-gray-4 mt-1">
									{{ __('All file types supported, up to 50MB') }}
								</p>
							</div>
						</template>
					</FileUploader>
					<div
						v-else
						class="flex items-center justify-between border rounded-lg p-3"
					>
						<div class="flex items-center space-x-3">
							<div
								class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center"
							>
								<FileText class="w-5 h-5 text-ink-gray-6" />
							</div>
							<div>
								<p class="text-sm font-medium text-ink-gray-9">
									{{ form.file.file_name }}
								</p>
								<p class="text-xs text-ink-gray-5">
									{{ getFileSize(form.file.file_size) }}
								</p>
							</div>
						</div>
						<Button
							variant="ghost"
							size="sm"
							@click="form.file = null"
						>
							<X class="w-4 h-4" />
						</Button>
					</div>
				</div>

				<div>
					<label class="block text-xs text-ink-gray-5 mb-1.5">
						{{ __('Description') }}
					</label>
					<FormControl
						type="textarea"
						v-model="form.description"
						:placeholder="__('Optional description')"
						:rows="3"
					/>
				</div>

				<FormControl
					type="select"
					:label="__('Access Level')"
					v-model="form.access_level"
					:options="accessLevelOptions"
				/>

				<div class="flex items-center space-x-2">
					<input
						type="checkbox"
						id="published"
						v-model="form.published"
						class="rounded border-gray-300"
					/>
					<label for="published" class="text-sm text-ink-gray-7">
						{{ __('Publish immediately') }}
					</label>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import {
	Button,
	Dialog,
	FileUploader,
	FormControl,
	createResource,
	toast,
} from 'frappe-ui'
import { reactive, ref, computed } from 'vue'
import { FileText, Upload, X } from 'lucide-vue-next'
import { getFileSize } from '@/utils/'
import Link from '@/components/Controls/Link.vue'

const show = defineModel()
const emit = defineEmits(['success'])

const uploading = ref(false)

const form = reactive({
	title: '',
	category: '',
	file: null,
	description: '',
	access_level: 'Public',
	published: true,
})

// Allow all file types - no restriction
const allowedFileTypes = ['*']

const accessLevelOptions = computed(() => [
	{ label: __('Public'), value: 'Public' },
	{ label: __('Logged In Users'), value: 'Logged In' },
	{ label: __('Moderators Only'), value: 'Moderators Only' },
	{ label: __('Course Creators Only'), value: 'Course Creators Only' },
])

const onFileUpload = (file) => {
	form.file = file
	if (!form.title && file.file_name) {
		form.title = file.file_name.replace(/\.[^/.]+$/, '')
	}
}

const documentResource = createResource({
	url: 'frappe.client.insert',
	makeParams() {
		return {
			doc: {
				doctype: 'LMS Document',
				title: form.title,
				category: form.category || null,
				file: form.file?.file_url,
				description: form.description,
				access_level: form.access_level,
				published: form.published ? 1 : 0,
			},
		}
	},
})

const uploadDocument = async (close) => {
	if (!form.title) {
		toast.error(__('Title is required'))
		return
	}

	if (!form.file) {
		toast.error(__('Please upload a file'))
		return
	}

	uploading.value = true

	try {
		await documentResource.submit()
		resetForm()
		emit('success')
		close()
	} catch (error) {
		toast.error(error.messages?.[0] || __('Failed to upload document'))
	} finally {
		uploading.value = false
	}
}

const resetForm = () => {
	form.title = ''
	form.category = ''
	form.file = null
	form.description = ''
	form.access_level = 'Public'
	form.published = true
}
</script>
