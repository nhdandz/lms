<template>
	<div class="aiit-root" ref="rootRef">
		<!-- Scan-line overlay -->
		<div class="scanlines" aria-hidden="true" />

		<!-- Neural Network Canvas -->
		<canvas ref="canvasRef" class="neural-canvas" aria-hidden="true" />

		<!-- ─────────────── NAVIGATION ─────────────── -->
		<nav class="aiit-nav" :class="{ scrolled: isScrolled }">
			<div class="nav-inner">
				<a href="#hero" class="nav-logo" @click.prevent="scrollTo('hero')">
					<span class="logo-bracket">[</span>
					<span class="logo-text">AIIT</span>
					<span class="logo-bracket">]</span>
					<span class="logo-sub">MTA</span>
				</a>
				<div class="nav-links">
					<a v-for="link in navLinks" :key="link.id"
						class="nav-link" @click.prevent="scrollTo(link.id)">
						{{ link.label }}
					</a>
				</div>
				<div class="nav-actions">
					<a v-if="user.data" :href="getLmsRoute('/courses')" class="btn-secondary-sm">
						<span>Dashboard</span>
					</a>
					<a v-else href="/login" class="btn-primary-sm">
						<span>Đăng nhập</span>
					</a>
				</div>
			</div>
		</nav>

		<!-- ─────────────── HERO ─────────────── -->
		<section id="hero" class="hero-section">
			<div class="hero-content">
				<div class="hero-badge reveal">
					<span class="badge-dot" />
					<span class="mono">Học viện Kỹ thuật Quân sự — AIIT CLB</span>
				</div>

				<h1 class="hero-headline reveal reveal-delay-1">
					<span class="headline-line">AIIT CLUB:</span>
					<span class="headline-line accent-emerald">TIÊN PHONG CÔNG NGHỆ</span>
					<span class="headline-line accent-blue">ĐỘT PHÁ TRÍ TUỆ</span>
				</h1>

				<p class="hero-sub reveal reveal-delay-2">
					Câu lạc bộ CNTT Học viện Kỹ thuật Quân sự — Nơi hội tụ đam mê,<br>
					làm chủ AI và định hình tương lai kỹ sư quân sự thời đại số.
				</p>

				<!-- Typewriter -->
				<div class="typewriter-wrap reveal reveal-delay-3">
					<span class="mono tw-prefix">▶ Chuyên sâu về: </span>
					<span class="mono tw-text">{{ typewriterText }}</span>
					<span class="tw-cursor">|</span>
				</div>

				<div class="hero-cta reveal reveal-delay-4">
					<a href="#join" @click.prevent="scrollTo('join')" class="btn-glow">
						<span>⚡ Gia nhập ngay</span>
					</a>
					<a href="#projects" @click.prevent="scrollTo('projects')" class="btn-outline">
						<span>🔬 Khám phá Lab</span>
					</a>
				</div>

				<!-- Floating tech tags -->
				<div class="tech-tags reveal reveal-delay-4">
					<span v-for="tag in techTags" :key="tag" class="tech-tag mono">{{ tag }}</span>
				</div>
			</div>

			<!-- Scroll indicator -->
			<div class="scroll-indicator">
				<span class="mono text-xs" style="color:#10B981">scroll</span>
				<div class="scroll-line" />
			</div>
		</section>

		<!-- ─────────────── AI PILLARS BENTO ─────────────── -->
		<section id="about" class="section-dark">
			<div class="container">
				<div class="section-header" ref="pillarsHeaderRef">
					<span class="section-tag mono">// LĨNH VỰC NGHIÊN CỨU</span>
					<h2 class="section-title">Bốn trụ cột <span class="accent-emerald">AI-First</span></h2>
					<p class="section-desc">Chúng tôi tập trung nghiên cứu và ứng dụng các lĩnh vực tiên tiến nhất của Trí tuệ Nhân tạo</p>
				</div>

				<div class="bento-grid">
					<div v-for="(pillar, i) in pillars" :key="pillar.id"
						class="bento-card" :class="[pillar.size, `bento-${i}`]"
						:style="{ '--accent': pillar.color }">
						<div class="bento-icon">{{ pillar.icon }}</div>
						<div class="bento-tag mono">{{ pillar.tag }}</div>
						<h3 class="bento-title">{{ pillar.title }}</h3>
						<p class="bento-desc">{{ pillar.desc }}</p>
						<div class="bento-chips">
							<span v-for="chip in pillar.chips" :key="chip" class="bento-chip mono">{{ chip }}</span>
						</div>
						<div class="bento-glow" />
					</div>
				</div>
			</div>
		</section>

		<!-- ─────────────── PROJECTS ─────────────── -->
		<section id="projects" class="section-darker">
			<div class="container">
				<div class="section-header">
					<span class="section-tag mono">// DỰ ÁN NỔI BẬT</span>
					<h2 class="section-title">Research & <span class="accent-blue">Projects</span></h2>
					<p class="section-desc">Các sản phẩm nghiên cứu thực chiến từ phòng lab AIIT</p>
				</div>

				<div class="projects-grid">
					<div v-for="project in projects" :key="project.id"
						class="project-card" :style="{ '--card-accent': project.accent }">
						<div class="project-header">
							<span class="project-icon">{{ project.icon }}</span>
							<span class="project-status mono" :class="project.statusClass">{{ project.status }}</span>
						</div>
						<h3 class="project-title">{{ project.title }}</h3>
						<p class="project-desc">{{ project.desc }}</p>
						<div class="project-stack">
							<span v-for="tech in project.stack" :key="tech" class="stack-chip mono">{{ tech }}</span>
						</div>
						<div class="project-footer">
							<span class="mono project-field">{{ project.field }}</span>
							<span class="project-arrow">→</span>
						</div>
						<div class="project-glow" />
					</div>
				</div>
			</div>
		</section>

		<!-- ─────────────── STATS ─────────────── -->
		<section id="stats" class="section-dark stats-section" ref="statsRef">
			<div class="container">
				<div class="stats-grid">
					<div v-for="stat in stats" :key="stat.id" class="stat-card">
						<div class="stat-num mono">
							<span>{{ displayedStats[stat.id] }}</span>
							<span class="stat-suffix">{{ stat.suffix }}</span>
						</div>
						<div class="stat-label">{{ stat.label }}</div>
						<div class="stat-icon">{{ stat.icon }}</div>
					</div>
				</div>

				<!-- Timeline / milestones -->
				<div class="timeline">
					<div v-for="milestone in milestones" :key="milestone.year" class="timeline-item">
						<div class="timeline-dot" />
						<div class="timeline-content">
							<span class="mono timeline-year">{{ milestone.year }}</span>
							<p class="timeline-text">{{ milestone.text }}</p>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- ─────────────── TUYỂN THÀNH VIÊN ─────────────── -->
		<section id="join" class="section-darker join-section">
			<div class="container">
				<div class="join-card">
					<div class="join-bg-text mono" aria-hidden="true">JOIN</div>
					<span class="section-tag mono">// TUYỂN THÀNH VIÊN</span>
					<h2 class="join-title">Bạn đam mê <span class="accent-emerald">AI & CNTT</span>?</h2>
					<p class="join-desc">
						AIIT Club đang tìm kiếm những sinh viên MTA có nhiệt huyết, ham học hỏi<br>
						và muốn tạo ra sản phẩm công nghệ có giá trị thực tế.
					</p>
					<div class="join-requirements">
						<div v-for="req in requirements" :key="req" class="req-item">
							<span class="req-check">✓</span>
							<span>{{ req }}</span>
						</div>
					</div>
					<div class="join-cta">
						<a href="https://aiitclub.inict.mta.edu.vn" target="_blank" class="btn-glow">
							<span>🚀 Đăng ký tham gia</span>
						</a>
						<a :href="getLmsRoute('/courses')" class="btn-outline">
							<span>📚 Xem khóa học</span>
						</a>
					</div>
				</div>
			</div>
		</section>

		<!-- ─────────────── DASHBOARD (logged in) ─────────────── -->
		<section v-if="user.data" class="section-dark dashboard-section">
			<div class="container">
				<div class="section-header">
					<span class="section-tag mono">// DASHBOARD</span>
					<h2 class="section-title">
						Xin chào, <span class="accent-emerald">{{ user.data?.full_name }}</span> 👋
					</h2>
					<p class="section-desc">{{ dashboardSubtitle }}</p>
				</div>
				<div class="dashboard-links">
					<a v-for="dl in dashboardLinks" :key="dl.to" :href="dl.to" class="dash-link">
						<span class="dash-icon">{{ dl.icon }}</span>
						<span>{{ dl.label }}</span>
						<span class="dash-arrow mono">→</span>
					</a>
				</div>
			</div>
		</section>

		<!-- ─────────────── FOOTER ─────────────── -->
		<footer class="aiit-footer">
			<div class="container footer-inner">
				<div class="footer-logo">
					<span class="logo-bracket">[</span>
					<span class="logo-text">AIIT</span>
					<span class="logo-bracket">]</span>
					<span class="logo-sub">MTA</span>
				</div>
				<p class="footer-desc mono">
					© {{ new Date().getFullYear() }} AIIT Club — Học viện Kỹ thuật Quân sự<br>
					<span style="color:#10B981">inict.mta.edu.vn</span>
				</p>
				<div class="footer-links">
					<a href="https://aiitclub.inict.mta.edu.vn" target="_blank" class="footer-link">Website chính thức</a>
					<a href="https://inict.mta.edu.vn" target="_blank" class="footer-link">Khoa CNTT — MTA</a>
					<a :href="getLmsRoute('/courses')" class="footer-link">Khóa học</a>
					<a :href="getLmsRoute('/roadmaps')" class="footer-link">Roadmaps</a>
				</div>
			</div>
		</footer>
	</div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, inject, reactive } from 'vue'
import { createResource } from 'frappe-ui'
import { getLmsRoute } from '@/utils/basePath'

const user = inject('$user')

// ─── Navigation ───
const navLinks = [
	{ id: 'about', label: 'Lĩnh vực' },
	{ id: 'projects', label: 'Dự án' },
	{ id: 'stats', label: 'Thành tựu' },
	{ id: 'join', label: 'Tuyển thành viên' },
]

const isScrolled = ref(false)
const rootRef = ref(null)

// ─── Canvas Neural Network ───
const canvasRef = ref(null)
let animationId = null

function initCanvas() {
	const canvas = canvasRef.value
	if (!canvas) return
	const ctx = canvas.getContext('2d')

	const resize = () => {
		canvas.width = window.innerWidth
		canvas.height = window.innerHeight
	}
	resize()
	window.addEventListener('resize', resize)

	const DOTS = 80
	const MAX_DIST = 160
	const dots = Array.from({ length: DOTS }, () => ({
		x: Math.random() * canvas.width,
		y: Math.random() * canvas.height,
		vx: (Math.random() - 0.5) * 0.4,
		vy: (Math.random() - 0.5) * 0.4,
		r: Math.random() * 1.5 + 0.5,
	}))

	function draw() {
		ctx.clearRect(0, 0, canvas.width, canvas.height)

		// Move dots
		dots.forEach((d) => {
			d.x += d.vx
			d.y += d.vy
			if (d.x < 0 || d.x > canvas.width) d.vx *= -1
			if (d.y < 0 || d.y > canvas.height) d.vy *= -1
		})

		// Draw connections
		for (let i = 0; i < dots.length; i++) {
			for (let j = i + 1; j < dots.length; j++) {
				const dx = dots[i].x - dots[j].x
				const dy = dots[i].y - dots[j].y
				const dist = Math.sqrt(dx * dx + dy * dy)
				if (dist < MAX_DIST) {
					const alpha = (1 - dist / MAX_DIST) * 0.25
					ctx.beginPath()
					ctx.strokeStyle = `rgba(16,185,129,${alpha})`
					ctx.lineWidth = 0.8
					ctx.moveTo(dots[i].x, dots[i].y)
					ctx.lineTo(dots[j].x, dots[j].y)
					ctx.stroke()
				}
			}
		}

		// Draw dots
		dots.forEach((d) => {
			ctx.beginPath()
			ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2)
			ctx.fillStyle = 'rgba(16,185,129,0.6)'
			ctx.fill()
		})

		animationId = requestAnimationFrame(draw)
	}
	draw()
}

// ─── Typewriter ───
const typewriterText = ref('')
const keywords = ['LLM', 'Python', 'MLOps', 'React', 'Computer Vision', 'OSINT', 'Deep Learning', 'NLP', 'Cybersecurity', 'RAG']
let kwIndex = 0
let charIndex = 0
let typing = true
let typeTimer = null

function runTypewriter() {
	const word = keywords[kwIndex]
	if (typing) {
		typewriterText.value = word.slice(0, charIndex + 1)
		charIndex++
		if (charIndex >= word.length) {
			typing = false
			typeTimer = setTimeout(runTypewriter, 1400)
			return
		}
	} else {
		typewriterText.value = word.slice(0, charIndex - 1)
		charIndex--
		if (charIndex <= 0) {
			typing = true
			kwIndex = (kwIndex + 1) % keywords.length
		}
	}
	typeTimer = setTimeout(runTypewriter, typing ? 80 : 45)
}

// ─── Scroll ───
function onScroll() {
	isScrolled.value = window.scrollY > 60
}

function scrollTo(id) {
	document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

// ─── Reveal on scroll ───
let revealObserver = null
function initReveal() {
	revealObserver = new IntersectionObserver(
		(entries) => entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('revealed') }),
		{ threshold: 0.15 }
	)
	document.querySelectorAll('.reveal').forEach((el) => revealObserver.observe(el))
}

// ─── Stats counter ───
const statsRef = ref(null)
const displayedStats = reactive({ members: 0, projects: 0, awards: 0, years: 0 })
const stats = [
	{ id: 'members', target: 50, suffix: '+', label: 'Thành viên', icon: '👥' },
	{ id: 'projects', target: 10, suffix: '+', label: 'Dự án nghiên cứu', icon: '🔬' },
	{ id: 'awards', target: 5, suffix: '+', label: 'Giải thưởng', icon: '🏆' },
	{ id: 'years', target: 1, suffix: '', label: 'Năm hoạt động', icon: '📅' },
]
let statsAnimated = false

function animateStats() {
	if (statsAnimated) return
	statsAnimated = true
	stats.forEach((s) => {
		let cur = 0
		const step = s.target / 60
		const timer = setInterval(() => {
			cur = Math.min(cur + step, s.target)
			displayedStats[s.id] = Math.floor(cur)
			if (cur >= s.target) clearInterval(timer)
		}, 25)
	})
}

// ─── Data ───
const techTags = ['#LLM', '#ComputerVision', '#MLOps', '#OSINT', '#RAG', '#Python', '#NLP']

const pillars = [
	{
		id: 'llm', size: 'bento-large', icon: '🧠', tag: '01 / LLM',
		title: 'Large Language Models',
		desc: 'Nghiên cứu và ứng dụng các mô hình ngôn ngữ lớn cho bài toán tiếng Việt. Phát triển QBot, TSBot và hệ thống RAG nội bộ.',
		chips: ['GPT-4', 'LLaMA', 'RAG', 'LangChain', 'Vietnamese NLP'],
		color: '#10B981',
	},
	{
		id: 'cv', size: 'bento-medium', icon: '👁️', tag: '02 / CV',
		title: 'Computer Vision',
		desc: 'Xử lý ảnh và nhận diện mục tiêu trong môi trường quân sự. Object detection, segmentation, thermal imaging.',
		chips: ['YOLO', 'OpenCV', 'PyTorch', 'Thermal'],
		color: '#3B82F6',
	},
	{
		id: 'mlops', size: 'bento-medium', icon: '⚙️', tag: '03 / MLOps',
		title: 'MLOps & System',
		desc: 'Triển khai và vận hành hệ thống AI quy mô lớn. CI/CD cho ML, model serving, monitoring.',
		chips: ['Docker', 'Kubernetes', 'MLflow', 'FastAPI'],
		color: '#8B5CF6',
	},
	{
		id: 'cyber', size: 'bento-large', icon: '🛡️', tag: '04 / CYBER',
		title: 'Cyber Security & OSINT',
		desc: 'Bảo mật thông tin và tình báo nguồn mở. Phân tích mạng xã hội, threat intelligence, penetration testing.',
		chips: ['OSINT', 'Threat Intel', 'Pentest', 'Network Security'],
		color: '#F59E0B',
	},
]

const projects = [
	{
		id: 'rri', icon: '📚', status: 'LIVE', statusClass: 'status-live',
		title: 'Hệ thống quản lý tri thức RRI',
		desc: 'Nền tảng tập trung tri thức tổ chức, hỗ trợ tìm kiếm thông minh và chia sẻ tài liệu nội bộ cho đơn vị quân sự.',
		stack: ['RAG', 'Elasticsearch', 'React', 'FastAPI'],
		field: 'Knowledge Management', accent: '#10B981',
	},
	{
		id: 'qbot', icon: '🤖', status: 'v2.0', statusClass: 'status-beta',
		title: 'QBot — Trợ lý tài liệu tiếng Việt',
		desc: 'Chatbot AI chuyên biệt cho văn bản pháp lý và tài liệu kỹ thuật quân sự. Hiểu ngữ cảnh, trích dẫn nguồn chính xác.',
		stack: ['LLM', 'LangChain', 'Vietnamese BERT', 'Vue.js'],
		field: 'NLP / Chatbot', accent: '#3B82F6',
	},
	{
		id: 'osint', icon: '🔍', status: 'BETA', statusClass: 'status-beta',
		title: 'AI-Powered OSINT Dashboard',
		desc: 'Hệ thống thu thập và phân tích thông tin nguồn mở tự động, theo dõi mạng xã hội và phát hiện mối đe dọa.',
		stack: ['Scrapy', 'Kafka', 'ML Pipeline', 'Grafana'],
		field: 'OSINT / Intel', accent: '#F59E0B',
	},
]

const milestones = [
	{ year: '10/2025', text: 'Thành lập CLB AIIT — Học viện Kỹ thuật Quân sự' },
	{ year: '12/2025', text: 'Giải Nhất OLP Tin học Sinh viên khối chuyên Tin & khối không chuyên' },
	{ year: '12/2025', text: 'Giải Nhì OLP Trí tuệ Nhân tạo toàn quốc' },
	{ year: '12/2025', text: 'Nhiều giải thưởng Hackathon trong nước và khu vực' },
]

const requirements = [
	'Là sinh viên Học viện Kỹ thuật Quân sự',
	'Đam mê AI, lập trình hoặc an ninh mạng',
	'Sẵn sàng học hỏi và làm việc nhóm',
	'Không yêu cầu kinh nghiệm trước',
]

const dashboardSubtitle = computed(() => {
	if (user.data?.is_moderator || user.data?.is_instructor) return 'Quản lý khóa học và theo dõi học viên của bạn'
	return 'Tiếp tục hành trình học tập của bạn'
})

const dashboardLinks = [
	{ to: getLmsRoute('/courses'), icon: '📖', label: 'Khóa học' },
	{ to: getLmsRoute('/roadmaps'), icon: '🗺️', label: 'Roadmaps' },
	{ to: getLmsRoute('/batches'), icon: '👥', label: 'Batches' },
	{ to: getLmsRoute('/documents'), icon: '📂', label: 'Tài liệu' },
	{ to: getLmsRoute('/statistics'), icon: '📊', label: 'Thống kê' },
]

// ─── Lifecycle ───
onMounted(() => {
	initCanvas()
	runTypewriter()
	window.addEventListener('scroll', onScroll, { passive: true })
	setTimeout(initReveal, 100)

	// Stats observer
	const statsObserver = new IntersectionObserver(
		(entries) => { if (entries[0].isIntersecting) animateStats() },
		{ threshold: 0.3 }
	)
	if (statsRef.value) statsObserver.observe(statsRef.value)
})

onUnmounted(() => {
	cancelAnimationFrame(animationId)
	clearTimeout(typeTimer)
	window.removeEventListener('scroll', onScroll)
	revealObserver?.disconnect()
})
</script>

<style scoped>
/* ─── BASE ─── */
.aiit-root {
	background: #020617;
	color: #e2e8f0;
	min-height: 100vh;
	position: relative;
	overflow-x: hidden;
	font-family: 'Inter', system-ui, sans-serif;
}

.mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; }

/* ─── SCANLINES ─── */
.scanlines {
	position: fixed;
	inset: 0;
	z-index: 1;
	pointer-events: none;
	background: repeating-linear-gradient(
		to bottom,
		transparent,
		transparent 2px,
		rgba(0, 0, 0, 0.03) 2px,
		rgba(0, 0, 0, 0.03) 4px
	);
	animation: scanMove 8s linear infinite;
}
@keyframes scanMove {
	from { background-position: 0 0; }
	to   { background-position: 0 100px; }
}

/* ─── CANVAS ─── */
.neural-canvas {
	position: fixed;
	inset: 0;
	z-index: 0;
	pointer-events: none;
	opacity: 0.7;
}

/* ─── CONTAINER ─── */
.container {
	max-width: 1200px;
	margin: 0 auto;
	padding: 0 1.5rem;
}

/* ─── NAV ─── */
.aiit-nav {
	position: fixed;
	top: 0; left: 0; right: 0;
	z-index: 100;
	padding: 1rem 2rem;
	transition: all 0.4s ease;
	background: transparent;
}
.aiit-nav.scrolled {
	background: rgba(2, 6, 23, 0.92);
	backdrop-filter: blur(12px);
	border-bottom: 1px solid rgba(16, 185, 129, 0.2);
	padding: 0.6rem 2rem;
}
.nav-inner {
	max-width: 1200px;
	margin: 0 auto;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 2rem;
}
.nav-logo {
	display: flex;
	align-items: center;
	gap: 0.25rem;
	text-decoration: none;
	font-family: 'JetBrains Mono', monospace;
	font-weight: 700;
	font-size: 1.25rem;
}
.logo-bracket { color: #10B981; }
.logo-text { color: #fff; letter-spacing: 0.1em; }
.logo-sub {
	font-size: 0.65rem;
	color: #3B82F6;
	margin-left: 0.5rem;
	padding: 0.1rem 0.4rem;
	border: 1px solid #3B82F6;
	border-radius: 3px;
}
.nav-links {
	display: flex;
	gap: 2rem;
}
.nav-link {
	color: #94a3b8;
	font-size: 0.875rem;
	cursor: pointer;
	text-decoration: none;
	transition: color 0.2s;
	letter-spacing: 0.05em;
}
.nav-link:hover { color: #10B981; }
.nav-actions { display: flex; gap: 0.75rem; }

.btn-primary-sm {
	padding: 0.4rem 1rem;
	background: #10B981;
	color: #020617;
	font-size: 0.8rem;
	font-weight: 600;
	border-radius: 6px;
	text-decoration: none;
	transition: all 0.2s;
}
.btn-primary-sm:hover { background: #34d399; transform: translateY(-1px); }
.btn-secondary-sm {
	padding: 0.4rem 1rem;
	border: 1px solid rgba(16,185,129,0.4);
	color: #10B981;
	font-size: 0.8rem;
	border-radius: 6px;
	text-decoration: none;
	transition: all 0.2s;
}
.btn-secondary-sm:hover { border-color: #10B981; background: rgba(16,185,129,0.1); }

/* ─── HERO ─── */
.hero-section {
	position: relative;
	z-index: 10;
	min-height: 100vh;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 8rem 2rem 4rem;
}
.hero-content {
	max-width: 860px;
	text-align: center;
}

/* Badge */
.hero-badge {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
	padding: 0.4rem 1rem;
	border: 1px solid rgba(16,185,129,0.35);
	border-radius: 999px;
	font-size: 0.75rem;
	color: #10B981;
	margin-bottom: 2rem;
	background: rgba(16,185,129,0.05);
	letter-spacing: 0.05em;
}
.badge-dot {
	width: 6px; height: 6px;
	border-radius: 50%;
	background: #10B981;
	animation: pulse 2s infinite;
}
@keyframes pulse {
	0%,100% { box-shadow: 0 0 0 0 rgba(16,185,129,0.4); }
	50%       { box-shadow: 0 0 0 6px rgba(16,185,129,0); }
}

/* Headline */
.hero-headline {
	font-size: clamp(2rem, 5vw, 3.75rem);
	font-weight: 800;
	line-height: 1.15;
	letter-spacing: -0.02em;
	margin-bottom: 1.5rem;
}
.headline-line { display: block; }
.accent-emerald { color: #10B981; }
.accent-blue    { color: #3B82F6; }

/* Sub */
.hero-sub {
	font-size: 1.1rem;
	color: #94a3b8;
	line-height: 1.7;
	margin-bottom: 1.5rem;
}

/* Typewriter */
.typewriter-wrap {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
	font-size: 0.875rem;
	color: #64748b;
	margin-bottom: 2.5rem;
}
.tw-prefix { color: #475569; }
.tw-text { color: #10B981; min-width: 12ch; }
.tw-cursor {
	color: #10B981;
	animation: blink 1s step-end infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* CTA Buttons */
.hero-cta {
	display: flex;
	gap: 1rem;
	justify-content: center;
	flex-wrap: wrap;
	margin-bottom: 2rem;
}
.btn-glow {
	display: inline-flex;
	align-items: center;
	padding: 0.75rem 1.75rem;
	background: #10B981;
	color: #020617;
	font-weight: 700;
	font-size: 0.95rem;
	border-radius: 8px;
	text-decoration: none;
	transition: all 0.2s;
	box-shadow: 0 0 20px rgba(16,185,129,0.4);
	cursor: pointer;
}
.btn-glow:hover {
	background: #34d399;
	box-shadow: 0 0 30px rgba(16,185,129,0.6);
	transform: translateY(-2px) scale(1.02);
}
.btn-glow:active { transform: translateY(0) scale(0.98); }
.btn-outline {
	display: inline-flex;
	align-items: center;
	padding: 0.75rem 1.75rem;
	border: 1px solid rgba(59,130,246,0.5);
	color: #3B82F6;
	font-weight: 600;
	font-size: 0.95rem;
	border-radius: 8px;
	text-decoration: none;
	transition: all 0.2s;
	cursor: pointer;
}
.btn-outline:hover {
	border-color: #3B82F6;
	background: rgba(59,130,246,0.1);
	box-shadow: 0 0 20px rgba(59,130,246,0.2);
	transform: translateY(-2px);
}
.btn-outline:active { transform: translateY(0); }

/* Tech tags */
.tech-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 0.5rem;
	justify-content: center;
}
.tech-tag {
	padding: 0.25rem 0.75rem;
	border: 1px solid rgba(99,102,241,0.3);
	border-radius: 999px;
	font-size: 0.7rem;
	color: #818cf8;
	background: rgba(99,102,241,0.06);
}

/* Scroll indicator */
.scroll-indicator {
	position: absolute;
	bottom: 2rem;
	left: 50%;
	transform: translateX(-50%);
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.5rem;
	opacity: 0.6;
}
.scroll-line {
	width: 1px;
	height: 40px;
	background: linear-gradient(to bottom, #10B981, transparent);
	animation: scrollPulse 2s ease-in-out infinite;
}
@keyframes scrollPulse {
	0%,100% { opacity: 0.3; transform: scaleY(1); }
	50% { opacity: 1; transform: scaleY(1.2); }
}

/* ─── SECTIONS ─── */
.section-dark   { background: #020617; position: relative; z-index: 10; padding: 6rem 0; }
.section-darker { background: #040d1a; position: relative; z-index: 10; padding: 6rem 0; }

.section-header { text-align: center; margin-bottom: 4rem; }
.section-tag {
	font-size: 0.75rem;
	color: #10B981;
	letter-spacing: 0.15em;
	display: block;
	margin-bottom: 1rem;
}
.section-title {
	font-size: clamp(1.75rem, 3vw, 2.75rem);
	font-weight: 800;
	letter-spacing: -0.02em;
	margin-bottom: 1rem;
}
.section-desc { color: #64748b; font-size: 1rem; max-width: 540px; margin: 0 auto; }

/* ─── BENTO GRID ─── */
.bento-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	grid-template-rows: auto auto;
	gap: 1.25rem;
}
.bento-card {
	position: relative;
	background: rgba(15, 23, 42, 0.8);
	border: 1px solid rgba(255,255,255,0.06);
	border-radius: 16px;
	padding: 2rem;
	overflow: hidden;
	transition: transform 0.3s, border-color 0.3s;
	cursor: default;
}
.bento-card:hover {
	transform: translateY(-4px);
	border-color: var(--accent, #10B981);
}
.bento-card:hover .bento-glow {
	opacity: 1;
}
.bento-large { grid-column: span 2; }
.bento-medium { grid-column: span 1; }

.bento-icon { font-size: 2rem; margin-bottom: 0.75rem; }
.bento-tag {
	font-size: 0.65rem;
	color: var(--accent, #10B981);
	letter-spacing: 0.15em;
	margin-bottom: 0.75rem;
	display: block;
}
.bento-title {
	font-size: 1.2rem;
	font-weight: 700;
	margin-bottom: 0.75rem;
	color: #f1f5f9;
}
.bento-desc {
	font-size: 0.875rem;
	color: #64748b;
	line-height: 1.65;
	margin-bottom: 1.25rem;
}
.bento-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.bento-chip {
	padding: 0.2rem 0.6rem;
	border: 1px solid rgba(255,255,255,0.08);
	border-radius: 4px;
	font-size: 0.65rem;
	color: #94a3b8;
}
.bento-glow {
	position: absolute;
	inset: 0;
	border-radius: inherit;
	opacity: 0;
	transition: opacity 0.4s;
	background: radial-gradient(ellipse at 50% 0%, rgba(16,185,129,0.08), transparent 70%);
	pointer-events: none;
}

/* ─── PROJECTS ─── */
.projects-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
	gap: 1.5rem;
}
.project-card {
	position: relative;
	background: rgba(15,23,42,0.6);
	border: 1px solid rgba(255,255,255,0.06);
	border-radius: 16px;
	padding: 2rem;
	overflow: hidden;
	transition: all 0.3s;
	cursor: default;
}
.project-card:hover {
	border-color: var(--card-accent, #10B981);
	transform: translateY(-6px);
	box-shadow: 0 20px 40px rgba(0,0,0,0.4);
}
.project-card:hover .project-glow { opacity: 1; }
.project-glow {
	position: absolute;
	inset: 0;
	opacity: 0;
	transition: opacity 0.4s;
	background: radial-gradient(ellipse at 50% 0%, rgba(var(--card-accent-rgb, 16,185,129), 0.07), transparent 65%);
	pointer-events: none;
}
.project-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 1rem;
}
.project-icon { font-size: 1.75rem; }
.project-status {
	font-size: 0.65rem;
	padding: 0.2rem 0.6rem;
	border-radius: 999px;
	letter-spacing: 0.1em;
}
.status-live { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid rgba(16,185,129,0.3); }
.status-beta { background: rgba(59,130,246,0.15); color: #3B82F6; border: 1px solid rgba(59,130,246,0.3); }
.project-title {
	font-size: 1.1rem;
	font-weight: 700;
	color: #f1f5f9;
	margin-bottom: 0.75rem;
}
.project-desc {
	font-size: 0.875rem;
	color: #64748b;
	line-height: 1.65;
	margin-bottom: 1.25rem;
}
.project-stack { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1.25rem; }
.stack-chip {
	padding: 0.2rem 0.5rem;
	background: rgba(255,255,255,0.04);
	border: 1px solid rgba(255,255,255,0.08);
	border-radius: 4px;
	font-size: 0.65rem;
	color: #94a3b8;
}
.project-footer {
	display: flex;
	align-items: center;
	justify-content: space-between;
	border-top: 1px solid rgba(255,255,255,0.05);
	padding-top: 1rem;
}
.project-field { font-size: 0.7rem; color: var(--card-accent, #10B981); }
.project-arrow {
	color: var(--card-accent, #10B981);
	font-size: 1.1rem;
	transition: transform 0.2s;
}
.project-card:hover .project-arrow { transform: translateX(4px); }

/* ─── STATS ─── */
.stats-section { border-top: 1px solid rgba(16,185,129,0.15); border-bottom: 1px solid rgba(16,185,129,0.15); }
.stats-grid {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 1.5rem;
	margin-bottom: 4rem;
}
.stat-card {
	text-align: center;
	padding: 2rem 1rem;
	background: rgba(15,23,42,0.5);
	border: 1px solid rgba(255,255,255,0.06);
	border-radius: 12px;
	position: relative;
	overflow: hidden;
}
.stat-card::before {
	content: '';
	position: absolute;
	top: 0; left: 50%;
	transform: translateX(-50%);
	width: 60%;
	height: 1px;
	background: linear-gradient(to right, transparent, #10B981, transparent);
}
.stat-num {
	font-size: 2.75rem;
	font-weight: 700;
	color: #10B981;
	line-height: 1;
	margin-bottom: 0.5rem;
}
.stat-suffix { font-size: 2rem; }
.stat-label { font-size: 0.875rem; color: #64748b; }
.stat-icon { font-size: 1.5rem; margin-top: 0.75rem; opacity: 0.6; }

/* Timeline */
.timeline {
	display: flex;
	gap: 0;
	position: relative;
	padding: 0 1rem;
}
.timeline::before {
	content: '';
	position: absolute;
	top: 10px;
	left: 1rem; right: 1rem;
	height: 1px;
	background: linear-gradient(to right, transparent, #10B981 20%, #3B82F6 80%, transparent);
}
.timeline-item {
	flex: 1;
	position: relative;
	padding-top: 2.5rem;
	padding-right: 1rem;
}
.timeline-dot {
	position: absolute;
	top: 4px;
	left: 0;
	width: 14px; height: 14px;
	border-radius: 50%;
	background: #10B981;
	border: 2px solid #020617;
	box-shadow: 0 0 10px rgba(16,185,129,0.5);
}
.timeline-year {
	font-size: 0.75rem;
	color: #10B981;
	display: block;
	margin-bottom: 0.5rem;
}
.timeline-text { font-size: 0.8rem; color: #64748b; line-height: 1.5; }

/* ─── JOIN ─── */
.join-section { }
.join-card {
	position: relative;
	background: rgba(15,23,42,0.6);
	border: 1px solid rgba(16,185,129,0.2);
	border-radius: 24px;
	padding: 4rem 3rem;
	text-align: center;
	overflow: hidden;
}
.join-bg-text {
	position: absolute;
	font-size: 12rem;
	font-weight: 900;
	color: rgba(16,185,129,0.03);
	top: 50%; left: 50%;
	transform: translate(-50%,-50%);
	pointer-events: none;
	user-select: none;
	white-space: nowrap;
}
.join-title {
	font-size: clamp(1.75rem, 3vw, 2.5rem);
	font-weight: 800;
	margin: 1rem 0 1.5rem;
}
.join-desc {
	color: #64748b;
	font-size: 1rem;
	line-height: 1.7;
	margin-bottom: 2rem;
}
.join-requirements {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 0.75rem;
	max-width: 560px;
	margin: 0 auto 2.5rem;
	text-align: left;
}
.req-item {
	display: flex;
	align-items: flex-start;
	gap: 0.5rem;
	font-size: 0.875rem;
	color: #94a3b8;
}
.req-check { color: #10B981; font-weight: 700; flex-shrink: 0; }
.join-cta {
	display: flex;
	gap: 1rem;
	justify-content: center;
	flex-wrap: wrap;
}

/* ─── DASHBOARD ─── */
.dashboard-section { }
.dashboard-links {
	display: grid;
	grid-template-columns: repeat(5, 1fr);
	gap: 1rem;
}
.dash-link {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.75rem;
	padding: 1.5rem 1rem;
	background: rgba(15,23,42,0.5);
	border: 1px solid rgba(255,255,255,0.06);
	border-radius: 12px;
	text-decoration: none;
	color: #94a3b8;
	font-size: 0.875rem;
	transition: all 0.2s;
}
.dash-link:hover {
	border-color: #10B981;
	color: #10B981;
	background: rgba(16,185,129,0.08);
	transform: translateY(-3px);
}
.dash-icon { font-size: 1.75rem; }
.dash-arrow { font-size: 0.75rem; opacity: 0.5; }

/* ─── FOOTER ─── */
.aiit-footer {
	background: #040d1a;
	border-top: 1px solid rgba(255,255,255,0.05);
	padding: 3rem 0;
	position: relative;
	z-index: 10;
}
.footer-inner {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 2rem;
	flex-wrap: wrap;
}
.footer-logo {
	display: flex;
	align-items: center;
	gap: 0.25rem;
	font-family: 'JetBrains Mono', monospace;
	font-weight: 700;
	font-size: 1.1rem;
}
.footer-desc {
	font-size: 0.75rem;
	color: #475569;
	line-height: 1.6;
}
.footer-links { display: flex; gap: 1.5rem; flex-wrap: wrap; }
.footer-link {
	font-size: 0.8rem;
	color: #475569;
	text-decoration: none;
	transition: color 0.2s;
}
.footer-link:hover { color: #10B981; }

/* ─── SCROLL REVEAL ─── */
.reveal {
	opacity: 0;
	transform: translateY(24px);
	transition: opacity 0.7s ease, transform 0.7s ease;
}
.reveal.revealed { opacity: 1; transform: translateY(0); }
.reveal-delay-1 { transition-delay: 0.1s; }
.reveal-delay-2 { transition-delay: 0.2s; }
.reveal-delay-3 { transition-delay: 0.3s; }
.reveal-delay-4 { transition-delay: 0.4s; }

/* ─── RESPONSIVE ─── */
@media (max-width: 900px) {
	.bento-grid { grid-template-columns: 1fr 1fr; }
	.bento-large { grid-column: span 2; }
	.stats-grid { grid-template-columns: repeat(2, 1fr); }
	.dashboard-links { grid-template-columns: repeat(3, 1fr); }
	.nav-links { display: none; }
	.timeline { flex-direction: column; gap: 1.5rem; }
	.timeline::before { display: none; }
	.timeline-dot { top: 0; }
	.timeline-item { padding-top: 0; padding-left: 2rem; }
}
@media (max-width: 600px) {
	.bento-grid { grid-template-columns: 1fr; }
	.bento-large, .bento-medium { grid-column: span 1; }
	.stats-grid { grid-template-columns: repeat(2, 1fr); }
	.dashboard-links { grid-template-columns: repeat(2, 1fr); }
	.join-requirements { grid-template-columns: 1fr; }
	.hero-section { padding: 7rem 1rem 3rem; }
	.section-dark, .section-darker { padding: 4rem 0; }
	.footer-inner { flex-direction: column; text-align: center; }
}
</style>
