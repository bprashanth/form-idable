<template>
  <div class="flex h-screen w-full overflow-hidden bg-surface font-body text-on-surface">
    <aside class="hidden md:flex flex-col h-full py-6 px-4 bg-surface-container-low w-64 shrink-0 border-r border-outline-variant/20">
      <div class="mb-8 px-2 flex items-center gap-3">
        <div class="w-8 h-8 bg-primary flex items-center justify-center rounded-sm shrink-0">
          <span class="material-symbols-outlined text-on-primary text-sm">dynamic_form</span>
        </div>
        <div><h1 class="font-headline font-black text-lg text-primary leading-none tracking-tighter">FORMIDABLE</h1>
          <p class="text-[10px] uppercase tracking-widest text-on-surface-variant mt-0.5">Form Processing Engine</p></div>
      </div>
      <nav class="flex-1 space-y-1">
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high cursor-pointer"
           @click="router.push('/dashboard')"><span class="material-symbols-outlined">dashboard</span><span>Dashboard</span></a>
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high cursor-pointer"
           @click="router.push({ name: 'job-review', params: { jobId } })"><span class="material-symbols-outlined">find_in_page</span><span>Review</span></a>
        <a class="flex items-center gap-3 px-3 py-2 text-primary font-bold bg-surface-container-highest rounded-sm">
          <span class="material-symbols-outlined">analytics</span><span>Analytics</span></a>
      </nav>
    </aside>

    <main class="flex-1 overflow-y-auto">
      <header class="sticky top-0 z-20 flex items-center justify-between px-7 py-4 border-b border-outline-variant/20 bg-surface-container-lowest">
        <div><p class="text-[10px] uppercase tracking-[0.2em] text-error font-black">High effort · read only</p>
          <h2 class="font-headline font-black text-2xl text-primary">Form distributions</h2>
          <p class="text-[10px] font-mono text-outline mt-1">{{ jobId }}</p></div>
        <button class="px-4 py-2 border border-outline-variant/40 text-xs font-black text-primary"
                @click="router.push({ name: 'job-review', params: { jobId } })">BACK TO REVIEW</button>
      </header>

      <div v-if="loading" class="p-10 text-on-surface-variant">Building distribution view…</div>
      <div v-else-if="!analytics" class="m-8 border border-outline-variant/30 bg-surface-container-low p-8 max-w-xl">
        <span class="material-symbols-outlined text-3xl text-outline">lock</span>
        <h3 class="font-headline font-black text-xl text-primary mt-3">Analytics requires High effort</h3>
        <p class="text-sm text-on-surface-variant mt-2">Low jobs retain the original review flow and do not create ecology or distribution artifacts.</p>
      </div>
      <div v-else class="p-7 space-y-7" data-testid="analytics-view">
        <section class="grid grid-cols-2 lg:grid-cols-5 gap-3">
          <SummaryCard label="Pages" :value="analytics.summary.pages" />
          <SummaryCard label="Cells mapped" :value="analytics.summary.cells" />
          <SummaryCard label="Filled" :value="analytics.summary.filled" />
          <SummaryCard label="Transcription alerts" :value="analytics.summary.disagreements" tone="red" />
          <SummaryCard label="Ecology flags" :value="analytics.summary.ecology_findings" tone="orange" />
        </section>

        <section>
          <div class="flex items-end justify-between mb-3"><div><p class="eyebrow">Review load by page</p>
            <h3 class="section-title">Where attention is concentrated</h3></div>
            <p class="text-[10px] text-on-surface-variant">Red = transcription · orange = ecology</p></div>
          <div class="grid md:grid-cols-2 xl:grid-cols-3 gap-3">
            <div v-for="page in analytics.pages" :key="page.page" class="chart-card">
              <div class="flex justify-between"><span class="font-black text-primary">Page {{ page.page }}</span><span class="font-mono text-xs">{{ page.filled }}/{{ page.cells }} filled</span></div>
              <div class="h-2 flex mt-4 bg-surface-container-highest overflow-hidden">
                <div class="bg-error" :style="{ width: percent(page.disagreements, page.cells) }" />
                <div class="bg-orange-500" :style="{ width: percent(page.ecology_flags, page.cells) }" />
              </div>
              <p class="text-[10px] text-on-surface-variant mt-2">{{ page.disagreements }} disputes · {{ page.ecology_flags }} ecology flags</p>
            </div>
          </div>
        </section>

        <section v-if="numericCharts.length">
          <p class="eyebrow">Numeric distributions</p><h3 class="section-title mb-3">Shape, centre and unusual tails</h3>
          <div class="grid lg:grid-cols-2 gap-4">
            <article v-for="chart in numericCharts" :key="chart.label" class="chart-card" data-testid="numeric-chart">
              <div class="flex justify-between gap-4"><h4 class="font-black text-primary truncate">{{ chart.label }}</h4><span class="font-mono text-[10px]">n={{ chart.n }}</span></div>
              <div class="h-24 flex items-end gap-1 mt-5 border-b border-outline-variant/30">
                <div v-for="(bin, index) in chart.histogram" :key="index" class="flex-1 bg-secondary/65 hover:bg-secondary transition-colors" :style="{ height: barHeight(bin.count, chart.histogram) }" :title="`${bin.x0}–${bin.x1}: ${bin.count}`" />
              </div>
              <div class="relative h-7 mt-3"><div class="absolute top-3 h-px bg-outline left-0 right-0" />
                <div class="absolute top-1 h-5 border-2 border-primary bg-primary/10" :style="boxStyle(chart)" />
                <div class="absolute top-0 h-7 w-0.5 bg-error" :style="{ left: scale(chart.median, chart) }" /></div>
              <div class="flex justify-between text-[9px] font-mono text-outline"><span>{{ format(chart.min) }}</span><span>median {{ format(chart.median) }}</span><span>{{ format(chart.max) }}</span></div>
            </article>
          </div>
        </section>

        <section v-if="categoricalCharts.length">
          <p class="eyebrow">Categorical distributions</p><h3 class="section-title mb-3">Dominant and rare recorded states</h3>
          <div class="grid lg:grid-cols-2 gap-4">
            <article v-for="chart in categoricalCharts" :key="chart.label" class="chart-card" data-testid="categorical-chart">
              <div class="flex justify-between"><h4 class="font-black text-primary truncate">{{ chart.label }}</h4><span class="font-mono text-[10px]">n={{ chart.n }}</span></div>
              <div class="space-y-2 mt-4"><div v-for="item in chart.values" :key="item.label" class="grid grid-cols-[7rem_1fr_2rem] items-center gap-2 text-xs">
                <span class="truncate" :title="item.label">{{ item.label }}</span><div class="h-3 bg-surface-container-highest"><div class="h-full bg-primary" :style="{ width: percent(item.count, chart.values[0].count) }" /></div><span class="font-mono text-right">{{ item.count }}</span></div></div>
            </article>
          </div>
        </section>

        <section v-if="actionableEcology.length">
          <p class="eyebrow text-orange-700">Ecology observations</p><h3 class="section-title mb-3">Investigate; do not auto-correct</h3>
          <div class="grid lg:grid-cols-2 gap-3"><article v-for="(item, index) in actionableEcology" :key="index" class="border-l-4 border-orange-500 bg-orange-50 p-4">
            <div class="flex justify-between"><strong class="text-sm">{{ item.label || item.code }}</strong><span class="text-[9px] uppercase font-black text-orange-700">{{ item.severity }}</span></div>
            <p class="text-xs mt-2">{{ item.message }}</p><p class="text-[10px] text-on-surface-variant mt-2">Observed {{ item.observed ?? '—' }} · Page {{ item.location?.page ?? '—' }}</p>
          </article></div>
        </section>

        <details v-if="informationalEcology.length" class="border border-outline-variant/25 bg-surface-container-lowest p-4">
          <summary class="cursor-pointer text-xs font-black text-primary">
            {{ informationalEcology.length }} informational ecology checks — not in the review queue
          </summary>
          <p class="text-[10px] text-on-surface-variant mt-2">Grouped context only. A failed catalogue lookup is not treated as a bad field value.</p>
          <div class="grid lg:grid-cols-2 gap-3 mt-4">
            <article v-for="group in ecologyInfoGroups" :key="group.code" class="bg-surface-container-low p-3">
              <div class="flex justify-between gap-3"><strong class="text-xs">{{ group.label }}</strong><span class="font-mono text-[10px]">{{ group.count }}</span></div>
              <p class="text-[10px] text-on-surface-variant mt-2">Examples: {{ group.examples.join(' · ') }}</p>
            </article>
          </div>
        </details>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useJobStore } from '@/composables/useJobStore.js'
import SummaryCard from '@/components/SummaryCard.vue'

const route = useRoute(); const router = useRouter(); const jobId = route.params.jobId
const { fetchAnalytics } = useJobStore(); const analytics = ref(null); const loading = ref(true)
onMounted(async () => { try { analytics.value = await fetchAnalytics(jobId) } finally { loading.value = false } })
const numericCharts = computed(() => (analytics.value?.charts ?? []).filter(item => item.type === 'numeric').slice(0, 12))
const categoricalCharts = computed(() => (analytics.value?.charts ?? []).filter(item => item.type === 'categorical').slice(0, 12))
const actionableEcology = computed(() => (analytics.value?.ecology_findings ?? [])
  .filter(item => ['medium', 'high'].includes(item.severity)))
const informationalEcology = computed(() => (analytics.value?.ecology_findings ?? [])
  .filter(item => !['medium', 'high'].includes(item.severity)))
const ecologyInfoGroups = computed(() => {
  const groups = new Map()
  for (const item of informationalEcology.value) {
    const code = item.code || 'context'
    const group = groups.get(code) || { code, label: code.replaceAll('_', ' '), count: 0, examples: [] }
    group.count += 1
    const example = String(item.observed ?? '').trim()
    if (example && group.examples.length < 3 && !group.examples.includes(example)) group.examples.push(example)
    groups.set(code, group)
  }
  return [...groups.values()].sort((a, b) => b.count - a.count)
})
function percent(value, total) { return `${Math.min(100, total ? value / total * 100 : 0)}%` }
function barHeight(value, bins) { return `${Math.max(4, value / Math.max(...bins.map(bin => bin.count), 1) * 100)}%` }
function scale(value, chart) { return percent(value - chart.min, chart.max - chart.min) }
function boxStyle(chart) { return { left: scale(chart.q1, chart), width: percent(chart.q3 - chart.q1, chart.max - chart.min) } }
function format(value) { return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 }) }
</script>

<style scoped>
.eyebrow { @apply text-[10px] uppercase tracking-[0.18em] font-black text-on-surface-variant; }
.section-title { @apply font-headline font-black text-xl text-primary; }
.chart-card { @apply border border-outline-variant/25 bg-surface-container-lowest p-4 shadow-sm; }
</style>
