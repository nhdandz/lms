<template>
	<div v-if="folder?.is_ranking_enabled" class="contest-info-panel rounded-xl border bg-surface-white shadow-sm overflow-hidden">
		<!-- Header -->
		<div class="px-5 py-4 border-b bg-gradient-to-r from-surface-gray-1 to-surface-white">
			<div class="flex flex-wrap items-start gap-3">
				<div class="flex-1 min-w-0">
					<div class="flex flex-wrap items-center gap-2 mb-1">
						<h2 class="text-base font-bold text-ink-gray-9 truncate">
							{{ folder.category_name }}
						</h2>
						<!-- Contest Type Badge -->
						<Badge
							v-if="folder.contest_type"
							:label="folder.contest_type"
							variant="subtle"
							:theme="contestTypeBadgeTheme"
						>
							<template #prefix>
								<component :is="contestTypeIcon" class="w-3 h-3" />
							</template>
						</Badge>
						<!-- Difficulty Badge -->
						<Badge
							v-if="folder.contest_difficulty"
							:label="folder.contest_difficulty"
							variant="outline"
							:theme="difficultyTheme"
						/>
					</div>

					<!-- Meta info row -->
					<div class="flex flex-wrap items-center gap-3 text-xs text-ink-gray-5">
						<span v-if="folder.organizer_name" class="flex items-center gap-1">
							<Users class="w-3 h-3" />
							{{ folder.organizer_name }}
						</span>
						<span v-if="folder.submission_deadline" class="flex items-center gap-1" :class="isDeadlineSoon ? 'text-red-500 font-medium' : ''">
							<Clock class="w-3 h-3" />
							{{ deadlineText }}
						</span>
						<span v-if="folder.contest_prize_info" class="flex items-center gap-1 text-yellow-600">
							<Gift class="w-3 h-3" />
							{{ folder.contest_prize_info }}
						</span>
						<a
							v-if="folder.external_contest_url"
							:href="folder.external_contest_url"
							target="_blank"
							class="flex items-center gap-1 text-blue-500 hover:underline"
						>
							<ExternalLink class="w-3 h-3" />
							{{ __('External Link') }}
						</a>
					</div>

					<!-- Tags -->
					<div v-if="parsedTags.length" class="flex flex-wrap gap-1 mt-2">
						<span
							v-for="tag in parsedTags"
							:key="tag"
							class="text-xs bg-surface-gray-2 text-ink-gray-6 px-2 py-0.5 rounded-full"
						>
							{{ tag }}
						</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Tabs -->
		<div class="border-b">
			<nav class="flex overflow-x-auto px-1" aria-label="Contest tabs">
				<button
					v-for="tab in visibleTabs"
					:key="tab.key"
					class="px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors"
					:class="
						activeTab === tab.key
							? 'border-blue-500 text-blue-600'
							: 'border-transparent text-ink-gray-5 hover:text-ink-gray-9 hover:border-ink-gray-3'
					"
					@click="activeTab = tab.key"
				>
					{{ tab.label }}
				</button>
			</nav>
		</div>

		<!-- Tab Content -->
		<div class="px-5 py-4">
			<!-- Overview Tab -->
			<div v-if="activeTab === 'overview'">
				<div
					v-if="folder.contest_description"
					class="prose prose-sm max-w-none text-ink-gray-8"
					v-html="renderMarkdown(folder.contest_description)"
				/>
				<p v-else class="text-sm text-ink-gray-4 italic">
					{{ __('Chưa có mô tả tổng quan.') }}
				</p>
			</div>

			<!-- Problem Tab -->
			<div v-if="activeTab === 'problem'">
				<div
					v-if="folder.contest_problem_statement"
					class="prose prose-sm max-w-none text-ink-gray-8"
					v-html="renderMarkdown(folder.contest_problem_statement)"
				/>
				<p v-else class="text-sm text-ink-gray-4 italic">
					{{ __('Chưa có mô tả bài toán.') }}
				</p>
			</div>

			<!-- Data Tab -->
			<div v-if="activeTab === 'data'">
				<div
					v-if="folder.contest_dataset_info"
					class="prose prose-sm max-w-none text-ink-gray-8"
					v-html="renderMarkdown(folder.contest_dataset_info)"
				/>
				<p v-else class="text-sm text-ink-gray-4 italic">
					{{ __('Chưa có thông tin dữ liệu.') }}
				</p>
			</div>

			<!-- Evaluation Tab -->
			<div v-if="activeTab === 'evaluation'" class="space-y-3">
				<div v-if="folder.contest_evaluation_metric">
					<p class="text-xs font-medium text-ink-gray-5 uppercase tracking-wide mb-1">
						{{ __('Metric đánh giá') }}
					</p>
					<Badge :label="folder.contest_evaluation_metric" variant="subtle" theme="blue" />
				</div>
				<div v-if="folder.contest_submission_format">
					<p class="text-xs font-medium text-ink-gray-5 uppercase tracking-wide mb-1">
						{{ __('Định dạng nộp bài') }}
					</p>
					<div
						class="prose prose-sm max-w-none text-ink-gray-8"
						v-html="renderMarkdown(folder.contest_submission_format)"
					/>
				</div>
				<p
					v-if="!folder.contest_evaluation_metric && !folder.contest_submission_format"
					class="text-sm text-ink-gray-4 italic"
				>
					{{ __('Chưa có thông tin đánh giá.') }}
				</p>
			</div>

			<!-- Rules Tab -->
			<div v-if="activeTab === 'rules'">
				<div
					v-if="folder.contest_rules"
					class="prose prose-sm max-w-none text-ink-gray-8"
					v-html="renderMarkdown(folder.contest_rules)"
				/>
				<p v-else class="text-sm text-ink-gray-4 italic">
					{{ __('Chưa có quy định.') }}
				</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Badge } from 'frappe-ui'
import {
	Users,
	Clock,
	Gift,
	ExternalLink,
	Medal,
	BarChart2,
	Code,
	Trophy,
	Activity,
} from 'lucide-vue-next'
import dayjs from '@/utils/dayjs'

const props = defineProps({
	folder: {
		type: Object,
		default: null,
	},
})

const activeTab = ref('overview')

const TABS = [
	{ key: 'overview', label: 'Overview' },
	{ key: 'problem', label: 'Bài toán' },
	{ key: 'data', label: 'Dữ liệu' },
	{ key: 'evaluation', label: 'Đánh giá' },
	{ key: 'rules', label: 'Quy định' },
]

const visibleTabs = computed(() => {
	return TABS.filter((tab) => {
		if (tab.key === 'overview') return true
		if (tab.key === 'problem') return !!props.folder?.contest_problem_statement
		if (tab.key === 'data') return !!props.folder?.contest_dataset_info
		if (tab.key === 'evaluation')
			return !!(props.folder?.contest_evaluation_metric || props.folder?.contest_submission_format)
		if (tab.key === 'rules') return !!props.folder?.contest_rules
		return false
	})
})

const contestTypeIcon = computed(() => {
	switch (props.folder?.contest_type) {
		case 'Olympic': return Medal
		case 'Club Activity': return Users
		case 'Data Challenge': return BarChart2
		case 'Competitive Programming': return Code
		case 'Algorithm Contest': return Activity
		default: return Trophy
	}
})

const contestTypeBadgeTheme = computed(() => {
	switch (props.folder?.contest_type) {
		case 'Olympic': return 'yellow'
		case 'Club Activity': return 'blue'
		case 'Data Challenge': return 'purple'
		case 'Competitive Programming': return 'green'
		case 'Algorithm Contest': return 'orange'
		default: return 'gray'
	}
})

const difficultyTheme = computed(() => {
	switch (props.folder?.contest_difficulty) {
		case 'Beginner': return 'green'
		case 'Intermediate': return 'blue'
		case 'Advanced': return 'orange'
		case 'Expert': return 'red'
		default: return 'gray'
	}
})

const parsedTags = computed(() => {
	const tags = props.folder?.contest_tags || ''
	return tags
		.split(',')
		.map((t) => t.trim())
		.filter(Boolean)
})

const deadlineText = computed(() => {
	if (!props.folder?.submission_deadline) return ''
	const d = dayjs(props.folder.submission_deadline)
	const now = dayjs()
	if (d.isBefore(now)) return `Đã hết hạn (${d.format('DD/MM/YYYY')})`
	const diff = d.diff(now, 'day')
	if (diff === 0) return 'Hết hạn hôm nay!'
	if (diff <= 3) return `Còn ${diff} ngày (${d.format('DD/MM')})`
	return `Deadline: ${d.format('DD/MM/YYYY HH:mm')}`
})

const isDeadlineSoon = computed(() => {
	if (!props.folder?.submission_deadline) return false
	const d = dayjs(props.folder.submission_deadline)
	return d.diff(dayjs(), 'day') <= 3
})

function renderMarkdown(text) {
	if (!text) return ''
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
		.replace(/\*(.+?)\*/g, '<em>$1</em>')
		.replace(/`(.+?)`/g, '<code>$1</code>')
		.replace(/^### (.+)$/gm, '<h3>$1</h3>')
		.replace(/^## (.+)$/gm, '<h2>$1</h2>')
		.replace(/^# (.+)$/gm, '<h1>$1</h1>')
		.replace(/^- (.+)$/gm, '<li>$1</li>')
		.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
		.replace(/\n\n/g, '</p><p>')
		.replace(/\n/g, '<br>')
}
</script>
