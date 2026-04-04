<template>
	<div class="folder-leaderboard">
		<!-- Contest Info Panel -->
		<ContestInfoPanel
			v-if="folder?.is_ranking_enabled"
			:folder="folder"
			class="mb-6"
		/>

		<!-- Header -->
		<div class="flex items-center justify-between mb-4">
			<div class="flex items-center gap-3">
				<Trophy class="w-6 h-6 text-yellow-500" />
				<div>
					<h3 class="text-lg font-semibold text-ink-gray-9">
						{{ __('Leaderboard') }}
					</h3>
				</div>
			</div>

			<div class="flex items-center gap-2">
				<!-- Pending submissions badge for moderators -->
				<Badge
					v-if="isModerator && pendingCount > 0"
					:label="`${pendingCount} pending`"
					variant="subtle"
					theme="orange"
					class="cursor-pointer"
					@click="showPendingModal = true"
				/>

				<!-- Submit score button -->
				<Button
					v-if="canSubmit"
					variant="solid"
					@click="showSubmitModal = true"
				>
					<template #prefix>
						<Plus class="w-4 h-4" />
					</template>
					{{ mySubmission ? __('Update Score') : __('Submit Score') }}
				</Button>
			</div>
		</div>

		<!-- My submission status -->
		<div
			v-if="mySubmission"
			class="mb-4 p-3 rounded-lg border"
			:class="{
				'bg-green-50 border-green-200': mySubmission.status === 'Approved',
				'bg-yellow-50 border-yellow-200': mySubmission.status === 'Pending',
				'bg-red-50 border-red-200': mySubmission.status === 'Rejected',
			}"
		>
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<div
						class="w-8 h-8 rounded-full flex items-center justify-center"
						:class="{
							'bg-green-100': mySubmission.status === 'Approved',
							'bg-yellow-100': mySubmission.status === 'Pending',
							'bg-red-100': mySubmission.status === 'Rejected',
						}"
					>
						<Check v-if="mySubmission.status === 'Approved'" class="w-4 h-4 text-green-600" />
						<Clock v-else-if="mySubmission.status === 'Pending'" class="w-4 h-4 text-yellow-600" />
						<X v-else class="w-4 h-4 text-red-600" />
					</div>
					<div>
						<p class="text-sm font-medium text-ink-gray-9">
							{{ __('Your Submission') }}:
							<span class="font-bold">
								{{ folder?.ranking_type === 'Rank' ? `#${mySubmission.rank}` : mySubmission.score }}
							</span>
						</p>
						<p class="text-xs text-ink-gray-5">
							{{ mySubmission.status }}
							<span v-if="mySubmission.remarks"> - {{ mySubmission.remarks }}</span>
						</p>
					</div>
				</div>
				<Button
					variant="ghost"
					size="sm"
					@click="showSubmitModal = true"
				>
					{{ __('Edit') }}
				</Button>
			</div>
		</div>

		<!-- Leaderboard table -->
		<div class="border rounded-lg overflow-hidden">
			<table class="w-full">
				<thead class="bg-surface-gray-2">
					<tr>
						<th class="px-4 py-3 text-left text-xs font-medium text-ink-gray-5 uppercase tracking-wider w-16">
							#
						</th>
						<th class="px-4 py-3 text-left text-xs font-medium text-ink-gray-5 uppercase tracking-wider">
							{{ __('Member') }}
						</th>
						<th v-if="folder?.ranking_type === 'Rank'" class="px-4 py-3 text-center text-xs font-medium text-ink-gray-5 uppercase tracking-wider w-24">
							{{ __('Rank') }}
						</th>
						<th class="px-4 py-3 text-center text-xs font-medium text-ink-gray-5 uppercase tracking-wider w-24">
							{{ __('Score') }}
						</th>
						<th v-if="folder?.external_contest_url" class="px-4 py-3 text-left text-xs font-medium text-ink-gray-5 uppercase tracking-wider w-32">
							{{ __('Username') }}
						</th>
						<th class="px-4 py-3 text-right text-xs font-medium text-ink-gray-5 uppercase tracking-wider w-32">
							{{ __('Date') }}
						</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-surface-gray-2">
					<tr
						v-for="(submission, index) in submissions"
						:key="submission.name"
						class="hover:bg-surface-gray-1 transition-colors cursor-pointer"
						:class="{ 'bg-yellow-50': submission.member === currentUser }"
						@click="openProof(submission)"
					>
						<td class="px-4 py-3">
							<div
								class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
								:class="getPositionClass(submission.position)"
							>
								{{ submission.position }}
							</div>
						</td>
						<td class="px-4 py-3">
							<div class="flex items-center gap-3">
								<img
									v-if="submission.member_image"
									:src="submission.member_image"
									class="w-8 h-8 rounded-full object-cover"
								/>
								<div
									v-else
									class="w-8 h-8 rounded-full bg-surface-gray-3 flex items-center justify-center"
								>
									<User class="w-4 h-4 text-ink-gray-5" />
								</div>
								<div>
									<p class="text-sm font-medium text-ink-gray-9">
										{{ submission.member_name }}
									</p>
								</div>
							</div>
						</td>
						<td v-if="folder?.ranking_type === 'Rank'" class="px-4 py-3 text-center">
							<span class="text-sm font-semibold text-ink-gray-9">
								#{{ submission.rank || '-' }}
							</span>
						</td>
						<td class="px-4 py-3 text-center">
							<span class="text-sm font-semibold text-ink-gray-9">
								{{ submission.score }}
							</span>
							<span v-if="submission.max_score" class="text-xs text-ink-gray-5">
								/{{ submission.max_score }}
							</span>
						</td>
						<td v-if="folder?.external_contest_url" class="px-4 py-3">
							<span class="text-sm text-ink-gray-7">
								{{ submission.external_username || '-' }}
							</span>
						</td>
						<td class="px-4 py-3 text-right text-sm text-ink-gray-5">
							{{ formatDate(submission.submission_date) }}
						</td>
					</tr>
					<tr v-if="submissions.length === 0">
						<td :colspan="folder?.external_contest_url ? 6 : 5" class="px-4 py-8 text-center text-ink-gray-5">
							{{ __('No submissions yet. Be the first to submit!') }}
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- Total count -->
		<p v-if="totalCount > submissions.length" class="mt-2 text-sm text-ink-gray-5 text-center">
			{{ __('Showing {0} of {1} submissions').replace('{0}', submissions.length).replace('{1}', totalCount) }}
		</p>

		<!-- Submit Modal -->
		<RankingSubmissionModal
			v-if="showSubmitModal"
			v-model="showSubmitModal"
			:category="category"
			:folder="folder"
			:existing-submission="mySubmission"
			@submitted="onSubmitted"
		/>

		<!-- Pending Approval Modal -->
		<RankingApprovalModal
			v-if="showPendingModal"
			v-model="showPendingModal"
			:category="category"
			@approved="onApproved"
		/>

		<!-- Proof Viewing Modal -->
		<RankingProofModal
			v-if="showProofModal"
			v-model="showProofModal"
			:submission="selectedProofSubmission"
		/>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { createResource, Button, Badge } from 'frappe-ui'
import { Trophy, Plus, User, Check, Clock, X } from 'lucide-vue-next'
import { usersStore } from '@/stores/user'
import RankingSubmissionModal from './Modals/RankingSubmissionModal.vue'
import RankingApprovalModal from './Modals/RankingApprovalModal.vue'
import RankingProofModal from './Modals/RankingProofModal.vue'
import ContestInfoPanel from './ContestInfoPanel.vue'
import dayjs from '@/utils/dayjs'

const props = defineProps({
	category: {
		type: String,
		required: true
	},
	folder: {
		type: Object,
		default: null
	}
})

const emit = defineEmits(['refresh'])

const { userResource } = usersStore()
const currentUser = computed(() => userResource.data?.name)
const isModerator = computed(() =>
	userResource.data?.is_moderator || userResource.data?.is_system_manager
)

const showSubmitModal = ref(false)
const showPendingModal = ref(false)
const showProofModal = ref(false)
const selectedProofSubmission = ref(null)

// Leaderboard data
const leaderboardResource = createResource({
	url: 'lms.lms.api.get_folder_leaderboard',
	makeParams: () => ({
		category: props.category,
		limit: 50
	})
})

const submissions = computed(() => leaderboardResource.data?.submissions || [])
const totalCount = computed(() => leaderboardResource.data?.total_count || 0)

// My submission
const mySubmissionResource = createResource({
	url: 'lms.lms.api.get_my_ranking_submission',
	makeParams: () => ({
		category: props.category
	})
})

const mySubmission = computed(() => mySubmissionResource.data)

// Pending submissions count (for moderators)
const pendingResource = createResource({
	url: 'lms.lms.api.get_pending_submissions',
	makeParams: () => ({
		category: props.category
	})
})

const pendingCount = computed(() => pendingResource.data?.length || 0)

// Can submit check
const canSubmit = computed(() => {
	if (!userResource.data) return false
	if (!props.folder?.allow_self_submission) return false
	return true
})

// Load data
onMounted(() => {
	loadData()
})

watch(() => props.category, () => {
	loadData()
})

function loadData() {
	leaderboardResource.reload()
	if (userResource.data) {
		mySubmissionResource.reload()
		if (isModerator.value) {
			pendingResource.reload()
		}
	}
}

function onSubmitted() {
	showSubmitModal.value = false
	loadData()
	emit('refresh')
}

function onApproved() {
	loadData()
	emit('refresh')
}

function openProof(submission) {
	selectedProofSubmission.value = submission
	showProofModal.value = true
}

function getPositionClass(position) {
	if (position === 1) return 'bg-yellow-100 text-yellow-700'
	if (position === 2) return 'bg-gray-100 text-gray-700'
	if (position === 3) return 'bg-orange-100 text-orange-700'
	return 'bg-surface-gray-2 text-ink-gray-7'
}

function formatDate(date) {
	if (!date) return '-'
	return dayjs(date).format('MMM D, YYYY')
}
</script>
