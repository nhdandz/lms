<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Pending Submissions'),
			size: 'xl'
		}"
	>
		<template #body-content>
			<div v-if="loading" class="py-8 text-center">
				<Spinner class="w-8 h-8 mx-auto text-ink-gray-5" />
			</div>

			<div v-else-if="submissions.length === 0" class="py-8 text-center text-ink-gray-5">
				{{ __('No pending submissions') }}
			</div>

			<div v-else class="space-y-4 max-h-[60vh] overflow-y-auto">
				<div
					v-for="submission in submissions"
					:key="submission.name"
					class="border rounded-lg p-4"
				>
					<div class="flex items-start justify-between gap-4">
						<div class="flex-1">
							<div class="flex items-center gap-3 mb-2">
								<div class="w-10 h-10 rounded-full bg-surface-gray-2 flex items-center justify-center">
									<User class="w-5 h-5 text-ink-gray-5" />
								</div>
								<div>
									<p class="font-medium text-ink-gray-9">
										{{ submission.member_name }}
									</p>
									<p class="text-sm text-ink-gray-5">
										{{ submission.category_name }}
									</p>
								</div>
							</div>

							<div class="grid grid-cols-3 gap-4 text-sm mb-3">
								<div>
									<span class="text-ink-gray-5">{{ __('Score') }}:</span>
									<span class="font-medium ml-1">{{ submission.score }}</span>
								</div>
								<div v-if="submission.rank">
									<span class="text-ink-gray-5">{{ __('Rank') }}:</span>
									<span class="font-medium ml-1">#{{ submission.rank }}</span>
								</div>
								<div v-if="submission.external_username">
									<span class="text-ink-gray-5">{{ __('Username') }}:</span>
									<span class="font-medium ml-1">{{ submission.external_username }}</span>
								</div>
							</div>

							<!-- Proof links -->
							<div class="flex items-center gap-4 text-sm">
								<a
									v-if="submission.proof_url"
									:href="submission.proof_url"
									target="_blank"
									class="text-blue-600 hover:underline flex items-center gap-1"
								>
									<ExternalLink class="w-3 h-3" />
									{{ __('View Proof') }}
								</a>
								<button
									v-if="submission.proof_screenshot"
									class="text-blue-600 hover:underline flex items-center gap-1"
									@click="viewScreenshot(submission.proof_screenshot)"
								>
									<ImageIcon class="w-3 h-3" />
									{{ __('View Screenshot') }}
								</button>
							</div>
						</div>

						<!-- Actions -->
						<div class="flex items-center gap-2">
							<Button
								variant="solid"
								theme="green"
								size="sm"
								:loading="approvingId === submission.name"
								@click="approve(submission.name, 'Approved')"
							>
								<Check class="w-4 h-4" />
							</Button>
							<Button
								variant="subtle"
								theme="red"
								size="sm"
								:loading="rejectingId === submission.name"
								@click="showRejectDialog(submission)"
							>
								<X class="w-4 h-4" />
							</Button>
						</div>
					</div>
				</div>
			</div>
		</template>
		<template #actions>
			<Button variant="ghost" @click="show = false">
				{{ __('Close') }}
			</Button>
		</template>
	</Dialog>

	<!-- Screenshot preview modal -->
	<Dialog
		v-model="showScreenshotModal"
		:options="{ title: __('Proof Screenshot'), size: 'lg' }"
	>
		<template #body-content>
			<img
				v-if="screenshotUrl"
				:src="screenshotUrl"
				class="w-full rounded"
			/>
		</template>
	</Dialog>

	<!-- Reject confirmation dialog -->
	<Dialog
		v-model="showRejectModal"
		:options="{ title: __('Reject Submission'), size: 'md' }"
	>
		<template #body-content>
			<FormControl
				v-model="rejectRemarks"
				type="textarea"
				:label="__('Reason for rejection')"
				:placeholder="__('Optional: Explain why this submission is being rejected')"
				:rows="3"
			/>
		</template>
		<template #actions>
			<Button variant="ghost" @click="showRejectModal = false">
				{{ __('Cancel') }}
			</Button>
			<Button
				variant="solid"
				theme="red"
				:loading="rejectingId !== null"
				@click="confirmReject"
			>
				{{ __('Reject') }}
			</Button>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Dialog, FormControl, Button, Spinner, call, toast } from 'frappe-ui'
import { User, ExternalLink, Image as ImageIcon, Check, X } from 'lucide-vue-next'

const props = defineProps({
	modelValue: {
		type: Boolean,
		default: false
	},
	category: {
		type: String,
		default: null
	}
})

const emit = defineEmits(['update:modelValue', 'approved'])

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const submissions = ref([])
const approvingId = ref(null)
const rejectingId = ref(null)

const showScreenshotModal = ref(false)
const screenshotUrl = ref(null)

const showRejectModal = ref(false)
const rejectRemarks = ref('')
const submissionToReject = ref(null)

onMounted(() => {
	loadSubmissions()
})

watch(() => props.modelValue, (val) => {
	if (val) {
		loadSubmissions()
	}
})

async function loadSubmissions() {
	loading.value = true
	try {
		const result = await call('lms.lms.api.get_pending_submissions', {
			category: props.category
		})
		submissions.value = result || []
	} catch (error) {
		toast.error(__('Failed to load submissions'))
	} finally {
		loading.value = false
	}
}

async function approve(submissionName, status) {
	approvingId.value = submissionName
	try {
		await call('lms.lms.api.approve_ranking_submission', {
			submission_name: submissionName,
			status: status
		})
		toast.success(__('Submission approved'))
		submissions.value = submissions.value.filter(s => s.name !== submissionName)
		emit('approved')
	} catch (error) {
		toast.error(error.messages?.[0] || __('Failed to approve'))
	} finally {
		approvingId.value = null
	}
}

function showRejectDialog(submission) {
	submissionToReject.value = submission
	rejectRemarks.value = ''
	showRejectModal.value = true
}

async function confirmReject() {
	if (!submissionToReject.value) return

	rejectingId.value = submissionToReject.value.name
	try {
		await call('lms.lms.api.approve_ranking_submission', {
			submission_name: submissionToReject.value.name,
			status: 'Rejected',
			remarks: rejectRemarks.value || null
		})
		toast.success(__('Submission rejected'))
		submissions.value = submissions.value.filter(s => s.name !== submissionToReject.value.name)
		showRejectModal.value = false
		emit('approved')
	} catch (error) {
		toast.error(error.messages?.[0] || __('Failed to reject'))
	} finally {
		rejectingId.value = null
		submissionToReject.value = null
	}
}

function viewScreenshot(url) {
	screenshotUrl.value = url
	showScreenshotModal.value = true
}
</script>
