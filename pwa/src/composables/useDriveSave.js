const API_KEY = import.meta.env.VITE_GOOGLE_API_KEY

let pickerLoaded = false

function loadPickerApi() {
  if (pickerLoaded) return Promise.resolve()
  return new Promise((resolve, reject) => {
    window.gapi.load('picker', {
      callback: () => {
        pickerLoaded = true
        resolve()
      },
      onerror: () => reject(new Error('Failed to load Picker API')),
    })
  })
}

function pickFolder(token) {
  return loadPickerApi().then(() => {
    return new Promise((resolve, reject) => {
      const folderView = new window.google.picker.DocsView(
        window.google.picker.ViewId.FOLDERS,
      )
      folderView.setSelectFolderEnabled(true)
      folderView.setMimeTypes('application/vnd.google-apps.folder')

      const picker = new window.google.picker.PickerBuilder()
        .setOAuthToken(token)
        .setDeveloperKey(API_KEY)
        .addView(folderView)
        .setTitle('Select a folder')
        .setCallback((data) => {
          if (data.action === window.google.picker.Action.PICKED) {
            const doc = data.docs[0]
            resolve({ id: doc.id, name: doc.name })
          } else if (data.action === window.google.picker.Action.CANCEL) {
            reject(new Error('Folder selection cancelled'))
          }
        })
        .build()
      picker.setVisible(true)
    })
  })
}

async function uploadFile(token, folderId, fileName, xlsxBytes) {
  const metadata = {
    name: fileName,
    mimeType:
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    parents: [folderId],
  }

  const boundary = '---scribe_boundary'
  const delimiter = `\r\n--${boundary}\r\n`
  const closeDelimiter = `\r\n--${boundary}--`

  const metaPart =
    delimiter +
    'Content-Type: application/json; charset=UTF-8\r\n\r\n' +
    JSON.stringify(metadata)

  const encoder = new TextEncoder()
  const metaBytes = encoder.encode(metaPart)
  const binHeader = encoder.encode(
    delimiter +
      'Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n' +
      'Content-Transfer-Encoding: binary\r\n\r\n',
  )
  const closeBytes = encoder.encode(closeDelimiter)

  const fileBytes =
    xlsxBytes instanceof ArrayBuffer ? new Uint8Array(xlsxBytes) : xlsxBytes

  const body = new Uint8Array(
    metaBytes.length + binHeader.length + fileBytes.length + closeBytes.length,
  )
  let offset = 0
  body.set(metaBytes, offset)
  offset += metaBytes.length
  body.set(binHeader, offset)
  offset += binHeader.length
  body.set(fileBytes, offset)
  offset += fileBytes.length
  body.set(closeBytes, offset)

  const res = await fetch(
    'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink',
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': `multipart/related; boundary=${boundary}`,
      },
      body: body,
    },
  )

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Upload failed (${res.status}): ${text}`)
  }

  return res.json()
}

export function useDriveSave() {
  return { pickFolder, uploadFile }
}
