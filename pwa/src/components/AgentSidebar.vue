<template>
  <Transition name="slide">
    <div v-if="sidebarOpen" class="fixed inset-0 z-20 flex">
      <!-- Backdrop -->
      <div class="flex-1 bg-black/50" @click="close" />

      <!-- Panel -->
      <div class="w-80 h-full bg-gray-900 border-l border-gray-700 flex flex-col overflow-hidden">

        <!-- Header -->
        <div class="flex items-center gap-2 px-4 py-3 border-b border-gray-700 shrink-0">
          <button
            class="text-sm px-3 py-1 rounded-full transition-colors"
            :class="sidebarTab === 'cheatsheet' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'"
            @click="sidebarTab = 'cheatsheet'"
          >Column Types</button>
          <button
            class="text-sm px-3 py-1 rounded-full transition-colors"
            :class="sidebarTab === 'species-db' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'"
            @click="sidebarTab = 'species-db'"
          >Species DB</button>
          <button class="ml-auto text-gray-500 hover:text-gray-200 text-lg" @click="close">×</button>
        </div>

        <!-- Cheatsheet tab -->
        <div v-if="sidebarTab === 'cheatsheet'" class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
          <div v-if="!cheatsheet" class="text-gray-500 text-sm">Loading…</div>
          <template v-else>
            <div v-for="(config, typeName) in cheatsheet.types" :key="typeName" class="flex flex-col gap-2">
              <p class="text-sm font-medium text-gray-300 capitalize">{{ typeName }}</p>

              <p class="text-xs text-gray-500">Keywords</p>
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="kw in config.keywords" :key="kw"
                  class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-700 text-xs text-gray-300"
                >
                  {{ kw }}
                  <button class="text-gray-500 hover:text-red-400" @click="removeKeyword(typeName, kw)">×</button>
                </span>
              </div>
              <div class="flex gap-1">
                <input
                  v-model="newKeyword[typeName]"
                  placeholder="add keyword"
                  class="flex-1 h-8 bg-gray-800 border border-gray-600 rounded px-2 text-xs text-gray-100 focus:outline-none focus:border-blue-500"
                  @keyup.enter="addKeyword(typeName)"
                />
                <button class="px-3 h-8 rounded bg-gray-700 text-gray-300 text-xs hover:bg-gray-600" @click="addKeyword(typeName)">+</button>
              </div>

              <p class="text-xs text-gray-500 mt-1">Ignore exact headers</p>
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="h in config.ignore_headers" :key="h"
                  class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-gray-800 border border-gray-700 text-xs text-gray-400"
                >
                  {{ h }}
                  <button class="text-gray-500 hover:text-red-400" @click="removeIgnoreHeader(typeName, h)">×</button>
                </span>
              </div>
              <div class="flex gap-1">
                <input
                  v-model="newIgnoreHeader[typeName]"
                  placeholder="exact header to ignore"
                  class="flex-1 h-8 bg-gray-800 border border-gray-600 rounded px-2 text-xs text-gray-100 focus:outline-none focus:border-blue-500"
                  @keyup.enter="addIgnoreHeader(typeName)"
                />
                <button class="px-3 h-8 rounded bg-gray-700 text-gray-300 text-xs hover:bg-gray-600" @click="addIgnoreHeader(typeName)">+</button>
              </div>
            </div>

            <button
              class="w-full h-10 rounded-lg bg-blue-600 text-white text-sm font-medium active:bg-blue-700 transition-colors mt-2"
              @click="saveCheatsheet"
            >Save Cheatsheet</button>
            <p v-if="savedMsg" class="text-green-400 text-xs text-center">{{ savedMsg }}</p>
          </template>
        </div>

        <!-- Species DB tab -->
        <div v-if="sidebarTab === 'species-db'" class="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          <p class="text-xs text-gray-500">{{ speciesDb.length }} entries</p>

          <div class="flex flex-col gap-1 text-xs">
            <div class="flex gap-2 text-gray-500 font-medium pb-1 border-b border-gray-700">
              <span class="w-16 shrink-0">Abbr</span>
              <span class="flex-1">Expanded</span>
              <span class="w-20 shrink-0">Toda name</span>
            </div>
            <div v-for="s in speciesDb" :key="s.abbr + s.expanded" class="flex gap-2 py-0.5 border-b border-gray-800">
              <span class="w-16 shrink-0 font-mono text-gray-400">{{ s.abbr }}</span>
              <span class="flex-1 text-gray-200">{{ s.expanded }}</span>
              <span class="w-20 shrink-0 text-gray-500">{{ s.toda_name }}</span>
            </div>
          </div>

          <div class="flex flex-col gap-2 mt-2 pt-3 border-t border-gray-700">
            <p class="text-xs font-medium text-gray-400">Add entry</p>
            <input v-model="newSpecies.abbr"      placeholder="Abbreviation"          class="h-8 bg-gray-800 border border-gray-600 rounded px-2 text-xs text-gray-100 focus:outline-none focus:border-blue-500" />
            <input v-model="newSpecies.expanded"   placeholder="Expanded name"          class="h-8 bg-gray-800 border border-gray-600 rounded px-2 text-xs text-gray-100 focus:outline-none focus:border-blue-500" />
            <input v-model="newSpecies.toda_name"  placeholder="Toda name (optional)"   class="h-8 bg-gray-800 border border-gray-600 rounded px-2 text-xs text-gray-100 focus:outline-none focus:border-blue-500" />
            <button
              class="w-full h-9 rounded-lg bg-green-700 text-white text-sm font-medium active:bg-green-800 transition-colors disabled:opacity-40"
              :disabled="!newSpecies.abbr || !newSpecies.expanded"
              @click="addSpeciesEntry"
            >Add</button>
            <p v-if="savedMsg" class="text-green-400 text-xs text-center">{{ savedMsg }}</p>
          </div>
        </div>

      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useSidebar } from '@/composables/useSidebar.js'

const { sidebarOpen, sidebarTab, close } = useSidebar()

const cheatsheet     = ref(null)
const speciesDb      = ref([])
const newKeyword     = ref({})
const newIgnoreHeader = ref({})
const newSpecies     = ref({ abbr: '', expanded: '', toda_name: '' })
const savedMsg       = ref('')

async function agentGet(path) {
  const res = await fetch(path)
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

async function load() {
  const [cs, db] = await Promise.all([
    agentGet('/agent/cheatsheet'),
    agentGet('/agent/species-db'),
  ])
  cheatsheet.value = cs
  speciesDb.value  = db
  for (const t of Object.keys(cs.types)) {
    if (!newKeyword.value[t])      newKeyword.value[t] = ''
    if (!newIgnoreHeader.value[t]) newIgnoreHeader.value[t] = ''
  }
}

watch(sidebarOpen, (open) => { if (open) load() })

function flash(msg) {
  savedMsg.value = msg
  setTimeout(() => { savedMsg.value = '' }, 2000)
}

function addKeyword(t) {
  const kw = newKeyword.value[t]?.trim()
  if (!kw) return
  cheatsheet.value.types[t].keywords.push(kw)
  newKeyword.value[t] = ''
}
function removeKeyword(t, kw) {
  cheatsheet.value.types[t].keywords = cheatsheet.value.types[t].keywords.filter(k => k !== kw)
}
function addIgnoreHeader(t) {
  const h = newIgnoreHeader.value[t]?.trim()
  if (!h) return
  cheatsheet.value.types[t].ignore_headers.push(h)
  newIgnoreHeader.value[t] = ''
}
function removeIgnoreHeader(t, h) {
  cheatsheet.value.types[t].ignore_headers = cheatsheet.value.types[t].ignore_headers.filter(x => x !== h)
}
async function saveCheatsheet() {
  await fetch('/agent/cheatsheet', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cheatsheet.value),
  })
  flash('Saved')
}
async function addSpeciesEntry() {
  await fetch('/agent/species-db/entry', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(newSpecies.value),
  })
  speciesDb.value = await agentGet('/agent/species-db')
  newSpecies.value = { abbr: '', expanded: '', toda_name: '' }
  flash('Added')
}
</script>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: opacity 0.2s ease; }
.slide-enter-from, .slide-leave-to       { opacity: 0; }
</style>
