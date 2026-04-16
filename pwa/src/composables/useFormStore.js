import { ref } from 'vue'

const capturedImage = ref(null) // File object from camera/gallery
const croppedImage = ref(null) // Blob (JPEG) after cropping
const xlsxBytes = ref(null) // ArrayBuffer of returned .xlsx
const summary = ref(null) // { rowCount, flaggedCount } or null
const rowBboxes = ref(null) // Map<system_serial, {left,top,width,height}>

export function useFormStore() {
  function reset() {
    capturedImage.value = null
    croppedImage.value = null
    xlsxBytes.value = null
    summary.value = null
    rowBboxes.value = null
  }

  return {
    capturedImage,
    croppedImage,
    xlsxBytes,
    summary,
    rowBboxes,
    reset,
  }
}
