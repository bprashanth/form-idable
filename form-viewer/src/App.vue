<template>
  <div class="flex flex-col h-screen bg-gray-900 text-gray-100">
    <!-- Top bar -->
    <ToolBar
      class="border-b border-gray-700"
      @json-loaded="onJsonLoaded"
      @image-loaded="onImageLoaded"
      @save-json="saveJson"
      @zoom-in="zoomIn"
      @zoom-out="zoomOut"
    />

    <!-- Main content -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Viewer -->
      <div class="flex-1 relative overflow-hidden bg-gray-800">
        <FormViewer
          v-if="formData && imageUrl"
          :formData="formData"
          :imageUrl="imageUrl"
          :zoom="zoom"
          @select-row="onSelectRow"
          @select-header="onSelectHeader"
          @select-universal="onSelectUniversal"
        />
        <div v-else class="h-full flex items-center justify-center text-gray-500">
          <p>Select an image and JSON to begin.</p>
        </div>
      </div>

      <!-- Side panel -->
      <div class="w-80 border-l border-gray-700 bg-[#0f141a]">
        <SidePanel
          :mode="mode"
          :selectedRow="selectedRow"
          :headers="formData?.header_map || null"
          :universals="formData?.universal_fields || null"
          @update-row="updateRow"
          @update-header="updateHeader"
          @update-universal="updateUniversal"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ToolBar from '@/components/ToolBar.vue'
import FormViewer from '@/components/FormViewer.vue'
import SidePanel from '@/components/SidePanel.vue'

/**
 * State
 */
const formData = ref(null) // loaded output.json (reactive source of truth)
const imageUrl = ref(null) // objectURL for the selected image
const zoom = ref(1) // viewer zoom 0.5–2.0

// selection / mode
const mode = ref(null) // "row" | "header" | "universal" | null
const selectedRow = ref(null) // currently selected row object
const selectedHeaderKey = ref(null) // currently selected header key (string)

/**
 * Toolbar events
 */
function onJsonLoaded(json) {
  formData.value = json
  // clear selection when new JSON is loaded
  mode.value = null
  selectedRow.value = null
  selectedHeaderKey.value = null
}
function onImageLoaded(url) {
  imageUrl.value = url
}
function zoomIn() {
  zoom.value = Math.min(2, +(zoom.value + 0.1).toFixed(2))
}
function zoomOut() {
  zoom.value = Math.max(0.5, +(zoom.value - 0.1).toFixed(2))
}

/**
 * FormViewer selection events
 */
function onSelectRow(row) {
  mode.value = 'row'
  selectedRow.value = row
  selectedHeaderKey.value = null
}
function onSelectHeader(key) {
  mode.value = 'header'
  selectedHeaderKey.value = key
  selectedRow.value = null
}
function onSelectUniversal() {
  mode.value = 'universal'
  selectedHeaderKey.value = null
  selectedRow.value = null
}

/**
 * Row editing
 * Replaces the row (by group_id) so changes persist in formData and Save JSON exports them.
 */
function updateRow(updatedRow) {
  if (!formData.value || !updatedRow?.system?.group_id) return
  const gid = updatedRow.system.group_id
  const idx = formData.value.rows.findIndex((r) => r.system?.group_id === gid)
  if (idx !== -1) {
    formData.value.rows[idx] = updatedRow
    selectedRow.value = updatedRow // keep panel in sync
  }
}

/**
 * Header editing
 * Handles three editable properties:
 *  - indicator (key rename) - propagate to rows + cells
 *  - field_name - update only header_map[key].field_name
 *  - description - update only header_map[key].description
 */
function updateHeader({ key, field, value }) {
  if (!formData.value?.header_map) return
  const headerMap = formData.value.header_map
  const headerEntry = headerMap[key]
  if (!headerEntry) return

  if (field === 'indicator') {
    const newKey = value.trim()
    if (!newKey || newKey === key) return

    // move sub-dict to new key
    headerMap[newKey] = { ...headerEntry }
    delete headerMap[key]

    // rename keys in rows
    for (const row of formData.value.rows || []) {
      if (Object.prototype.hasOwnProperty.call(row, key)) {
        row[newKey] = row[key]
        delete row[key]
      }
      // update cell.header too
      for (const cellId in row.system?.cells || {}) {
        const cell = row.system.cells[cellId]
        if (cell.header === key) cell.header = newKey
      }
    }
  } else if (field === 'field_name' || field === 'description') {
    headerEntry[field] = value
  }
}

/**
 * Universal editing
 * Update universal_fields[key].value live. Validity is handled via v-model in SidePanel.
 */
function updateUniversal({ key, newVal }) {
  if (!formData.value?.universal_fields?.[key]) return
  formData.value.universal_fields[key].value = newVal
}

/**
 * Save JSON
 *  - Create a deep copy
 *  - Gather only valid universal fields
 *  - Merge those k/v into each row (flat)
 *  - Download the updated JSON
 */
function saveJson() {
  if (!formData.value) return

  const cloned = structuredClone(formData.value)

  const validUniversals = Object.fromEntries(
    Object.entries(cloned.universal_fields || {}).filter(([, v]) => v?.system?.valid !== false),
  )

  const flatUniversals = {}
  for (const [k, v] of Object.entries(validUniversals)) {
    flatUniversals[k] = v?.value ?? null
  }

  cloned.rows = (cloned.rows || []).map((row) => ({
    ...flatUniversals,
    ...row,
  }))

  const blob = new Blob([JSON.stringify(cloned, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'updated_output.json'
  a.click()
  URL.revokeObjectURL(url)
}
</script>
