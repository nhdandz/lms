<template>
	<Dialog
		v-model="show"
		:options="{
			title: existingSubmission ? __('Update Your Score') : __('Submit Your Score'),
			size: 'lg'
		}"
	>
		<template #body-content>
			<div class="space-y-4">
				<!-- Contest info -->
				<div v-if="folder?.external_contest_url" class="p-3 bg-blue-50 rounded-lg">
					<p class="text-sm text-blue-800">
						<a
							:href="folder.external_contest_url"
							target="_blank"
							class="flex items-center gap-1 hover:underline font-medium"
						>
							<ExternalLink class="w-4 h-4" />
							{{ __('View Contest Details') }}
						</a>
					</p>
				</div>

				<!-- Score input -->
				<div class="grid grid-cols-2 gap-4">
					<FormControl
						v-if="folder?.ranking_type !== 'Rank'"
						v-model="form.score"
						type="number"
						:label="__('Score')"
						:placeholder="folder?.max_score ? `Max: ${folder.max_score}` : __('Enter your score')"
						required
					/>
					<FormControl
						v-if="folder?.ranking_type === 'Rank' || folder?.ranking_type === 'Score'"
						v-model="form.rank"
						type="number"
						:label="__('Rank')"
						:placeholder="__('Your contest rank')"
						:required="folder?.ranking_type === 'Rank'"
					/>
				</div>

				<!-- External username -->
				<FormControl
					v-if="folder?.external_contest_url"
					v-model="form.external_username"
					type="text"
					:label="__('External Username')"
					:placeholder="__('Your username on the contest platform')"
				/>

				<!-- Proof URL -->
				<FormControl
					v-model="form.proof_url"
					type="text"
					:label="__('Proof URL')"
					:placeholder="__('Link to your submission or profile')"
				/>

				<!-- Proof Screenshot -->
				<div>
					<label class="block text-sm font-medium text-ink-gray-7 mb-1">
						{{ __('Proof Screenshot') }}
					</label>
					<div
						class="border-2 border-dashed border-surface-gray-3 rounded-lg p-4 text-center cursor-pointer hover:border-surface-gray-4 transition-colors"
						@click="triggerFileInput"
						@dragover.prevent
						@drop.prevent="handleDrop"
					>
						<input
							ref="fileInput"
							type="file"
							accept="image/*"
							class="hidden"
							@change="handleFileSelect"
						/>
						<div v-if="previewUrl" class="relative">
							<img :src="previewUrl" class="max-h-48 mx-auto rounded" />
							<Button
								variant="ghost"
								size="sm"
								class="absolute top-2 right-2"
								@click.stop="clearFile"
							>
								<X class="w-4 h-4" />
							</Button>
						</div>
						<div v-else class="text-ink-gray-5">
							<Upload class="w-8 h-8 mx-auto mb-2" />
							<p class="text-sm">{{ __('Click or drag to upload screenshot') }}</p>
						</div>
					</div>
				</div>

				<!-- Status info for existing submission -->
				<div
					v-if="existingSubmission"
					class="p-3 rounded-lg"
					:class="{
						'bg-green-50': existingSubmission.status === 'Approved',
						'bg-yellow-50': existingSubmission.status === 'Pending',
						'bg-red-50': existingSubmission.status === 'Rejected',
					}"
				>
					<p class="text-sm">
						<span class="font-medium">{{ __('Current Status') }}:</span>
						{{ existingSubmission.status }}
						<span v-if="folder?.require_approval && existingSubmission.status === 'Approved'">
							({{ __('Will be reset to Pending after update') }})
						</span>
					</p>
				</div>
			</div>
		</template>
		<template #actions>
			<Button variant="ghost" @click="show = false">
				{{ __('Cancel') }}
			</Button>
			<Button
				variant="solid"
				:loading="submitting"
				@click="submit"
			>
				{{ existingSubmission ? __('Update') : __('Submit') }}
			</Button>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Dialog, FormControl, Button, call, toast } from 'frappe-ui'
import { ExternalLink, Upload, X } from 'lucide-vue-next'

const props = defineProps({
	modelValue: {
		type: Boolean,
		default: false
	},
	category: {
		type: String,
		required: true
	},
	folder: {
		type: Object,
		default: null
	},
	existingSubmission: {
		type: Object,
		default: null
	}
})

const emit = defineEmits(['update:modelValue', 'submitted'])

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val)
})

const form = reactive({
	score: null,
	rank: null,
	external_username: '',
	proof_url: '',
})

const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref(null)
const submitting = ref(false)

// Initialize form with existing data
onMounted(() => {
	if (props.existingSubmission) {
		form.score = props.existingSubmission.score
		form.rank = props.existingSubmission.rank
		form.external_username = props.existingSubmission.external_username || ''
		form.proof_url = props.existingSubmission.proof_url || ''
		if (props.existingSubmission.proof_screenshot) {
			previewUrl.value = props.existingSubmission.proof_screenshot
		}
	}
})

function triggerFileInput() {
	fileInput.value?.click()
}

function handleFileSelect(event) {
	const file = event.target.files[0]
	if (file) {
		processFile(file)
	}
}

function handleDrop(event) {
	const file = event.dataTransfer.files[0]
	if (file && file.type.startsWith('image/')) {
		processFile(file)
	}
}

function processFile(file) {
	selectedFile.value = file
	const reader = new FileReader()
	reader.onload = (e) => {
		previewUrl.value = e.target.result
	}
	reader.readAsDataURL(file)
}

function clearFile() {
	selectedFile.value = null
	previewUrl.value = props.existingSubmission?.proof_screenshot || null
	if (fileInput.value) {
		fileInput.value.value = ''
	}
}

async function submit() {
	// Validation
	if (props.folder?.ranking_type === 'Rank' && !form.rank) {
		toast.error(__('Please enter your rank'))
		return
	}
	if (props.folder?.ranking_type !== 'Rank' && !form.score) {
		toast.error(__('Please enter your score'))
		return
	}

	submitting.value = true

	try {
		// Upload file if selected
		let proofScreenshot = props.existingSubmission?.proof_screenshot || null
		if (selectedFile.value) {
			const formData = new FormData()
			formData.append('file', selectedFile.value)
			formData.append('is_private', 0)
			formData.append('folder', 'Home/Ranking Proofs')

			const uploadResponse = await fetch('/api/method/upload_file', {
				method: 'POST',
				body: formData,
				headers: {
					'X-Frappe-CSRF-Token': window.csrf_token
				}
			})

			const uploadResult = await uploadResponse.json()
			if (uploadResult.message?.file_url) {
				proofScreenshot = uploadResult.message.file_url
			}
		}

		// Submit score
		await call('lms.lms.api.submit_ranking_score', {
			category: props.category,
			score: form.score || 0,
			rank: form.rank || null,
			external_username: form.external_username || null,
			proof_url: form.proof_url || null,
			proof_screenshot: proofScreenshot,
		})

		toast.success(props.existingSubmission ? __('Score updated successfully') : __('Score submitted successfully'))
		emit('submitted')
	} catch (error) {
		toast.error(error.messages?.[0] || __('Failed to submit score'))
	} finally {
		submitting.value = false
	}
}
</script>
