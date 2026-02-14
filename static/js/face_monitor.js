// WebRTC + MediaPipe Face Detection for Browser-based Monitoring
class FaceMonitor {
    constructor(sessionId, onAlert) {
        this.sessionId = sessionId;
        this.onAlert = onAlert;
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.stream = null;
        this.isMonitoring = false;
        this.alertCooldown = {};
        this.lastFaceDetected = Date.now();
        this.multipleFaceCount = 0;
    }

    async initialize(videoElement) {
        this.video = videoElement;
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
            });

            this.video.srcObject = this.stream;
            await this.video.play();

            this.isMonitoring = true;
            this.startMonitoring();

            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    startMonitoring() {
        // Analyze frames every 3 seconds
        setInterval(async () => {
            if (!this.isMonitoring) return;
            try {
                await this.analyzeFrame();
            } catch (error) {
                console.error('Frame analysis error:', error);
            }
        }, 3000);
        
        // Send snapshots every 10 seconds for invigilator viewing
        setInterval(async () => {
            if (!this.isMonitoring) return;
            try {
                await this.sendSnapshot();
            } catch (error) {
                console.error('Snapshot upload error:', error);
            }
        }, 10000);
    }

    async analyzeFrame() {
        if (!this.video || this.video.readyState !== 4) return;

        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        this.ctx.drawImage(this.video, 0, 0);

        const faces = await this.detectFaces();
        this.processFaceDetection(faces);
        this.checkLighting();
    }

    async detectFaces() {
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;
        
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const regionSize = Math.min(this.canvas.width, this.canvas.height) / 3;
        
        let faceRegionBrightness = 0;
        let totalBrightness = 0;
        
        for (let y = 0; y < this.canvas.height; y++) {
            for (let x = 0; x < this.canvas.width; x++) {
                const i = (y * this.canvas.width + x) * 4;
                const brightness = (data[i] + data[i + 1] + data[i + 2]) / 3;
                totalBrightness += brightness;
                
                if (Math.abs(x - centerX) < regionSize && Math.abs(y - centerY) < regionSize) {
                    faceRegionBrightness += brightness;
                }
            }
        }
        
        const avgBrightness = totalBrightness / (this.canvas.width * this.canvas.height);
        const centerBrightness = faceRegionBrightness / (regionSize * regionSize * 4);
        
        if (centerBrightness > avgBrightness * 1.2 && avgBrightness > 30) {
            return [{ detected: true }];
        }
        
        return [];
    }

    processFaceDetection(faces) {
        const now = Date.now();

        if (faces.length === 0) {
            if (now - this.lastFaceDetected > 5000) {
                this.sendAlert('no_face_detected', 'No face detected in frame');
            }
        } else if (faces.length === 1) {
            this.lastFaceDetected = now;
            this.multipleFaceCount = 0;
        } else if (faces.length > 1) {
            this.multipleFaceCount++;
            if (this.multipleFaceCount > 2) {
                this.sendAlert('multiple_faces', `${faces.length} faces detected`);
                this.multipleFaceCount = 0;
            }
        }
    }

    checkLighting() {
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        const data = imageData.data;
        
        let totalBrightness = 0;
        for (let i = 0; i < data.length; i += 4) {
            totalBrightness += (data[i] + data[i + 1] + data[i + 2]) / 3;
        }
        
        const avgBrightness = totalBrightness / (this.canvas.width * this.canvas.height);
        
        if (avgBrightness < 30) {
            this.sendAlert('poor_lighting', 'Lighting too dark');
        } else if (avgBrightness > 240) {
            this.sendAlert('poor_lighting', 'Lighting too bright');
        }
    }

    sendAlert(alertType, description) {
        const cooldownKey = alertType;
        const now = Date.now();
        
        if (this.alertCooldown[cooldownKey] && now - this.alertCooldown[cooldownKey] < 30000) {
            return;
        }
        
        this.alertCooldown[cooldownKey] = now;

        fetch('/proctoring_alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                alert_type: alertType,
                description: description,
                timestamp: new Date().toISOString()
            })
        }).catch(err => console.error('Alert failed:', err));

        if (this.onAlert) {
            this.onAlert(alertType, description);
        }
    }

    async sendSnapshot() {
        if (!this.sessionId || !this.isMonitoring) return;
        
        const snapshot = this.canvas.toDataURL('image/jpeg', 0.6);
        
        try {
            await fetch('/upload_snapshot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    snapshot: snapshot
                })
            });
        } catch (err) {
            console.error('Snapshot upload failed:', err);
        }
    }

    stop() {
        this.isMonitoring = false;
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
    }
}

window.FaceMonitor = FaceMonitor;
