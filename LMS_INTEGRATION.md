# LMS Integration Guide

## Overview
Integrate AI Invigilator with Canvas, Moodle, Blackboard, or custom LMS.

## Integration Methods

### 1. REST API (Recommended)
**Base URL:** `https://your-domain.com/api/v1`

**Authentication:** Add header `X-API-Key: your-api-key`

#### Create Student
```http
POST /api/v1/students
Content-Type: application/json

{
  "name": "John Doe",
  "student_id": "12345",
  "email": "john@university.edu",
  "password": "optional"
}
```

#### Schedule Exam
```http
POST /api/v1/exams
Content-Type: application/json

{
  "student_id": "12345",
  "exam_name": "CS 101 Midterm"
}

Response:
{
  "session_id": 42,
  "exam_url": "/exam/12345?session_id=42",
  "embed_url": "/embed/exam/42"
}
```

#### Get Results
```http
GET /api/v1/exams/42

Response:
{
  "session_id": 42,
  "student_id": "12345",
  "status": "completed",
  "integrity_score": 85,
  "alerts": [...]
}
```

### 2. LTI 1.3 (Canvas/Moodle)
**Coming soon** - Full LTI integration for single sign-on

### 3. Iframe Embed
Embed monitoring widget directly in LMS:

```html
<iframe 
  src="https://your-domain.com/embed/exam/42" 
  width="100%" 
  height="600"
  allow="camera; microphone"
></iframe>
```

### 4. Webhooks
Receive real-time alerts:

```http
POST /api/v1/webhooks/alerts
{
  "url": "https://your-lms.com/webhook",
  "events": ["alert_created", "exam_ended"]
}
```

## Example: Canvas Integration

```javascript
// In Canvas course, add external tool
const examUrl = await fetch('https://ai-invigilator.com/api/v1/exams', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    student_id: canvas_user_id,
    exam_name: 'Midterm Exam'
  })
});

const { embed_url } = await examUrl.json();

// Redirect student to exam
window.location.href = embed_url;
```

## Security
- API keys rotate every 90 days
- HTTPS required
- CORS configured per domain
- Rate limiting: 100 req/min

## Support
Email: support@ai-invigilator.com
Docs: https://docs.ai-invigilator.com
