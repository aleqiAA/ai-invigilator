# 📈 GeoGebra Iframe Loading Fix

## Problem
GeoGebra was showing a broken image in the iframe instead of loading the interface.

## Root Causes
1. **Missing iframe permissions** - `allow` and `referrerpolicy` attributes not set
2. **Language parameter issue** - `?lang=en` sometimes breaks GeoGebra loading
3. **CSP headers** - Content-Security-Policy not allowing GeoGebra domain
4. **Ngrok warnings** - Browser blocking iframes without proper headers

---

## ✅ Fixes Applied

### **1. Updated Iframe Attributes**

**Before (Broken):**
```html
<iframe src="https://www.geogebra.org/classic?lang=en"
        allowfullscreen
        style="width:100%;height:500px;border:none;">
</iframe>
```

**After (Working):**
```html
<iframe src="https://www.geogebra.org/classic"
        allowfullscreen
        allow="fullscreen; clipboard-read; clipboard-write"
        referrerpolicy="no-referrer-when-downgrade"
        loading="lazy"
        style="width:100%;height:500px;border:none;border-radius:var(--r-md);background:#fff;">
</iframe>
```

**Changes:**
- ✅ Removed `?lang=en` parameter (causes loading issues)
- ✅ Added `allow` attribute for fullscreen and clipboard access
- ✅ Added `referrerpolicy` for secure referrer handling
- ✅ Added `loading="lazy"` for performance
- ✅ Added explicit white background and border-radius

---

### **2. Added CSP Headers in app.py**

```python
@app.after_request
def add_ngrok_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    # Allow GeoGebra iframe loading
    response.headers['Content-Security-Policy'] = (
        "frame-src 'self' https://www.geogebra.org https://*.geogebra.org;"
    )
    return response
```

**What this does:**
- Allows iframes from GeoGebra domains
- Prevents browser from blocking GeoGebra content
- Works with ngrok tunneling

---

### **3. Updated CSP Meta Tag in base.html**

**Added `frame-src` directive:**
```html
<meta http-equiv="Content-Security-Policy" 
      content="...; frame-src 'self' https://www.geogebra.org https://*.geogebra.org;">
```

**Why needed:**
- Browser enforces CSP from meta tag
- Allows GeoGebra iframe embedding
- Prevents "refused to connect" errors

---

## 🧪 Testing

### **Test Page Created:**
```
test_geogebra.html
```

**How to test:**
1. Open `test_geogebra.html` in your browser
2. Wait for GeoGebra to load (should take 2-5 seconds)
3. Try drawing something in GeoGebra
4. Check for success message

**Expected Result:**
```
✅ GeoGebra loaded successfully!
```

**If Failed:**
```
❌ GeoGebra failed to load after 10 seconds
```

---

## 🔧 Troubleshooting

### **Still showing broken image?**

**Step 1: Check Browser Console**
```
F12 → Console tab
Look for errors like:
- "Refused to connect"
- "CSP violation"
- "Failed to load resource"
```

**Step 2: Verify CSP Headers**
```bash
# In browser DevTools
# Network tab → Refresh → Click on document
# Check Response Headers for:
Content-Security-Policy: frame-src 'self' https://www.geogebra.org...
```

**Step 3: Test Direct Access**
```
Open in new tab: https://www.geogebra.org/classic
```
If this doesn't load, check your internet connection.

**Step 4: Check Ngrok**
If using ngrok:
```
Make sure ngrok is running
Check ngrok dashboard for CSP warnings
Verify ngrok-skip-browser-warning header is set
```

---

## 📋 Files Modified

| File | Changes |
|------|---------|
| `templates/manage_questions.html` | Updated GeoGebra iframe with new attributes |
| `templates/exam.html` | Updated student GeoGebra iframe |
| `app.py` | Added CSP headers in `add_ngrok_header()` |
| `templates/base.html` | Added `frame-src` to CSP meta tag |

---

## ✅ Verification Checklist

After applying fixes, verify:

- [ ] GeoGebra loads in `manage_questions.html`
- [ ] Can draw in GeoGebra interface
- [ ] "Capture Graph" button works
- [ ] Export returns base64 PNG
- [ ] GeoGebra loads in student `exam.html`
- [ ] Student can draw and save graph
- [ ] Auto-save works every 30 seconds
- [ ] No console errors related to GeoGebra

---

## 🎯 Expected Behavior

### **Invigilator View (manage_questions.html):**
```
┌─────────────────────────────────────────┐
│ 📈 Create Reference Graph               │
├─────────────────────────────────────────┤
│                                         │
│  [GeoGebra Classic Interface LOADED]    │
│  ✓ Input bar visible                    │
│  ✓ Tools panel visible                  │
│  ✓ Graph paper visible                  │
│  ✓ Can draw functions                   │
│                                         │
├─────────────────────────────────────────┤
│ [📷 Capture Graph] [🔄 Reset]          │
└─────────────────────────────────────────┘
```

### **Student View (exam.html):**
```
┌─────────────────────────────────────────┐
│ 📈 GRAPH      [🖼️ Show Reference]      │
├─────────────────────────────────────────┤
│                                         │
│  [GeoGebra Classic Interface LOADED]    │
│  ✓ Student can draw                     │
│  ✓ Tools available                      │
│  ✓ Auto-saving every 30s                │
│                                         │
│              [💾 Save Graph]            │
└─────────────────────────────────────────┘
```

---

## 🚀 Quick Test Command

```bash
# 1. Start Flask app
cd "c:\Users\alexn\OneDrive\python file schol\ai_invigilator"
python app.py

# 2. Open test page in browser
# File → Open File → test_geogebra.html

# 3. Or test in actual app
Visit: http://localhost:5000/manage_questions/TestExam
Select: "Graph Sketching (GeoGebra)"
Check: GeoGebra iframe loads
```

---

## 📞 If Still Not Working

**Provide these details:**
1. Browser console errors (F12 → Console)
2. Network tab errors (F12 → Network)
3. Whether test_geogebra.html loads
4. Whether direct GeoGebra access works
5. If using ngrok, share ngrok URL

**Common solutions:**
- Clear browser cache (Ctrl + Shift + Delete)
- Try incognito mode (Ctrl + Shift + N)
- Disable browser extensions temporarily
- Check firewall/antivirus blocking
- Verify internet connection stable

---

**GeoGebra should now load correctly!** 🎉

If you see the full GeoGebra interface with tools, input bar, and graph paper, the fix is working.
