<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Submission Evidence'),
			size: 'lg'
		}"
	>
		<template #body-content>
			<div v-if="submission" class="space-y-4">
				<!-- Member info -->
				<div class="flex items-center gap-3">
					<img
						v-if="submission.member_image"
						:src="submission.member_image"
						class="w-10 h-10 rounded-full object-cover"
					/>
					<div
						v-else
						class="w-10 h-10 rounded-full bg-surface-gray-2 flex items-center justify-center"
					>
						<User class="w-5 h-5 text-ink-gray-5" />
					</div>
					<div>
						<p class="font-medium text-ink-gray-9">{{ submission.member_name }}</p>
						<p class="text-sm text-ink-gray-5">
							{{ __('Score') }}: <span class="font-semibold">{{ submission.score }}</span>
							<span v-if="submission.rank"> &middot; {{ __('Rank') }}: <span class="font-semibold">#{{ submission.rank }}</span></span>
						</p>
					</div>
				</div>

				<!-- No evidence message -->
				<div
					v-if="!submission.proof_url && !submission.proof_screenshot"
					class="py-6 text-center text-ink-gray-5"
				>
					{{ __('No evidence provided for this submission.') }}
				</div>

				<!-- Proof URL -->
				<div v-if="submission.proof_url">
					<p class="text-sm font-medium text-ink-gray-7 mb-1">{{ __('Proof Link') }}</p>
					<a
						:href="submission.proof_url"
						target="_blank"
						class="inline-flex items-center gap-1 text-blue-600 hover:underline text-sm"
					>
						<ExternalLink class="w-4 h-4" />
						{{ submission.proof_url }}
					</a>
				</div>

				<!-- Proof Screenshot -->
				<div v-if="submission.proof_screenshot">
					<p class="text-sm font-medium text-ink-gray-7 mb-2">{{ __('Proof Screenshot') }}</p>
					<img
						:src="submission.proof_screenshot"
						class="w-full rounded-lg border"
					/>
				</div>
			</div>
		</template>
		<template #actions>
			<Button variant="ghost" @click="show = false">
				{{ __('Close') }}
			</Button>
		</template>
	</Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { Dialog, Button } from 'frappe-ui'
import { User, ExternalLink } from 'lucide-vue-next'

const props = defineProps({
	modelValue: {
		type: Boolean,
		default: false
	},
	submission: {
		type: Object,
		default: null
	}
})

const emit = defineEmits(['update:modelValue'])

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val)
})
</script>
