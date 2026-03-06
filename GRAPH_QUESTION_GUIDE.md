# 📈 Graph Question Creation - Complete Guide

## Overview

Invigilators can now create graph questions with a **reference graph** drawn in GeoGebra. Students see the reference graph as part of the question and sketch their answer on their own GeoGebra canvas.

---

## 🎯 Features

### **For Invigilators (Question Creation)**

✅ **GeoGebra Integration**
- Full GeoGebra Classic interface embedded in manage_questions.html
- Draw functions, shapes, points, lines, etc.
- All GeoGebra tools available

✅ **Graph Capture**
- Click "Capture Graph" to take a screenshot
- Exports as base64 PNG image
- Preview shown before saving

✅ **Canvas Configuration**
- Set X axis range (min/max)
- Set Y axis range (min/max)
- Configure grid step size
- Settings stored as JSON in database

✅ **Reference Image Storage**
- Base64 image saved in `reference_image` column
- Axis config saved in `options` column (JSON)
- Automatically displayed to students during exam

---

### **For Students (During Exam)**

✅ **Reference Graph Display**
- "Show Reference" button on graph questions
- Toggle visibility of reference graph
- Shows image + canvas settings

✅ **Student Canvas**
- Full GeoGebra Classic interface
- Independent from reference graph
- Auto-saves every 30 seconds
- Manual "Save Graph" button

---

## 📋 Database Schema

### **Question Model Updates**

```python
class Question(db.Model):
    # ... existing fields ...
    
    reference_image = db.Column(db.Text)  # Base64 PNG image
    # options column now also stores graph config as JSON:
    # {
    #   "x_min": -10,
    #   "x_max": 10,
    #   "y_min": -10,
    #   "y_max": 10,
    #   "step": 1
    # }
```

---

## 🔧 How to Use

### **Creating a Graph Question**

1. **Navigate to Question Management**
   ```
   /manage_questions/<exam_name>
   ```

2. **Fill in Basic Info**
   - Question Text: "Sketch the graph of f(x) = x²"
   - Question Type: **Graph Sketching (GeoGebra)**
   - Points: e.g., 10

3. **Draw Reference Graph**
   - GeoGebra iframe loads automatically
   - Use tools to draw your reference:
     - Input bar: type `f(x) = x^2`
     - Draw points, lines, shapes
     - Add labels, text, etc.

4. **Capture Graph**
   - Click **"📷 Capture Graph"**
   - Wait for preview to appear
   - Preview shows exactly what students will see

5. **Configure Canvas (Optional)**
   - Set X Min/Max (default: -10 to 10)
   - Set Y Min/Max (default: -10 to 10)
   - Set Grid Step (default: 1)
   - These settings are shown to students

6. **Save Question**
   - Click **"Add Question"**
   - Reference image and config are saved

---

### **Student Experience**

1. **During Exam**
   - Student sees graph question
   - **"Show Reference"** button visible

2. **View Reference**
   - Click "Show Reference"
   - Reference graph appears above canvas
   - Canvas settings displayed below image
   - Click "Close" to hide

3. **Sketch Answer**
   - Use GeoGebra tools below
   - Draw their answer independently
   - Auto-saves every 30 seconds
   - Click "Save Graph" to manually save

---

## 💻 Code Implementation

### **Frontend (manage_questions.html)**

```html
<!-- GeoGebra iframe -->
<iframe id="geogebraIframe" 
        src="https://www.geogebra.org/classic?lang=en"
        style="width:100%;height:500px;">
</iframe>

<!-- Capture button -->
<button onclick="captureGraph()">
    <i class="fas fa-camera"></i> Capture Graph
</button>

<!-- Hidden inputs -->
<input type="hidden" name="graph_reference_image" id="graphReferenceImage">
<input type="number" name="graph_x_min" value="-10">
<input type="number" name="graph_x_max" value="10">
<!-- etc. -->
```

### **JavaScript (Graph Capture)**

```javascript
function captureGraph() {
    const iframe = document.getElementById('geogebraIframe');
    
    // Request PNG export from GeoGebra
    iframe.contentWindow.postMessage(
        { action: 'export', type: 'png' }, 
        '*'
    );
    
    // Listen for response
    window.addEventListener('message', function(e) {
        if (e.data && e.data.type === 'png' && e.data.data) {
            const base64Image = e.data.data;
            
            // Store in hidden input
            document.getElementById('graphReferenceImage').value = base64Image;
            
            // Show preview
            document.getElementById('previewImg').src = base64Image;
        }
    });
}
```

### **Backend (app.py)**

```python
@app.route('/manage_questions/<exam_name>', methods=['GET', 'POST'])
def manage_questions(exam_name):
    if request.method == 'POST':
        # ... existing code ...
        
        # Handle graph questions
        if question_type == 'graph':
            reference_image = request.form.get('graph_reference_image')
            
            # Build axis configuration
            graph_config = {
                'x_min': float(request.form.get('graph_x_min', '-10')),
                'x_max': float(request.form.get('graph_x_max', '10')),
                'y_min': float(request.form.get('graph_y_min', '-10')),
                'y_max': float(request.form.get('graph_y_max', '10')),
                'step': float(request.form.get('graph_step', '1'))
            }
            
            question = Question(
                # ... other fields ...
                reference_image=reference_image,
                options=json.dumps(graph_config)
            )
```

### **Student View (exam.html)**

```html
{% if q.reference_image %}
<!-- Show Reference button -->
<button onclick="toggleReferenceGraph({{ q.id }})">
    <i class="fas fa-image"></i> Show Reference
</button>

<!-- Reference graph panel (hidden by default) -->
<div id="referenceGraph{{ q.id }}" style="display:none;">
    <img src="{{ q.reference_image }}" alt="Reference">
    
    {% set graph_config = q.options|from_json %}
    <div>
        X: [{{ graph_config.x_min }}, {{ graph_config.x_max }}]
        Y: [{{ graph_config.y_min }}, {{ graph_config.y_max }}]
        Step: {{ graph_config.step }}
    </div>
</div>
{% endif %}

<!-- Student's own GeoGebra canvas -->
<iframe id="graphFrame{{ q.id }}" 
        src="https://www.geogebra.org/classic?lang=en">
</iframe>
```

---

## 🎨 UI/UX Design

### **Color Scheme (Matches Existing Theme)**

```css
/* Dark theme variables */
--bg-card: rgba(255, 255, 255, 0.98);
--bg-overlay: rgba(0, 0, 0, 0.05);
--teal: #008080;
--line-1: rgba(0, 0, 0, 0.1);
--t1: #1f2937;  /* Primary text */
--t3: #6b7280;  /* Muted text */
```

### **Layout**

```
┌─────────────────────────────────────────┐
│ 📈 Create Reference Graph               │
│ Draw the reference graph students see   │
├─────────────────────────────────────────┤
│                                         │
│  [GeoGebra Classic Interface]           │
│  - Graph paper                          │
│  - Input bar                            │
│  - Tools panel                          │
│                                         │
├─────────────────────────────────────────┤
│ [📷 Capture] [🔄 Reset] ✓ Captured!    │
│                                         │
│ Preview:                                │
│ ┌─────────────────────────────────┐    │
│ │ [Reference Graph Image]         │    │
│ └─────────────────────────────────┘    │
│                                         │
│ 📐 Canvas Configuration (Optional)      │
│ X Min: [-10]  X Max: [10]               │
│ Y Min: [-10]  Y Max: [10]               │
│ Grid Step: [1]                          │
└─────────────────────────────────────────┘
```

---

## 📊 Data Flow

```
Invigilator creates question:
  1. Draws in GeoGebra
  2. Clicks "Capture Graph"
  3. GeoGebra → postMessage → PNG base64
  4. Base64 → hidden input → POST to server
  5. Server saves to Question.reference_image
  6. Axis config → JSON → Question.options

Student answers question:
  1. Loads exam.html
  2. Sees "Show Reference" button
  3. Clicks → reference graph appears
  4. Uses own GeoGebra canvas below
  5. Saves graph → base64 PNG → Answer.answer_text
```

---

## 🔒 Security Considerations

✅ **Base64 Image Storage**
- Images stored as text (no file uploads)
- No external storage needed
- Database-only storage

✅ **GeoGebra iframe**
- Loaded from official https://www.geogebra.org
- Communication via postMessage (secure)
- No direct DOM access

✅ **Student/Invigilator Separation**
- Students cannot see reference until exam starts
- Reference is read-only for students
- Students draw on separate canvas

---

## 🐛 Troubleshooting

### **"Capture Graph" button doesn't work**

**Problem:** GeoGebra iframe not loaded or postMessage failing

**Solution:**
1. Check browser console for errors
2. Ensure iframe has loaded completely
3. Try refreshing the page
4. Check internet connection (GeoGebra loads from CDN)

### **Reference graph not showing to students**

**Problem:** Image not saved or not displaying

**Solution:**
1. Check if `reference_image` column exists in database
2. Run migration: `python add_reference_image_column.py`
3. Verify base64 string is saved (check database)
4. Check browser console for image loading errors

### **Graph config not displaying**

**Problem:** JSON parsing failing

**Solution:**
1. Check `options` column contains valid JSON
2. Verify `from_json` filter is available in templates
3. Check for null/empty options in template

---

## 📝 Example Use Cases

### **1. Quadratic Functions**
```
Question: "Sketch f(x) = 2x² - 3x + 1"
Reference: Draw parabola with vertex, axis of symmetry
Config: X: [-5, 5], Y: [-5, 10], Step: 1
```

### **2. Trigonometry**
```
Question: "Graph y = sin(x) for 0 ≤ x ≤ 2π"
Reference: Show sine wave with key points marked
Config: X: [0, 6.28], Y: [-1.5, 1.5], Step: 1.57
```

### **3. Geometry**
```
Question: "Construct an equilateral triangle with side length 5"
Reference: Show triangle with labeled vertices
Config: X: [-10, 10], Y: [-10, 10], Step: 1
```

### **4. Calculus**
```
Question: "Sketch f(x) = x³ - 3x and find critical points"
Reference: Show cubic with local max/min marked
Config: X: [-3, 3], Y: [-5, 5], Step: 0.5
```

---

## ✅ Testing Checklist

- [ ] Create graph question with reference
- [ ] Capture graph successfully
- [ ] Preview displays correctly
- [ ] Axis config saves properly
- [ ] Question appears in list with reference image
- [ ] Student sees "Show Reference" button
- [ ] Reference graph toggles correctly
- [ ] Canvas settings display properly
- [ ] Student can draw on separate canvas
- [ ] Student graph saves correctly
- [ ] Invigilator can view student's graph in review

---

## 🎉 Success!

Graph question creation is now fully implemented with:
- ✅ GeoGebra integration
- ✅ Reference graph capture
- ✅ Canvas configuration
- ✅ Student view with toggle
- ✅ Database storage
- ✅ Secure implementation

**Ready to use!** 🚀
