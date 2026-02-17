// Enhanced Background Animations for AI Invigilator
class EnhancedBackground {
    constructor(canvasId = 'background-canvas') {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            // Create canvas if it doesn't exist
            this.canvas = document.createElement('canvas');
            this.canvas.id = canvasId;
            this.canvas.style.position = 'fixed';
            this.canvas.style.top = '0';
            this.canvas.style.left = '0';
            this.canvas.style.width = '100%';
            this.canvas.style.height = '100%';
            this.canvas.style.zIndex = '-1';
            this.canvas.style.pointerEvents = 'none';
            document.body.appendChild(this.canvas);
        }

        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.shapes = [];
        this.connections = [];
        this.mousePos = { x: 0, y: 0 };
        this.resizeCanvas();
        this.init();
    }

    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    init() {
        this.createParticles(100);
        this.createShapes(15);
        this.setupEventListeners();
        this.animate();
    }

    setupEventListeners() {
        window.addEventListener('resize', () => this.resizeCanvas());
        
        document.addEventListener('mousemove', (e) => {
            this.mousePos = { x: e.clientX, y: e.clientY };
        });
    }

    createParticles(count) {
        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * 3 + 1,
                speedX: (Math.random() - 0.5) * 0.5,
                speedY: (Math.random() - 0.5) * 0.5,
                color: `rgba(0, 168, 168, ${Math.random() * 0.3 + 0.1})`,
                originalOpacity: Math.random() * 0.3 + 0.1,
                pulseOffset: Math.random() * Math.PI * 2,
                pulseSpeed: Math.random() * 0.02 + 0.01
            });
        }
    }

    createShapes(count) {
        const colors = [
            `rgba(0, 128, 128, 0.1)`, 
            `rgba(20, 184, 166, 0.1)`, 
            `rgba(6, 182, 212, 0.1)`,
            `rgba(59, 130, 246, 0.1)`
        ];
        
        for (let i = 0; i < count; i++) {
            const sides = Math.floor(Math.random() * 4) + 3; // Triangle to hexagon
            this.shapes.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * 60 + 30,
                rotation: Math.random() * Math.PI * 2,
                rotationSpeed: (Math.random() - 0.5) * 0.01,
                speedX: (Math.random() - 0.5) * 0.3,
                speedY: (Math.random() - 0.5) * 0.3,
                sides: sides,
                color: colors[Math.floor(Math.random() * colors.length)],
                originalColor: colors[Math.floor(Math.random() * colors.length)],
                pulseOffset: Math.random() * Math.PI * 2,
                pulseSpeed: Math.random() * 0.005 + 0.005
            });
        }
    }

    updateParticles() {
        this.particles.forEach(p => {
            p.x += p.speedX;
            p.y += p.speedY;

            // Wrap around edges
            if (p.x < 0) p.x = this.canvas.width;
            if (p.x > this.canvas.width) p.x = 0;
            if (p.y < 0) p.y = this.canvas.height;
            if (p.y > this.canvas.height) p.y = 0;

            // Pulsing effect
            const pulse = Math.sin(Date.now() * 0.001 + p.pulseOffset) * 0.1 + 0.9;
            const opacity = p.originalOpacity * pulse;
            p.color = `rgba(0, 168, 168, ${opacity})`;
        });
    }

    updateShapes() {
        this.shapes.forEach(s => {
            s.x += s.speedX;
            s.y += s.speedY;
            s.rotation += s.rotationSpeed;

            // Wrap around edges with buffer
            if (s.x < -s.size) s.x = this.canvas.width + s.size;
            if (s.x > this.canvas.width + s.size) s.x = -s.size;
            if (s.y < -s.size) s.y = this.canvas.height + s.size;
            if (s.y > this.canvas.height + s.size) s.y = -s.size;

            // Pulsing color effect
            const pulse = Math.sin(Date.now() * 0.001 + s.pulseOffset) * 0.05 + 0.95;
            const colorMatch = s.originalColor.match(/[\d\.]+/g);
            if (colorMatch && colorMatch.length >= 4) {
                const r = parseInt(colorMatch[0]);
                const g = parseInt(colorMatch[1]);
                const b = parseInt(colorMatch[2]);
                const originalAlpha = parseFloat(colorMatch[3]);
                const newAlpha = originalAlpha * pulse;
                
                s.color = `rgba(${r}, ${g}, ${b}, ${newAlpha})`;
            }
        });
    }

    drawParticles() {
        this.particles.forEach(p => {
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fillStyle = p.color;
            this.ctx.fill();
        });
    }

    drawShapes() {
        this.shapes.forEach(s => {
            this.ctx.save();
            this.ctx.translate(s.x, s.y);
            this.ctx.rotate(s.rotation);
            
            this.ctx.beginPath();
            for (let i = 0; i < s.sides; i++) {
                const angle = (i / s.sides) * Math.PI * 2;
                const x = Math.cos(angle) * s.size;
                const y = Math.sin(angle) * s.size;
                
                if (i === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            }
            this.ctx.closePath();
            
            this.ctx.fillStyle = s.color;
            this.ctx.fill();
            
            // Subtle stroke
            this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();
            
            this.ctx.restore();
        });
    }

    drawConnections() {
        // Draw connections between nearby particles
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 120) {
                    const opacity = 0.2 * (1 - distance / 120);
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = `rgba(0, 168, 168, ${opacity})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.stroke();
                }
            }
        }
        
        // Draw connection from mouse to nearby particles
        for (let i = 0; i < this.particles.length; i++) {
            const dx = this.particles[i].x - this.mousePos.x;
            const dy = this.particles[i].y - this.mousePos.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 150) {
                const opacity = 0.3 * (1 - distance / 150);
                this.ctx.beginPath();
                this.ctx.strokeStyle = `rgba(255, 255, 255, ${opacity})`;
                this.ctx.lineWidth = 1;
                this.ctx.moveTo(this.mousePos.x, this.mousePos.y);
                this.ctx.lineTo(this.particles[i].x, this.particles[i].y);
                this.ctx.stroke();
            }
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.updateParticles();
        this.updateShapes();
        this.drawShapes();
        this.drawParticles();
        this.drawConnections();

        requestAnimationFrame(() => this.animate());
    }
}

// Initialize background animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure everything is loaded
    setTimeout(() => {
        new EnhancedBackground();
    }, 100);
});