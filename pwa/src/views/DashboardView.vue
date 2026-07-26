<template>
  <div class="flex h-screen w-full overflow-hidden bg-surface font-body text-on-surface">

    <!-- Sidebar -->
    <aside class="flex flex-col h-full py-6 px-4 bg-surface-container-low w-64 shrink-0 border-r border-outline-variant/20">
      <div class="mb-8 px-2 flex items-center gap-3">
        <img :src="'/logo.png'" class="w-8 h-8 shrink-0 border-[3px] border-black rounded-sm" alt="Formidable" />
        <div>
          <h1 class="font-headline font-black text-lg text-primary leading-none tracking-tighter">FORMIDABLE</h1>
          <p class="text-[10px] uppercase tracking-widest text-on-surface-variant mt-0.5">Form Processing Engine</p>
        </div>
      </div>
      <nav class="flex-1 space-y-1">
        <a class="flex items-center gap-3 px-3 py-2 text-primary font-bold bg-surface-container-highest rounded-sm">
          <span class="material-symbols-outlined">dashboard</span>
          <span>Dashboard</span>
        </a>
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer">
          <span class="material-symbols-outlined">architecture</span>
          <span>Form Builder</span>
        </a>
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer">
          <span class="material-symbols-outlined">analytics</span>
          <span>Analyse</span>
        </a>
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer">
          <span class="material-symbols-outlined">hub</span>
          <span>Share</span>
        </a>
      </nav>
      <div class="pt-4 border-t border-outline-variant/20 space-y-1">
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer">
          <span class="material-symbols-outlined">help</span>
          <span>Help Center</span>
        </a>
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer"
           @click="handleLogout">
          <span class="material-symbols-outlined">logout</span>
          <span>Log Out</span>
        </a>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 flex flex-col min-w-0 overflow-y-auto">

      <!-- Header -->
      <header class="flex justify-between items-center px-6 py-3 border-b border-outline-variant/20 bg-surface-container-lowest sticky top-0 z-40"
              style="box-shadow: 0 8px 32px rgba(11,28,48,0.06)">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1.5 bg-surface-container rounded-sm w-72">
            <span class="material-symbols-outlined text-outline text-sm">search</span>
            <input class="bg-transparent border-none focus:ring-0 text-sm w-full p-0" placeholder="Search surveys..." />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="p-2 text-on-surface-variant hover:bg-surface-container-low rounded-sm">
            <span class="material-symbols-outlined">notifications</span>
          </button>
          <button class="p-2 text-on-surface-variant hover:bg-surface-container-low rounded-sm">
            <span class="material-symbols-outlined">settings</span>
          </button>
        </div>
      </header>

      <!-- Map -->
      <div class="relative w-full flex-1 min-h-[40vh] max-h-[55vh] bg-surface-container-highest">
        <div ref="mapContainer" class="w-full h-full" data-testid="map" />
        <div class="absolute bottom-4 left-4 px-4 py-2 border border-outline-variant/20 bg-white/80 backdrop-blur-sm flex gap-6 items-center z-10 pointer-events-none">
          <div class="flex flex-col">
            <span class="text-[10px] uppercase tracking-tighter text-on-surface-variant font-bold">Region</span>
            <span class="text-sm font-bold text-primary">Western Ghats</span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] uppercase tracking-tighter text-on-surface-variant font-bold">Survey Sites</span>
            <span class="text-sm font-bold text-primary">{{ jobs.filter(j => j.gps).length }}</span>
          </div>
        </div>
      </div>

      <!-- Your Forms -->
      <div class="pb-20">
        <div class="flex justify-between items-center px-6 py-4 border-b border-outline-variant/10">
          <h3 class="font-headline font-bold text-xl text-primary">Your Forms</h3>

          <div v-if="!selectMode" class="flex items-center gap-2">
            <!-- Trash — enters select mode -->
            <button
              data-testid="trash-btn"
              class="flex items-center gap-1.5 px-3 py-2 border border-outline-variant/40 text-on-surface-variant hover:bg-error-container hover:text-error hover:border-error/40 transition-colors rounded-sm"
              title="Select and delete forms"
              @click="enterSelectMode"
            >
              <span class="material-symbols-outlined text-sm">delete</span>
            </button>
            <!-- Add Forms — opens modal -->
            <button
              data-testid="add-forms-btn"
              class="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary font-bold text-xs rounded-sm"
              @click="openUploadModal"
            >
              <span class="material-symbols-outlined text-sm">upload_file</span> Add Forms
            </button>
            <!-- Retry file picker (single file, hidden, used only by handleRetryClick) -->
            <input
              ref="fileInput"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              class="hidden"
              @change="handleFileUpload"
            />
          </div>

          <!-- Select-mode action bar -->
          <div v-else class="flex items-center gap-3">
            <span class="text-xs text-on-surface-variant">
              {{ selectedIds.size }} selected
            </span>
            <button
              class="px-3 py-1.5 text-xs font-bold text-on-surface-variant border border-outline-variant/40 hover:bg-surface-container transition-colors rounded-sm"
              @click="cancelSelectMode"
            >
              Cancel
            </button>
            <button
              data-testid="delete-selected-btn"
              class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-error border border-error/40 hover:bg-error-container transition-colors rounded-sm disabled:opacity-40"
              :disabled="selectedIds.size === 0 || deleting"
              @click="deleteSelected"
            >
              <span v-if="deleting" class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
              <span v-else class="material-symbols-outlined text-sm">delete</span>
              Delete {{ selectedIds.size > 0 ? selectedIds.size : '' }} selected
            </button>
          </div>
        </div>

        <div v-if="jobsLoading" class="text-on-surface-variant text-sm px-6 py-8">Loading…</div>

        <div v-else class="w-full overflow-x-auto" data-testid="submission-log">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-container-low">
                <th v-if="selectMode" class="py-3 px-4 w-10 border-b border-outline-variant/20"></th>
                <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/20">Preview</th>
                <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/20">Form Metadata</th>
                <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/20">Processing Status</th>
                <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/20">Review State</th>
                <th class="py-3 px-6 text-[10px] font-black uppercase tracking-widest text-on-surface-variant border-b border-outline-variant/20 text-right">Download</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-variant/10">
              <tr
                v-for="job in jobs"
                :key="job.job_id"
                class="hover:bg-surface-container-low transition-colors cursor-pointer"
                :class="{ 'bg-primary/5': selectedIds.has(job.job_id) }"
                :data-testid="`job-row-${job.job_id}`"
                @click="handleRowClick(job)"
              >
                <!-- Checkbox in select mode — @click.stop prevents row nav; @change drives selection -->
                <td v-if="selectMode" class="py-3 px-4 w-10" @click.stop>
                  <input
                    type="checkbox"
                    :checked="selectedIds.has(job.job_id)"
                    :data-testid="`select-${job.job_id}`"
                    class="w-4 h-4 accent-primary cursor-pointer"
                    @change="toggleSelect(job.job_id)"
                  />
                </td>
                <!-- Thumbnail -->
                <td class="py-3 px-6" @click.stop="selectMode ? toggleSelect(job.job_id) : (['queued','processing','uploading'].includes(job.status) ? handleRowClick(job) : openLightbox(job))">
                  <div class="w-10 h-14 bg-surface-container-highest border border-outline-variant/40 flex items-center justify-center overflow-hidden hover:border-primary/60 transition-colors group relative">
                    <img
                      :src="thumbnailUrls[job.job_id]"
                      class="w-full h-full object-cover opacity-70 grayscale group-hover:opacity-90 group-hover:grayscale-0 transition-all"
                      :alt="job.name"
                    />
                    <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/20 transition-opacity">
                      <span class="material-symbols-outlined text-white text-sm">zoom_in</span>
                    </div>
                  </div>
                </td>
                <td class="py-3 px-6">
                  <div class="flex flex-col gap-0.5">
                    <span class="font-bold text-primary">{{ job.name }}</span>
                    <span class="text-[10px] text-on-surface-variant">{{ job.pages }} pages · {{ job.crops }} crops</span>
                    <span v-if="job.date" class="text-[10px] text-on-surface-variant">{{ job.date }}</span>
                    <span class="text-[10px] font-mono text-outline/60 tracking-tight">id: {{ job.job_id }}</span>
                  </div>
                </td>
                <td class="py-3 px-6">
                  <div v-if="job.status === 'complete'"
                       class="inline-flex items-center gap-2 px-2 py-1 bg-secondary-container text-on-secondary-container text-[10px] font-bold rounded-full">
                    <span class="w-1.5 h-1.5 bg-secondary rounded-full"></span> Processed
                  </div>
                  <div v-else-if="job.status === 'uploading' && uploadErrors[job.job_id]"
                       class="inline-flex items-center gap-2 px-2 py-1 bg-error-container text-error text-[10px] font-bold rounded-full">
                    <span class="w-1.5 h-1.5 bg-error rounded-full"></span> Upload failed
                  </div>
                  <div v-else class="inline-flex items-center gap-2 px-2 py-1 bg-surface-container-highest text-on-surface-variant text-[10px] font-bold rounded-full">
                    <span v-if="job.status === 'uploading'" class="material-symbols-outlined text-[10px] animate-spin">progress_activity</span>
                    <span v-else class="w-1.5 h-1.5 bg-outline rounded-full"></span>
                    {{ job.status === 'uploading' ? 'Uploading…' : job.status }}
                  </div>
                </td>
                <td class="py-3 px-6">
                  <div v-if="job.review_state === 'reviewed'"
                       class="flex items-center gap-2 text-on-surface-variant font-medium text-sm">
                    <span class="material-symbols-outlined text-secondary text-lg">check_circle</span> Reviewed
                  </div>
                  <div v-else class="flex items-center gap-2 text-on-surface-variant font-medium text-sm">
                    <span class="material-symbols-outlined text-outline text-lg">radio_button_unchecked</span> Unreviewed
                  </div>
                </td>
                <td class="py-3 px-6 text-right" @click.stop>
                  <button
                    v-if="job.status === 'failed'"
                    class="flex items-center gap-1.5 ml-auto border border-error/40 px-3 py-1.5 text-xs font-bold text-error hover:bg-error-container transition-colors"
                    @click="rerunJob(job)"
                  >
                    <span class="material-symbols-outlined text-sm">refresh</span>
                    Rerun
                  </button>
                  <div
                    v-else-if="job.status === 'queued' || job.status === 'processing'"
                    class="flex items-center gap-1.5 ml-auto text-xs text-on-surface-variant"
                  >
                    <span class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                    {{ job.status }}
                  </div>
                  <template v-else-if="job.status === 'uploading'">
                    <button
                      v-if="uploadErrors[job.job_id]"
                      class="flex items-center gap-1.5 ml-auto border border-primary/40 px-3 py-1.5 text-xs font-bold text-primary hover:bg-primary/10 transition-colors"
                      @click.stop="handleRetryClick(job)"
                    >
                      <span class="material-symbols-outlined text-sm">refresh</span>
                      Retry
                    </button>
                    <div v-else class="flex items-center gap-1.5 ml-auto text-xs text-on-surface-variant">
                      <span class="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                      Uploading
                    </div>
                  </template>
                  <button
                    v-else
                    class="flex items-center gap-1.5 ml-auto border border-outline-variant/40 px-3 py-1.5 text-xs font-bold text-on-surface hover:bg-surface-container transition-colors"
                    @click="downloadXlsx(job)"
                  >
                    <span class="material-symbols-outlined text-sm">download</span>
                    Excel
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <!-- Progress modal (in-progress jobs) -->
    <Teleport to="body">
      <div v-if="progressModal"
           class="fixed inset-0 z-[9998] bg-black/60 flex items-center justify-center"
           @click.self="closeProgressModal">
        <div class="relative w-full max-w-md mx-4 bg-surface border border-outline-variant/20 shadow-2xl"
             style="box-shadow: 0 24px 64px rgba(11,28,48,0.18)">
          <!-- Header -->
          <div class="flex justify-between items-start px-6 pt-5 pb-4 border-b border-outline-variant/10">
            <div class="flex flex-col gap-1 min-w-0 pr-4">
              <span class="font-headline font-bold text-primary text-base leading-snug truncate">
                {{ progressModal.name }}
              </span>
              <div class="flex items-center gap-2">
                <!-- Status badge -->
                <span v-if="progressModal.status === 'complete'"
                      class="inline-flex items-center gap-1.5 px-2 py-0.5 bg-secondary-container text-on-secondary-container text-[10px] font-bold rounded-full">
                  <span class="w-1.5 h-1.5 bg-secondary rounded-full"></span> Complete
                </span>
                <span v-else-if="progressModal.status === 'failed'"
                      class="inline-flex items-center gap-1.5 px-2 py-0.5 bg-error-container text-error text-[10px] font-bold rounded-full">
                  <span class="w-1.5 h-1.5 bg-error rounded-full"></span> Failed
                </span>
                <span v-else
                      class="inline-flex items-center gap-1.5 px-2 py-0.5 bg-surface-container-highest text-on-surface-variant text-[10px] font-bold rounded-full">
                  <span class="material-symbols-outlined text-[10px] animate-spin">progress_activity</span>
                  {{ progressModal.status === 'queued' ? 'Queued' : 'Processing' }}
                </span>
              </div>
            </div>
            <button class="text-on-surface-variant hover:text-on-surface mt-0.5 shrink-0" @click="closeProgressModal">
              <span class="material-symbols-outlined text-xl">close</span>
            </button>
          </div>

          <!-- Progress body -->
          <div class="px-6 py-5 flex flex-col gap-4">
            <!-- Bar -->
            <div>
              <div class="flex justify-between items-baseline mb-1.5">
                <span class="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant">Progress</span>
                <span class="text-xs font-bold text-primary tabular-nums">
                  {{ progressModal.status === 'complete' ? 100 : (progressData?.pct ?? 0) }}%
                </span>
              </div>
              <div class="w-full h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                <div class="h-full bg-primary transition-all duration-700 rounded-full"
                     :style="{ width: `${progressModal.status === 'complete' ? 100 : (progressData?.pct ?? 0)}%` }"></div>
              </div>
            </div>

            <!-- Step text -->
            <p class="text-sm text-on-surface min-h-[1.25rem]">
              {{ progressModal.status === 'complete' ? 'Complete' : (progressData?.step ?? 'Waiting for update…') }}
            </p>

            <!-- Error detail (failed jobs) -->
            <p v-if="progressModal.status === 'failed' && progressModal.error"
               class="text-xs text-error font-mono bg-error-container px-3 py-2 leading-relaxed break-all">
              {{ progressModal.error }}
            </p>
          </div>

          <!-- Footer -->
          <div class="flex justify-end gap-2 px-6 pb-5">
            <button
              class="px-4 py-2 text-xs font-bold text-on-surface-variant border border-outline-variant/40 hover:bg-surface-container transition-colors"
              @click="closeProgressModal"
            >
              Close
            </button>
            <button
              v-if="progressModal.status === 'complete'"
              class="px-4 py-2 text-xs font-bold bg-primary text-on-primary hover:opacity-90 transition-opacity"
              @click="closeProgressModal(); openReview(progressModal.job_id)"
            >
              Open Review
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Lightbox -->
    <Teleport to="body">
      <div v-if="lightbox"
           class="fixed inset-0 z-[9999] bg-black/80 flex items-center justify-center"
           @click.self="lightbox = null">
        <div class="relative max-w-3xl max-h-[90vh] mx-4 flex flex-col">
          <div class="flex justify-between items-center mb-3">
            <span class="text-white text-sm font-bold">{{ lightbox.name }}</span>
            <button class="text-white/70 hover:text-white p-1" @click="lightbox = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <img :src="thumbnailUrls[lightbox.job_id]"
               class="max-w-full max-h-[80vh] object-contain"
               :alt="lightbox.name" />
        </div>
      </div>
    </Teleport>

    <!-- Upload Modal -->
    <Teleport to="body">
      <div v-if="uploadModal"
           data-testid="upload-modal"
           class="fixed inset-0 z-[9998] bg-black/60 flex items-center justify-center"
           @click.self="closeUploadModal">
        <div class="relative w-full max-w-md mx-4 bg-surface border border-outline-variant/20 shadow-2xl">
          <div class="flex justify-between items-center px-6 pt-5 pb-4 border-b border-outline-variant/10">
            <span class="font-headline font-bold text-primary text-base">Add Forms</span>
            <button class="text-on-surface-variant hover:text-on-surface" @click="closeUploadModal">
              <span class="material-symbols-outlined text-xl">close</span>
            </button>
          </div>

          <div class="px-6 py-5 flex flex-col gap-4">
            <!-- File drop zone -->
            <div>
              <label class="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant block mb-2">
                Forms (PDF, PNG, JPG)
              </label>
              <div
                class="border-2 border-dashed border-outline-variant/40 hover:border-primary/60 p-6 text-center cursor-pointer transition-colors"
                @click="modalFileInput.click()"
              >
                <span class="material-symbols-outlined text-3xl text-on-surface-variant/40">upload_file</span>
                <p class="text-sm text-on-surface-variant mt-2">Click to select files</p>
                <p class="text-[10px] text-outline/60 mt-1">PDF, PNG, JPG — multiple allowed</p>
              </div>
              <!-- Selected file list -->
              <div v-if="modalSelectedFiles.length > 0" class="mt-2 flex flex-col gap-1">
                <div
                  v-for="(f, i) in modalSelectedFiles"
                  :key="i"
                  class="flex items-center justify-between px-3 py-1.5 bg-surface-container"
                >
                  <span class="truncate text-xs text-on-surface min-w-0">{{ f.name }}</span>
                  <button class="text-on-surface-variant hover:text-error ml-2 shrink-0" @click="removeModalFile(i)">
                    <span class="material-symbols-outlined text-sm">close</span>
                  </button>
                </div>
              </div>
              <input
                ref="modalFileInput"
                data-testid="modal-file-input"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                multiple
                class="hidden"
                @change="handleModalFileSelect"
              />
            </div>

            <!-- Notification email -->
            <div>
              <label class="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant block mb-1">
                Notify when done (optional)
              </label>
              <input
                v-model="notifEmail"
                type="email"
                placeholder="your@email.com"
                class="w-full px-3 py-2 bg-surface-container border border-outline-variant/40 text-sm focus:outline-none focus:border-primary transition-colors"
              />
            </div>
          </div>

          <div class="flex justify-end gap-2 px-6 pb-5">
            <button
              class="px-4 py-2 text-xs font-bold text-on-surface-variant border border-outline-variant/40 hover:bg-surface-container transition-colors"
              @click="closeUploadModal"
            >Cancel</button>
            <button
              data-testid="upload-submit-btn"
              class="px-4 py-2 text-xs font-bold bg-primary text-on-primary hover:opacity-90 transition-opacity disabled:opacity-40"
              :disabled="modalSelectedFiles.length === 0"
              @click="submitUploadModal"
            >
              Upload {{ modalSelectedFiles.length > 1 ? `${modalSelectedFiles.length} forms` : modalSelectedFiles.length === 1 ? '1 form' : '' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toasts -->
    <Teleport to="body">
      <div class="fixed bottom-4 right-4 flex flex-col gap-2 z-[9999] pointer-events-none">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="px-4 py-3 text-sm font-medium shadow-lg max-w-xs"
          :class="toast.type === 'error'
            ? 'bg-error text-on-error'
            : 'bg-primary text-on-primary'"
        >
          {{ toast.message }}
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useJobStore } from '@/composables/useJobStore.js'
import { useCognitoAuth } from '@/composables/useCognitoAuth.js'

const router = useRouter()
const {
  jobs, jobsLoading, fetchJobs, deleteJob, rerunJob: rerunJobApi,
  initUpload, s3Put, startJob, savePendingFile, getPendingFile,
  fetchProgress, pollJob, fetchAuthedUrl, getXlsxUrl, pageUrl,
} = useJobStore()
const { logout } = useCognitoAuth()

const mapContainer       = ref(null)
const lightbox           = ref(null)
const fileInput          = ref(null)
const retryingJobId      = ref(null)
const uploadErrors       = ref({})
const thumbnailUrls      = ref({})
let leafletMap           = null

// ── Upload modal ───────────────────────────────────────────────────────────────
const uploadModal        = ref(false)
const modalFileInput     = ref(null)
const modalSelectedFiles = ref([])
const notifEmail         = ref('')

function openUploadModal() {
  modalSelectedFiles.value = []
  notifEmail.value = ''
  uploadModal.value = true
}

function closeUploadModal() {
  uploadModal.value = false
}

function handleModalFileSelect(e) {
  const picked = [...(e.target.files || [])]
  e.target.value = ''
  if (picked.length > 0) modalSelectedFiles.value = [...modalSelectedFiles.value, ...picked]
}

function removeModalFile(i) {
  modalSelectedFiles.value = modalSelectedFiles.value.filter((_, idx) => idx !== i)
}

async function submitUploadModal() {
  const files = [...modalSelectedFiles.value]
  const email = notifEmail.value.trim()
  closeUploadModal()
  for (const file of files) {
    await doNewUpload(file, email)
  }
}

// ── Progress modal ─────────────────────────────────────────────────────────────
const progressModal = ref(null)   // job object while modal is open
const progressData  = ref(null)   // { step, pct, ts } from /progress endpoint
let progressTimer   = null

function openProgressModal(job) {
  progressModal.value = { ...job }
  progressData.value  = null
  _tickProgress()
}

function closeProgressModal() {
  if (progressTimer) { clearTimeout(progressTimer); progressTimer = null }
  progressModal.value = null
  progressData.value  = null
}

async function _tickProgress() {
  if (!progressModal.value) return
  const jobId = progressModal.value.job_id

  // Fetch structured progress
  const prog = await fetchProgress(jobId).catch(() => null)
  if (prog) progressData.value = prog

  // Also refresh job status so badge + error update
  try {
    const res = await fetch(`/api/jobs/${jobId}/status`, {
      headers: { Authorization: `Bearer ${(useCognitoAuth().idToken.value ?? '')}` },
    })
    if (res.ok) {
      const s = await res.json()
      const idx = jobs.value.findIndex(j => j.job_id === jobId)
      if (idx !== -1) jobs.value[idx] = { ...jobs.value[idx], ...s }
      progressModal.value = { ...progressModal.value, ...s }
    }
  } catch { /* ignore */ }

  const status = progressModal.value?.status
  if (status === 'queued' || status === 'processing') {
    progressTimer = setTimeout(_tickProgress, 5000)
  }
}

// ── Select / delete state ──────────────────────────────────────────────────────
const selectMode = ref(false)
const selectedIds = ref(new Set())
const deleting    = ref(false)

function enterSelectMode() {
  selectMode.value  = true
  selectedIds.value = new Set()
}

function cancelSelectMode() {
  selectMode.value  = false
  selectedIds.value = new Set()
}

function toggleSelect(jobId) {
  const next = new Set(selectedIds.value)
  if (next.has(jobId)) next.delete(jobId)
  else next.add(jobId)
  selectedIds.value = next
}

async function deleteSelected() {
  if (selectedIds.value.size === 0) return
  deleting.value = true
  const ids = [...selectedIds.value]
  for (const id of ids) {
    try {
      await deleteJob(id)
      jobs.value = jobs.value.filter(j => j.job_id !== id)
      const next = new Set(selectedIds.value)
      next.delete(id)
      selectedIds.value = next
    } catch (err) {
      const name = jobs.value.find(j => j.job_id === id)?.name || id
      showToast(`Failed to delete "${name}"`, 'error')
    }
  }
  deleting.value   = false
  selectMode.value = false
}

// ── Toast ──────────────────────────────────────────────────────────────────────
const toasts = ref([])
let toastSeq = 0

function showToast(message, type = 'error') {
  const id = ++toastSeq
  toasts.value.push({ id, message, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 4000)
}

// ── File upload + retry ────────────────────────────────────────────────────────
async function handleFileUpload(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) { retryingJobId.value = null; return }
  if (retryingJobId.value) {
    const jid = retryingJobId.value
    retryingJobId.value = null
    await doRetry(jid, file)
  } else {
    await doNewUpload(file)
  }
}

async function doNewUpload(file, email = '') {
  let job_id, upload_url
  try {
    const r = await initUpload(file.name, file.name, email)
    job_id = r.job_id; upload_url = r.upload_url
  } catch (err) {
    showToast(`Upload failed: ${err.message}`, 'error')
    return
  }
  // Optimistic prepend before S3 upload starts
  jobs.value = [
    { job_id, name: file.name, status: 'uploading', review_state: 'unreviewed',
      pages: 0, crops: 0, gps: null, grid_no: null, date: null,
      created_at: new Date().toISOString(), error: null, corrections: {} },
    ...jobs.value,
  ]
  await doUploadContinue(job_id, upload_url, file)
}

async function doUploadContinue(job_id, upload_url, file) {
  savePendingFile(job_id, file)
  try {
    await s3Put(upload_url, file)
  } catch (err) {
    _setUploadError(job_id, err.message)
    return
  }
  try {
    await startJob(job_id)
    _clearUploadError(job_id, 'queued')
    pollJob(job_id)
  } catch (err) {
    _setUploadError(job_id, err.message)
  }
}

async function doRetry(jobId, file) {
  // Show spinner while retrying
  uploadErrors.value = { ...uploadErrors.value, [jobId]: null }
  let result
  try {
    result = await startJob(jobId)
  } catch (err) {
    _setUploadError(jobId, err.message)
    return
  }
  if (result.needs_upload) {
    await doUploadContinue(jobId, result.upload_url, file)
  } else {
    _clearUploadError(jobId, 'queued')
    pollJob(jobId)
  }
}

function handleRetryClick(job) {
  const pending = getPendingFile(job.job_id)
  if (pending) {
    doRetry(job.job_id, pending)
  } else {
    retryingJobId.value = job.job_id
    fileInput.value.click()
  }
}

function _setUploadError(job_id, msg) {
  const idx = jobs.value.findIndex(j => j.job_id === job_id)
  if (idx !== -1) jobs.value[idx] = { ...jobs.value[idx], status: 'uploading' }
  uploadErrors.value = { ...uploadErrors.value, [job_id]: msg }
}

function _clearUploadError(job_id, status) {
  const idx = jobs.value.findIndex(j => j.job_id === job_id)
  if (idx !== -1) jobs.value[idx] = { ...jobs.value[idx], status }
  const next = { ...uploadErrors.value }
  delete next[job_id]
  uploadErrors.value = next
}

async function loadThumbnails() {
  for (const job of jobs.value) {
    if (job.status === 'complete' && !thumbnailUrls.value[job.job_id]) {
      fetchAuthedUrl(pageUrl(job.job_id, 'page_1.png')).then(url => {
        if (url) thumbnailUrls.value = { ...thumbnailUrls.value, [job.job_id]: url }
      })
    }
  }
}

// ── Lifecycle ──────────────────────────────────────────────────────────────────
onMounted(async () => {
  await fetchJobs()
  loadThumbnails()
  await initMap()
})

onBeforeUnmount(() => {
  leafletMap?.remove()
  delete window._formidableNav
  if (progressTimer) clearTimeout(progressTimer)
})

// ── Map ────────────────────────────────────────────────────────────────────────
async function initMap() {
  if (!mapContainer.value) return
  const L = (await import('leaflet')).default

  leafletMap = L.map(mapContainer.value, { zoomControl: true }).setView([10.31, 76.82], 11)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
  }).addTo(leafletMap)

  mapContainer.value.querySelector('.leaflet-tile-pane').style.filter =
    'grayscale(1) brightness(1.05) contrast(0.85)'

  const byLocation = new Map()
  for (const job of jobs.value) {
    if (!job.gps) continue
    const key = `${job.gps[0].toFixed(4)},${job.gps[1].toFixed(4)}`
    if (!byLocation.has(key)) byLocation.set(key, { gps: job.gps, jobs: [] })
    byLocation.get(key).jobs.push(job)
  }

  for (const { gps, jobs: locJobs } of byLocation.values()) {
    const marker = L.circleMarker(gps, {
      radius: 8, color: '#ffffff', fillColor: '#000000', fillOpacity: 1, weight: 2,
    }).addTo(leafletMap)

    const popupContent = locJobs.map(j =>
      `<a href="/review/${j.job_id}"
          onclick="event.preventDefault();window._formidableNav('${j.job_id}')"
          style="display:block;font-family:Inter,sans-serif;font-size:11px;color:#000;text-decoration:none;line-height:1.8;white-space:nowrap"
        >${j.name.replace(/\.pdf$/i, '')}</a>`
    ).join('')
    marker.bindPopup(popupContent, { maxWidth: 240, className: 'formidable-popup' })
  }

  window._formidableNav = (jobId) => { leafletMap?.closePopup(); openReview(jobId) }
}

// ── Navigation / actions ───────────────────────────────────────────────────────
function handleRowClick(job) {
  if (selectMode.value) { toggleSelect(job.job_id); return }
  if (job.status === 'uploading') {
    if (uploadErrors.value[job.job_id]) handleRetryClick(job)
    return
  }
  if (job.status === 'queued' || job.status === 'processing') {
    openProgressModal(job)
  } else {
    openReview(job.job_id)
  }
}

function openReview(jobId) {
  router.push({ name: 'job-review', params: { jobId } })
}

function openLightbox(job) {
  lightbox.value = job
}

async function downloadXlsx(job) {
  try {
    const { url } = await getXlsxUrl(job.job_id)
    const a = document.createElement('a')
    a.href = url
    a.click()
  } catch (err) {
    showToast(`Download failed: ${err.message}`, 'error')
  }
}

async function rerunJob(job) {
  try {
    const { job_id } = await rerunJobApi(job.job_id)
    await fetchJobs()      // surface the new job in the list
    pollJob(job_id)        // track its progress
    showToast('Rerun started as a new job', 'success')
  } catch (err) {
    showToast(`Rerun failed: ${err.message}`, 'error')
  }
}

function handleLogout() {
  logout()
  router.push({ name: 'login' })
}
</script>

<style>
.formidable-popup .leaflet-popup-content-wrapper {
  padding: 6px 10px;
  border-radius: 3px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.18);
}
.formidable-popup .leaflet-popup-content { margin: 0; }
.formidable-popup .leaflet-popup-tip-container { display: none; }
</style>
