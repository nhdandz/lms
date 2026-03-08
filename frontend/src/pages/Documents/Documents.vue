<template>
	<div class="h-screen flex flex-col">
		<!-- Header -->
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<div class="flex items-center space-x-2">
				<Button
					variant="ghost"
					size="sm"
					class="lg:hidden"
					@click="showSidebar = !showSidebar"
				>
					<Menu class="w-5 h-5" />
				</Button>
				<Breadcrumbs class="h-7" :items="breadcrumbItems" />
				<!-- Ranking badge -->
				<Badge
					v-if="isRankingEnabled"
					label="Leaderboard"
					variant="subtle"
					theme="yellow"
				>
					<template #prefix>
						<Trophy class="w-3 h-3" />
					</template>
				</Badge>
			</div>
			<div class="flex items-center space-x-2">
				<!-- Toggle Ranking Settings (for moderators) -->
				<Button
					v-if="canUpload && currentFolder"
					variant="ghost"
					@click="showRankingSettings = true"
					:title="__('Ranking Settings')"
				>
					<Trophy class="h-4 w-4" :class="isRankingEnabled ? 'text-yellow-500' : ''" />
				</Button>
				<Button
					v-if="canUpload"
					variant="solid"
					@click="showUploadModal = true"
				>
					<template #prefix>
						<Upload class="h-4 w-4" />
					</template>
					<span class="hidden sm:inline">{{ __('Upload') }}</span>
				</Button>
				<Button
					v-if="canUpload"
					variant="outline"
					@click="showCreateFolder = true"
				>
					<template #prefix>
						<FolderPlus class="h-4 w-4" />
					</template>
					<span class="hidden sm:inline">{{ __('New Folder') }}</span>
				</Button>
			</div>
		</header>

		<div class="flex flex-1 overflow-hidden">
			<!-- Sidebar -->
			<aside
				class="w-64 flex-shrink-0 bg-surface-gray-1 border-r overflow-y-auto transition-all duration-200"
				:class="showSidebar ? 'block' : 'hidden lg:block'"
			>
				<DocumentsSidebar
					ref="sidebarRef"
					:currentFolder="currentFolder"
					@select-folder="navigateToFolder"
				/>
			</aside>

			<!-- Main Content -->
			<main class="flex-1 overflow-y-auto bg-surface-white">
				<div class="p-4 sm:p-6">
					<!-- Toolbar -->
					<div
						class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6"
					>
						<div class="flex items-center space-x-4">
							<!-- Back Button -->
							<Button
								v-if="currentFolder"
								variant="ghost"
								size="sm"
								@click="goBack"
							>
								<ArrowLeft class="w-4 h-4" />
							</Button>
							<div>
								<h2 class="text-lg font-semibold text-ink-gray-9">
									{{ currentFolderName || __('All Documents') }}
								</h2>
								<p class="text-sm text-ink-gray-5">
									{{ folderContents.data?.folders?.length || 0 }}
									{{ __('folders') }},
									{{ folderContents.data?.documents?.length || 0 }}
									{{ __('files') }}
								</p>
							</div>
						</div>

						<div class="flex items-center space-x-3">
							<!-- Search -->
							<FormControl
								type="text"
								:placeholder="__('Search...')"
								v-model="searchQuery"
								class="w-48"
								@input="debouncedSearch"
							>
								<template #prefix>
									<Search class="w-4 h-4 text-ink-gray-5" />
								</template>
							</FormControl>

							<!-- View Toggle -->
							<div class="flex items-center border rounded-lg">
								<button
									class="p-2 transition-colors"
									:class="
										viewMode === 'grid'
											? 'bg-surface-gray-2'
											: 'hover:bg-surface-gray-1'
									"
									@click="viewMode = 'grid'"
								>
									<LayoutGrid class="w-4 h-4" />
								</button>
								<button
									class="p-2 transition-colors"
									:class="
										viewMode === 'list'
											? 'bg-surface-gray-2'
											: 'hover:bg-surface-gray-1'
									"
									@click="viewMode = 'list'"
								>
									<List class="w-4 h-4" />
								</button>
							</div>
						</div>
					</div>

					<!-- Folder Notes -->
					<FolderNotes
						v-if="currentFolder"
						:folder="folderContents.data?.current_folder"
						:folder-name="currentFolder"
						class="mb-4"
						@updated="folderContents.reload()"
					/>

					<!-- Loading State -->
					<div
						v-if="folderContents.loading"
						class="flex justify-center py-20"
					>
						<LoadingIndicator class="w-8 h-8" />
					</div>

					<!-- Content -->
					<div v-else>
						<!-- Leaderboard Section (if ranking enabled) -->
						<div v-if="isRankingEnabled" class="mb-8">
							<FolderLeaderboard
								:category="currentFolder"
								:folder="folderContents.data?.current_folder"
								@refresh="folderContents.reload()"
							/>
						</div>

						<!-- Folders Section -->
						<div
							v-if="filteredFolders.length > 0"
							class="mb-6"
						>
							<h3
								class="text-sm font-medium text-ink-gray-5 mb-3"
							>
								{{ __('Folders') }}
							</h3>
							<div
								:class="
									viewMode === 'grid'
										? 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3'
										: 'space-y-1'
								"
							>
								<FolderCard
									v-for="folder in filteredFolders"
									:key="folder.name"
									:folder="folder"
									:viewMode="viewMode"
									@click="navigateToFolder(folder.name)"
									@delete="confirmDeleteFolder"
									@rename="confirmRenameFolder"
								/>
							</div>
						</div>

						<!-- Documents Section -->
						<div v-if="filteredDocuments.length > 0">
							<h3
								v-if="filteredFolders.length > 0"
								class="text-sm font-medium text-ink-gray-5 mb-3"
							>
								{{ __('Files') }}
							</h3>
							<div
								:class="
									viewMode === 'grid'
										? 'grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4'
										: 'space-y-1'
								"
							>
								<DocumentCard
									v-for="doc in filteredDocuments"
									:key="doc.name"
									:document="doc"
									:viewMode="viewMode"
									@preview="openPreview"
									@download="downloadDocument"
									@delete="confirmDelete"
								/>
							</div>
						</div>

						<!-- Empty State -->
						<div
							v-if="
								!isRankingEnabled &&
								filteredFolders.length === 0 &&
								filteredDocuments.length === 0
							"
							class="flex flex-col items-center justify-center py-20"
						>
							<FolderOpen
								class="w-16 h-16 text-ink-gray-3 mb-4"
							/>
							<p class="text-lg font-medium text-ink-gray-7 mb-2">
								{{ __('This folder is empty') }}
							</p>
							<p class="text-sm text-ink-gray-5 mb-4">
								{{ __('Upload files or create subfolders') }}
							</p>
							<div class="flex space-x-2">
								<Button
									v-if="canUpload"
									variant="solid"
									@click="showUploadModal = true"
								>
									<template #prefix>
										<Upload class="w-4 h-4" />
									</template>
									{{ __('Upload File') }}
								</Button>
								<Button
									v-if="canUpload"
									variant="outline"
									@click="showCreateFolder = true"
								>
									<template #prefix>
										<FolderPlus class="w-4 h-4" />
									</template>
									{{ __('New Folder') }}
								</Button>
							</div>
						</div>
					</div>
				</div>
			</main>
		</div>

		<!-- Upload Modal -->
		<DocumentUploadModal
			v-model="showUploadModal"
			:defaultCategory="currentFolder"
			@success="onUploadSuccess"
		/>

		<!-- Preview Modal -->
		<DocumentPreviewModal
			v-model="showPreviewModal"
			:document="selectedDocument"
		/>

		<!-- Create Folder Dialog -->
		<Dialog
			v-model="showCreateFolder"
			:options="{
				title: __('New Folder'),
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
				<FormControl
					:label="__('Folder Name')"
					v-model="newFolderName"
					:placeholder="__('Enter folder name')"
				/>
			</template>
		</Dialog>

		<!-- Delete Confirmation -->
		<Dialog
			v-model="showDeleteDialog"
			:options="{
				title: __('Delete'),
				message: deleteMessage,
				actions: [
					{
						label: __('Delete'),
						variant: 'solid',
						theme: 'red',
						onClick: (close) => executeDelete(close),
					},
				],
			}"
		/>

		<!-- Rename Folder Dialog -->
	<Dialog
		v-model="showRenameDialog"
		:options="{
			title: __('Rename Folder'),
			size: 'sm',
			actions: [
				{
					label: __('Rename'),
					variant: 'solid',
					onClick: (close) => executeRename(close),
				},
			],
		}"
	>
		<template #body-content>
			<FormControl
				:label="__('Folder Name')"
				v-model="renameValue"
				:placeholder="__('Enter new folder name')"
			/>
		</template>
	</Dialog>

	<!-- Ranking Settings Modal -->
		<Dialog
			v-model="showRankingSettings"
			:options="{
				title: __('Ranking Settings'),
				size: 'lg',
				actions: [
					{
						label: __('Save'),
						variant: 'solid',
						onClick: (close) => saveRankingSettings(close),
					},
				],
			}"
		>
			<template #body-content>
				<div class="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
					<FormControl
						type="checkbox"
						v-model="rankingForm.is_ranking_enabled"
						:label="__('Enable Leaderboard')"
					/>

					<div v-if="rankingForm.is_ranking_enabled" class="space-y-4 pt-2">
						<!-- Basic Settings -->
						<div class="grid grid-cols-2 gap-4">
							<FormControl
								type="select"
								v-model="rankingForm.ranking_type"
								:label="__('Ranking Type')"
								:options="[
									{ label: 'Score (Higher is better)', value: 'Score' },
									{ label: 'Rank (Lower is better)', value: 'Rank' },
									{ label: 'Points', value: 'Points' },
								]"
							/>
							<FormControl
								type="select"
								v-model="rankingForm.contest_type"
								:label="__('Contest Type')"
								:options="[
									{ label: 'General', value: 'General' },
									{ label: 'Club Activity', value: 'Club Activity' },
									{ label: 'Olympic', value: 'Olympic' },
									{ label: 'Data Challenge', value: 'Data Challenge' },
									{ label: 'Algorithm Contest', value: 'Algorithm Contest' },
									{ label: 'Competitive Programming', value: 'Competitive Programming' },
								]"
							/>
						</div>

						<div class="grid grid-cols-2 gap-4">
							<FormControl
								type="text"
								v-model="rankingForm.organizer_name"
								:label="__('Organizer / Club')"
								:placeholder="__('e.g. CLB Tin học')"
							/>
							<FormControl
								type="select"
								v-model="rankingForm.contest_difficulty"
								:label="__('Difficulty')"
								:options="[
									{ label: '—', value: '' },
									{ label: 'Beginner', value: 'Beginner' },
									{ label: 'Intermediate', value: 'Intermediate' },
									{ label: 'Advanced', value: 'Advanced' },
									{ label: 'Expert', value: 'Expert' },
								]"
							/>
						</div>

						<div class="grid grid-cols-2 gap-4">
							<FormControl
								type="text"
								v-model="rankingForm.external_contest_url"
								:label="__('External Contest URL')"
								:placeholder="__('https://codeforces.com/contest/...')"
							/>
							<FormControl
								type="number"
								v-model="rankingForm.max_score"
								:label="__('Max Score (optional)')"
							/>
						</div>

						<FormControl
							type="text"
							v-model="rankingForm.contest_tags"
							:label="__('Tags (phân cách bằng dấu phẩy)')"
							:placeholder="__('e.g. graph, dp, greedy')"
						/>

						<FormControl
							type="text"
							v-model="rankingForm.contest_prize_info"
							:label="__('Prize / Reward')"
							:placeholder="__('e.g. Giải nhất: 500k')"
						/>

						<div class="grid grid-cols-2 gap-4">
							<FormControl
								type="checkbox"
								v-model="rankingForm.allow_self_submission"
								:label="__('Allow Self Submission')"
							/>
							<FormControl
								type="checkbox"
								v-model="rankingForm.require_approval"
								:label="__('Require Approval')"
							/>
						</div>

						<!-- Contest Info Section -->
						<div class="border-t pt-4 space-y-4">
							<p class="text-sm font-semibold text-ink-gray-7">{{ __('Contest Information') }}</p>

							<div>
								<label class="text-sm font-medium text-ink-gray-7 block mb-1">{{ __('Contest Overview') }}</label>
								<textarea
									v-model="rankingForm.contest_description"
									class="w-full rounded border border-surface-gray-3 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-y"
									rows="3"
									:placeholder="__('Mô tả tổng quan về contest...')"
								/>
							</div>

							<div>
								<label class="text-sm font-medium text-ink-gray-7 block mb-1">{{ __('Problem Statement') }}</label>
								<textarea
									v-model="rankingForm.contest_problem_statement"
									class="w-full rounded border border-surface-gray-3 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-y"
									rows="4"
									:placeholder="__('Mô tả bài toán (hỗ trợ markdown)...')"
								/>
							</div>

							<div>
								<label class="text-sm font-medium text-ink-gray-7 block mb-1">{{ __('Data / Dataset Information') }}</label>
								<textarea
									v-model="rankingForm.contest_dataset_info"
									class="w-full rounded border border-surface-gray-3 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-y"
									rows="3"
									:placeholder="__('Thông tin về dataset...')"
								/>
							</div>

							<FormControl
								type="text"
								v-model="rankingForm.contest_evaluation_metric"
								:label="__('Evaluation Metric')"
								:placeholder="__('e.g. Accuracy, F1-score, MSE')"
							/>

							<div>
								<label class="text-sm font-medium text-ink-gray-7 block mb-1">{{ __('Submission Format') }}</label>
								<textarea
									v-model="rankingForm.contest_submission_format"
									class="w-full rounded border border-surface-gray-3 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-y"
									rows="3"
									:placeholder="__('Định dạng nộp bài...')"
								/>
							</div>

							<div>
								<label class="text-sm font-medium text-ink-gray-7 block mb-1">{{ __('Rules & Regulations') }}</label>
								<textarea
									v-model="rankingForm.contest_rules"
									class="w-full rounded border border-surface-gray-3 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 resize-y"
									rows="3"
									:placeholder="__('Quy định tham gia...')"
								/>
							</div>
						</div>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import {
	Button,
	Breadcrumbs,
	createResource,
	FormControl,
	Dialog,
	LoadingIndicator,
	Badge,
	usePageMeta,
	toast,
	call,
} from 'frappe-ui'
import {
	Upload,
	Search,
	FolderPlus,
	FolderOpen,
	Menu,
	ArrowLeft,
	LayoutGrid,
	List,
	Trophy,
} from 'lucide-vue-next'
import { computed, ref, inject, watch, reactive } from 'vue'
import { sessionStore } from '@/stores/session'
import DocumentsSidebar from '@/components/DocumentsSidebar.vue'
import DocumentCard from '@/components/DocumentCard.vue'
import FolderCard from '@/components/FolderCard.vue'
import FolderLeaderboard from '@/components/FolderLeaderboard.vue'
import FolderNotes from '@/components/FolderNotes.vue'
import DocumentUploadModal from '@/components/Modals/DocumentUploadModal.vue'
import DocumentPreviewModal from '@/components/Modals/DocumentPreviewModal.vue'
import { debounce } from '@/utils/debounce'

const user = inject('$user')
const { brand } = sessionStore()

// State
const currentFolder = ref(null)
const searchQuery = ref('')
const viewMode = ref('grid')
const showSidebar = ref(true)
const showUploadModal = ref(false)
const showPreviewModal = ref(false)
const showCreateFolder = ref(false)
const showDeleteDialog = ref(false)
const showRenameDialog = ref(false)
const renamingFolder = ref(null)
const renameValue = ref('')
const showRankingSettings = ref(false)
const selectedDocument = ref(null)
const itemToDelete = ref(null)
const deleteType = ref(null)
const newFolderName = ref('')
const sidebarRef = ref(null)

// Ranking form
const rankingForm = reactive({
	is_ranking_enabled: false,
	ranking_type: 'Score',
	external_contest_url: '',
	max_score: null,
	allow_self_submission: true,
	require_approval: false,
	contest_type: '',
	organizer_name: '',
	contest_difficulty: '',
	contest_tags: '',
	contest_prize_info: '',
	contest_description: '',
	contest_problem_statement: '',
	contest_dataset_info: '',
	contest_evaluation_metric: '',
	contest_submission_format: '',
	contest_rules: '',
})

// Computed
const canUpload = computed(() => {
	return (
		user.data?.is_instructor ||
		user.data?.is_moderator ||
		user.data?.is_system_manager
	)
})

const isRankingEnabled = computed(() => {
	return folderContents.data?.current_folder?.is_ranking_enabled
})

const currentFolderName = computed(() => {
	return folderContents.data?.current_folder?.category_name || null
})

const breadcrumbItems = computed(() => {
	const items = [{ label: __('Documents'), route: { name: 'Documents' } }]

	if (folderContents.data?.current_folder) {
		// Build breadcrumb path (simplified - just current folder)
		items.push({
			label: folderContents.data.current_folder.category_name,
		})
	}

	return items
})

const deleteMessage = computed(() => {
	if (deleteType.value === 'folder') {
		return __('Are you sure you want to delete this folder? All documents inside will be moved to root.')
	}
	return __('Are you sure you want to delete this document? This action cannot be undone.')
})

const filteredFolders = computed(() => {
	const folders = folderContents.data?.folders || []
	if (!searchQuery.value) return folders
	const query = searchQuery.value.toLowerCase()
	return folders.filter((f) =>
		f.category_name.toLowerCase().includes(query)
	)
})

const filteredDocuments = computed(() => {
	const docs = folderContents.data?.documents || []
	if (!searchQuery.value) return docs
	const query = searchQuery.value.toLowerCase()
	return docs.filter(
		(d) =>
			d.title.toLowerCase().includes(query) ||
			(d.description && d.description.toLowerCase().includes(query))
	)
})

// Resources
const folderContents = createResource({
	url: 'lms.lms.api.get_folder_contents',
	makeParams() {
		return { folder: currentFolder.value }
	},
	auto: true,
})

// Methods
const navigateToFolder = (folderName) => {
	currentFolder.value = folderName
	searchQuery.value = ''
}

const goBack = () => {
	if (folderContents.data?.current_folder?.parent_category) {
		currentFolder.value =
			folderContents.data.current_folder.parent_category
	} else {
		currentFolder.value = null
	}
}

const debouncedSearch = debounce(() => {
	// Search is client-side, no API call needed
}, 300)

const openPreview = (doc) => {
	selectedDocument.value = doc
	showPreviewModal.value = true
}

const downloadDocument = async (doc) => {
	try {
		const response = await createResource({
			url: 'lms.lms.api.track_document_download',
			params: { document_name: doc.name },
		}).fetch()

		if (response.file_url) {
			const link = window.document.createElement('a')
			link.href = response.file_url
			link.download = doc.title
			link.target = '_blank'
			window.document.body.appendChild(link)
			link.click()
			window.document.body.removeChild(link)
		}
	} catch (error) {
		toast.error(__('Failed to download document'))
	}
}

const confirmDelete = (doc) => {
	itemToDelete.value = doc
	deleteType.value = 'document'
	showDeleteDialog.value = true
}

const confirmDeleteFolder = (folder) => {
	itemToDelete.value = folder
	deleteType.value = 'folder'
	showDeleteDialog.value = true
}

const confirmRenameFolder = (folder) => {
	renamingFolder.value = folder
	renameValue.value = folder.category_name
	showRenameDialog.value = true
}

const executeRename = async (close) => {
	if (!renameValue.value.trim()) {
		toast.error(__('Folder name is required'))
		return
	}
	try {
		await createResource({
			url: 'frappe.client.set_value',
			params: {
				doctype: 'LMS Document Category',
				name: renamingFolder.value.name,
				fieldname: 'category_name',
				value: renameValue.value.trim(),
			},
		}).fetch()
		toast.success(__('Folder renamed successfully'))
		close()
		folderContents.reload()
		sidebarRef.value?.reload()
	} catch (error) {
		toast.error(error.messages?.[0] || __('Failed to rename folder'))
	}
}

const executeDelete = async (close) => {
	try {
		if (deleteType.value === 'folder') {
			await createResource({
				url: 'frappe.client.delete',
				params: {
					doctype: 'LMS Document Category',
					name: itemToDelete.value.name,
				},
			}).fetch()
			toast.success(__('Folder deleted successfully'))
		} else {
			await createResource({
				url: 'lms.lms.api.delete_document',
				params: { document_name: itemToDelete.value.name },
			}).fetch()
			toast.success(__('Document deleted successfully'))
		}
		close()
		folderContents.reload()
		sidebarRef.value?.reload()
	} catch (error) {
		toast.error(__('Failed to delete'))
	}
}

const createFolder = async (close) => {
	if (!newFolderName.value.trim()) {
		toast.error(__('Folder name is required'))
		return
	}

	try {
		await createResource({
			url: 'frappe.client.insert',
			params: {
				doc: {
					doctype: 'LMS Document Category',
					category_name: newFolderName.value.trim(),
					parent_category: currentFolder.value,
					is_group: 1,
				},
			},
		}).fetch()

		toast.success(__('Folder created successfully'))
		newFolderName.value = ''
		close()
		folderContents.reload()
		sidebarRef.value?.reload()
	} catch (error) {
		toast.error(error.messages?.[0] || __('Failed to create folder'))
	}
}

const onUploadSuccess = () => {
	showUploadModal.value = false
	folderContents.reload()
	sidebarRef.value?.reload()
	toast.success(__('Document uploaded successfully'))
}

// Load ranking settings when opening modal
watch(showRankingSettings, (val) => {
	if (val && folderContents.data?.current_folder) {
		const folder = folderContents.data.current_folder
		rankingForm.is_ranking_enabled = folder.is_ranking_enabled || false
		rankingForm.ranking_type = folder.ranking_type || 'Score'
		rankingForm.external_contest_url = folder.external_contest_url || ''
		rankingForm.max_score = folder.max_score || null
		rankingForm.allow_self_submission = folder.allow_self_submission !== false
		rankingForm.require_approval = folder.require_approval || false
		rankingForm.contest_type = folder.contest_type || ''
		rankingForm.organizer_name = folder.organizer_name || ''
		rankingForm.contest_difficulty = folder.contest_difficulty || ''
		rankingForm.contest_tags = folder.contest_tags || ''
		rankingForm.contest_prize_info = folder.contest_prize_info || ''
		rankingForm.contest_description = folder.contest_description || ''
		rankingForm.contest_problem_statement = folder.contest_problem_statement || ''
		rankingForm.contest_dataset_info = folder.contest_dataset_info || ''
		rankingForm.contest_evaluation_metric = folder.contest_evaluation_metric || ''
		rankingForm.contest_submission_format = folder.contest_submission_format || ''
		rankingForm.contest_rules = folder.contest_rules || ''
	}
})

const saveRankingSettings = async (close) => {
	try {
		await call('lms.lms.api.update_folder_ranking_settings', {
			folder_name: currentFolder.value,
			is_ranking_enabled: rankingForm.is_ranking_enabled,
			ranking_type: rankingForm.ranking_type,
			external_contest_url: rankingForm.external_contest_url || null,
			max_score: rankingForm.max_score || null,
			allow_self_submission: rankingForm.allow_self_submission,
			require_approval: rankingForm.require_approval,
			contest_type: rankingForm.contest_type || null,
			organizer_name: rankingForm.organizer_name || null,
			contest_difficulty: rankingForm.contest_difficulty || null,
			contest_tags: rankingForm.contest_tags || null,
			contest_prize_info: rankingForm.contest_prize_info || null,
			contest_description: rankingForm.contest_description || null,
			contest_problem_statement: rankingForm.contest_problem_statement || null,
			contest_dataset_info: rankingForm.contest_dataset_info || null,
			contest_evaluation_metric: rankingForm.contest_evaluation_metric || null,
			contest_submission_format: rankingForm.contest_submission_format || null,
			contest_rules: rankingForm.contest_rules || null,
		})
		toast.success(__('Ranking settings saved'))
		close()
		folderContents.reload()
		sidebarRef.value?.reload()
	} catch (error) {
		toast.error(error.messages?.[0] || __('Failed to save settings'))
	}
}

// Watch for folder changes
watch(currentFolder, () => {
	folderContents.reload()
})

usePageMeta(() => {
	return {
		title: __('Documents'),
		icon: brand.favicon,
	}
})
</script>
