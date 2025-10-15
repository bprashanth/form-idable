# UI Design

See [imf](./imf.md) for details on the intermediate format.
This intermediate format is used to drive the UI.


1. Single Source of Truth

The entire UI state (editable form) is driven by one reactive formData object loaded from the JSON.

Vue 3’s reactivity ensures that any change in input boxes immediately updates the data structure.

2. Layered Visual Layout

We can visualize the UI as three stacked layers:
```
--------------------------------
Toolbar / Controls (top bar)
--------------------------------
[ Canvas container ]
  [ Background Image (form) ]
  [ Overlay Boxes with Text ]
--------------------------------
Side Panel 
--------------------------------
```

3. Box Positioning

Each cell or field has normalized Textract coordinates (bbox.Left, Top, Width, Height) relative to the image. Convert these into absolute pixel coordinates on the overlay container.

Eg:
```
const x = bbox.Left * imageWidth;
const y = bbox.Top * imageHeight;
const w = bbox.Width * imageWidth;
const h = bbox.Height * imageHeight
```

4. Box Components

Each bounding box (data cell or header) is represented as a Vue component, eg 
```
<BoxOverlay 
  :x="x"
  :y="y"
  :w="w"
  :h="h"
  :value="cell.text"
  :confidence="cell.confidence"
  :selected="selectedGroupId === cell.system.group_id"
  @click="selectBox(cell)"
/>
```

5. Interaction Flow

When a box is clicked:

Highlight it.

Display editable value in a right-side panel (or floating modal).

On edit confirm → update formData.rows[rowIndex].system.cells[cellId].text.

Re-render updated text on overlay.

6. Confidence & Validation

Color coding by confidence:

borderColor = confidence < 70 ? 'red' : confidence < 85 ? 'orange' : 'green';


Universal field validity toggle:

Each universal field shows a checkbox for system.valid.

Invalid fields are grayed out on overlay.

7. Saving / Export

User can click “Save JSON” → triggers a JSON download of the in-memory structure.

## UI Zones 


| Zone                   | Purpose                                                 | Data Source                            |
| :--------------------- | :------------------------------------------------------ | :------------------------------------- |
| **Image Panel (left)** | Display form image with overlays                        | `rows[].system.cells[]` bounding boxes |
| **Side Panel (right)** | Edit details of selected box / field                    | `formData` reactive object             |
| **Toolbar (top)**      | File name, zoom, save/export, filter by type/confidence | Global UI actions                      |
| **Legend (bottom)**    | Color key (confidence thresholds, merged headers)       | Static metadata                        |


## Components 


```
components/
FormViewer.vue          # Top-level controller
BoxOverlay.vue          # Individual clickable box
SidePanel.vue           # Field editor + universal field management
Toolbar.vue             # File controls, zoom, export
ConfidenceLegend.vue    # Color key legend
```

## Phasing 

| Phase                             | Focus                                   | Core Components                                              |
| :-------------------------------- | :-------------------------------------- | :----------------------------------------------------------- |
| **1. Basic Form Rendering**       | Show form image + bounding box overlays | Canvas / `<img>` layer, overlay `div`s or `<canvas>` drawing |
| **2. Data Display**               | Display extracted text in each box      | `v-for` rendering using positions + `system.bbox`            |
| **3. Interactive Editing**        | Click-to-edit field values              | Click events → modal/inline editor → JSON sync               |
| **4. Universal Field Management** | Toggle `system.valid` per field         | Side panel with toggles (checkbox/slider)                    |
| **5. Header Management**          | Handle merged or hierarchical headers   | Group hover highlights, grouped editing                      |
| **6. Validation Indicators**      | Show confidence-based colors            | Border or background color by `confidence` threshold         |
| **7. Export / Save**              | Persist updated JSON                    | “Download JSON” or `POST` to backend                         |

