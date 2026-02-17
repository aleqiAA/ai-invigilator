// Enhanced Dashboard Animations
function initDashboardAnimations() {
    const canvas = document.getElementById('pencil-bg');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Enhanced particle system with more variety
    const particles = [];
    const particleCount = 120;

    class Particle {
        constructor() {
            this.reset();
            this.y = Math.random() * canvas.height;
            this.opacity = Math.random() * 0.5 + 0.2;
            this.type = Math.random() > 0.7 ? 'glow' : 'standard';
            this.pulsePhase = Math.random() * Math.PI * 2;
            this.pulseSpeed = (Math.random() * 0.02) + 0.01;
        }

        reset() {
            this.x = Math.random() * canvas.width;
            this.y = -10;
            this.size = Math.random() * 4 + 1;
            this.speedY = Math.random() * 1.5 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.8;
            
            // More varied colors
            const colors = [
                `rgba(0, 168, 168, ${this.opacity})`,
                `rgba(20, 184, 166, ${this.opacity})`,
                `rgba(56, 189, 248, ${this.opacity})`,
                `rgba(139, 92, 246, ${this.opacity})`
            ];
            this.color = colors[Math.floor(Math.random() * colors.length)];
        }

        update() {
            this.y += this.speedY;
            this.x += this.speedX;

            if (this.type === 'glow') {
                this.pulsePhase += this.pulseSpeed;
                this.currentSize = this.size + Math.sin(this.pulsePhase) * 1.5;
            } else {
                this.currentSize = this.size;
            }

            if (this.y > canvas.height) this.reset();
            if (this.x < -20 || this.x > canvas.width + 20) this.reset();
        }

        draw() {
            if (this.type === 'glow') {
                // Create glow effect
                const gradient = ctx.createRadialGradient(
                    this.x, this.y, 0,
                    this.x, this.y, this.currentSize * 3
                );
                gradient.addColorStop(0, this.color.replace(')', ', 0.8)').replace('rgba', 'rgba'));
                gradient.addColorStop(1, this.color.replace(')', ', 0)').replace('rgba', 'rgba'));
                
                ctx.fillStyle = gradient;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.currentSize * 3, 0, Math.PI * 2);
                ctx.fill();
            }
            
            // Standard particle
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.currentSize, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // Initialize particles
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }

    // Enhanced floating geometric shapes
    const shapes = [];
    const shapeCount = 15;

    class Shape {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 70 + 30;
            this.rotation = Math.random() * Math.PI * 2;
            this.rotationSpeed = (Math.random() - 0.5) * 0.03;
            this.speedX = (Math.random() - 0.5) * 0.7;
            this.speedY = (Math.random() - 0.5) * 0.7;
            this.sides = Math.floor(Math.random() * 4) + 3; // 3-6 sides
            this.opacity = Math.random() * 0.2 + 0.05;
            this.color = `rgba(${Math.floor(Math.random() * 100 + 100)}, ${Math.floor(Math.random() * 100 + 100)}, ${Math.floor(Math.random() * 100 + 150)}, ${this.opacity})`;
            this.pulsePhase = Math.random() * Math.PI * 2;
            this.pulseSpeed = (Math.random() * 0.01) + 0.005;
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.rotation += this.rotationSpeed;
            this.pulsePhase += this.pulseSpeed;
            this.currentSize = this.size + Math.sin(this.pulsePhase) * 5;

            if (this.x < -this.currentSize * 2) this.x = canvas.width + this.currentSize * 2;
            if (this.x > canvas.width + this.currentSize * 2) this.x = -this.currentSize * 2;
            if (this.y < -this.currentSize * 2) this.y = canvas.height + this.currentSize * 2;
            if (this.y > canvas.height + this.currentSize * 2) this.y = -this.currentSize * 2;
        }

        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);
            
            // Create gradient
            const gradient = ctx.createLinearGradient(-this.currentSize, -this.currentSize, this.currentSize, this.currentSize);
            gradient.addColorStop(0, this.color);
            gradient.addColorStop(1, this.color.replace(')', ', 0.7)').replace('rgba', 'rgba'));
            
            ctx.strokeStyle = `rgba(255, 255, 255, ${this.opacity * 0.7})`;
            ctx.fillStyle = gradient;
            ctx.lineWidth = 2;

            ctx.beginPath();
            for (let i = 0; i < this.sides; i++) {
                const angle = (i / this.sides) * Math.PI * 2;
                const x = Math.cos(angle) * this.currentSize;
                const y = Math.sin(angle) * this.currentSize;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            
            // Add inner glow
            ctx.shadowColor = this.color;
            ctx.shadowBlur = 15;
            ctx.stroke();
            
            ctx.restore();
        }
    }

    for (let i = 0; i < shapeCount; i++) {
        shapes.push(new Shape());
    }

    // Enhanced connection lines between particles
    function drawConnections() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 120) {
                    const alpha = 0.15 * (1 - distance / 120);
                    ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
                    ctx.lineWidth = 0.5 + (1 - distance / 120) * 1.5;
                    
                    // Add gradient to line
                    const gradient = ctx.createLinearGradient(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
                    gradient.addColorStop(0, `rgba(56, 189, 248, ${alpha})`);
                    gradient.addColorStop(1, `rgba(139, 92, 246, ${alpha})`);
                    ctx.strokeStyle = gradient;
                    
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }
    }

    // Enhanced wave effect with multiple layers
    let waveOffset = 0;
    function drawWave() {
        // Multiple wave layers
        for (let layer = 0; layer < 3; layer++) {
            const yPos = canvas.height * (0.6 + layer * 0.1);
            const amplitude = 30 + layer * 10;
            const frequency = 0.01 + layer * 0.005;
            const alpha = 0.05 + layer * 0.03;
            
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
            ctx.lineWidth = 1 + layer * 0.5;
            ctx.beginPath();

            for (let x = 0; x < canvas.width; x += 5) {
                const y = yPos + Math.sin((x + waveOffset * (1 + layer * 0.3)) * frequency) * amplitude;
                if (x === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
        }
        
        waveOffset += 1.5;
    }

    // Enhanced starfield effect
    const stars = [];
    const starCount = 100;
    
    class Star {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 1.5;
            this.opacity = Math.random() * 0.5 + 0.3;
            this.twinklePhase = Math.random() * Math.PI * 2;
            this.twinkleSpeed = (Math.random() * 0.03) + 0.01;
        }
        
        update() {
            this.twinklePhase += this.twinkleSpeed;
            this.currentOpacity = this.opacity + Math.sin(this.twinklePhase) * 0.2;
        }
        
        draw() {
            ctx.fillStyle = `rgba(255, 255, 255, ${this.currentOpacity})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    for (let i = 0; i < starCount; i++) {
        stars.push(new Star());
    }

    // Animation loop
    function animate() {
        // Create fade effect for trails
        ctx.fillStyle = 'rgba(15, 23, 42, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        drawWave();

        shapes.forEach(shape => {
            shape.update();
            shape.draw();
        });

        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });

        stars.forEach(star => {
            star.update();
            star.draw();
        });

        drawConnections();

        requestAnimationFrame(animate);
    }

    animate();

    // Enhanced resize handler
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });

    // Enhanced interactive hover effect on cards with ripple effect
    const cards = document.querySelectorAll('.stat-box, .glass-card, .session-card, .exam-card, .action-btn');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
            this.style.boxShadow = '0 20px 60px rgba(0, 168, 168, 0.4), 0 0 30px rgba(56, 189, 248, 0.2)';
            
            // Add ripple effect
            const rect = this.getBoundingClientRect();
            const ripple = document.createElement('div');
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = 'inherit';
            ripple.style.width = '100%';
            ripple.style.height = '100%';
            ripple.style.top = '0';
            ripple.style.left = '0';
            ripple.style.pointerEvents = 'none';
            ripple.style.overflow = 'hidden';
            ripple.style.zIndex = '-1';
            ripple.style.background = 'radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%)';
            ripple.style.opacity = '0';
            ripple.style.transition = 'opacity 0.3s ease';
            
            if (!this.contains(ripple)) {
                this.style.position = 'relative';
                this.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.style.opacity = '1';
                }, 10);
            }
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
            
            // Remove ripple effect
            const ripple = this.querySelector('div[style*="radial-gradient"]');
            if (ripple) {
                ripple.style.opacity = '0';
                setTimeout(() => {
                    if (ripple.parentNode) {
                        ripple.parentNode.removeChild(ripple);
                    }
                }, 300);
            }
        });
    });
    
    // Enhanced scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                entry.target.style.animation = 'fadeIn 0.8s ease forwards, scaleIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards';
            }
        });
    }, observerOptions);
    
    // Observe stat boxes and other elements
    document.querySelectorAll('.stat-box, .action-btn, .glass-card').forEach(el => {
        observer.observe(el);
    });
}

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboardAnimations);
} else {
    initDashboardAnimations();
}

// Enhanced Loading Spinner Animation
function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = `
        <div class="spinner-circle">
            <div class="spinner-ring"></div>
            <div class="spinner-core"></div>
        </div>
        <div class="spinner-text">Loading...</div>
    `;
    spinner.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(15, 23, 42, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        flex-direction: column;
        gap: 20px;
    `;
    document.body.appendChild(spinner);
    
    // Add spinner styles dynamically
    const style = document.createElement('style');
    style.textContent = `
        .spinner-circle {
            position: relative;
            width: 60px;
            height: 60px;
        }
        .spinner-ring {
            position: absolute;
            width: 100%;
            height: 100%;
            border: 4px solid transparent;
            border-top: 4px solid #00a8a8;
            border-radius: 50%;
            animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
        }
        .spinner-core {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 30px;
            height: 30px;
            background: #00a8a8;
            border-radius: 50%;
            animation: pulse 1.5s ease-in-out infinite alternate;
        }
        .spinner-text {
            color: white;
            font-family: 'Poppins', sans-serif;
            font-size: 16px;
            font-weight: 500;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes pulse {
            0% { transform: translate(-50%, -50%) scale(1); opacity: 0.7; }
            100% { transform: translate(-50%, -50%) scale(1.1); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}

function hideLoadingSpinner() {
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) {
        spinner.style.opacity = '0';
        spinner.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
            if (spinner.parentNode) {
                spinner.parentNode.removeChild(spinner);
            }
        }, 300);
    }
}

// Initialize spinner during data fetch
// Example usage:
// showLoadingSpinner();
// fetchData().then(() => hideLoadingSpinner());
