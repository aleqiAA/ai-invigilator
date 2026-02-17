// Unique Floating UI Template with Distinct Colors
function initFloatingUITemplate() {
    const canvas = document.getElementById('pencil-bg');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Floating orbs with distinct colors (purple, pink, orange)
    const orbs = [];
    class Orb {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.radius = Math.random() * 100 + 50;
            this.speedX = (Math.random() - 0.5) * 0.3;
            this.speedY = (Math.random() - 0.5) * 0.3;
            
            const colors = [
                { r: 168, g: 85, b: 247 },  // Purple
                { r: 236, g: 72, b: 153 },  // Pink
                { r: 251, g: 146, b: 60 }   // Orange
            ];
            this.color = colors[Math.floor(Math.random() * colors.length)];
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;

            if (this.x < -this.radius) this.x = canvas.width + this.radius;
            if (this.x > canvas.width + this.radius) this.x = -this.radius;
            if (this.y < -this.radius) this.y = canvas.height + this.radius;
            if (this.y > canvas.height + this.radius) this.y = -this.radius;
        }

        draw() {
            const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.radius);
            gradient.addColorStop(0, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0.15)`);
            gradient.addColorStop(0.5, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0.08)`);
            gradient.addColorStop(1, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0)`);
            
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    for (let i = 0; i < 8; i++) {
        orbs.push(new Orb());
    }

    // Neon grid lines
    const gridLines = [];
    class GridLine {
        constructor(isVertical) {
            this.isVertical = isVertical;
            this.position = Math.random() * (isVertical ? canvas.width : canvas.height);
            this.offset = 0;
            this.speed = 0.5;
            this.color = `rgba(251, 146, 60, 0.2)`; // Orange
        }

        update() {
            this.offset += this.speed;
            if (this.offset > 50) this.offset = 0;
        }

        draw() {
            ctx.strokeStyle = this.color;
            ctx.lineWidth = 2;
            ctx.setLineDash([10, 20]);
            ctx.lineDashOffset = -this.offset;
            
            ctx.beginPath();
            if (this.isVertical) {
                ctx.moveTo(this.position, 0);
                ctx.lineTo(this.position, canvas.height);
            } else {
                ctx.moveTo(0, this.position);
                ctx.lineTo(canvas.width, this.position);
            }
            ctx.stroke();
            ctx.setLineDash([]);
        }
    }

    for (let i = 0; i < 5; i++) {
        gridLines.push(new GridLine(true));
        gridLines.push(new GridLine(false));
    }

    // Floating hexagons
    const hexagons = [];
    class Hexagon {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 40 + 20;
            this.rotation = Math.random() * Math.PI * 2;
            this.rotationSpeed = (Math.random() - 0.5) * 0.01;
            this.speedX = (Math.random() - 0.5) * 0.4;
            this.speedY = (Math.random() - 0.5) * 0.4;
            this.color = `rgba(168, 85, 247, ${Math.random() * 0.3 + 0.1})`; // Purple
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.rotation += this.rotationSpeed;

            if (this.x < -this.size) this.x = canvas.width + this.size;
            if (this.x > canvas.width + this.size) this.x = -this.size;
            if (this.y < -this.size) this.y = canvas.height + this.size;
            if (this.y > canvas.height + this.size) this.y = -this.size;
        }

        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);
            
            ctx.strokeStyle = `rgba(168, 85, 247, 0.4)`;
            ctx.fillStyle = this.color;
            ctx.lineWidth = 2;
            
            ctx.beginPath();
            for (let i = 0; i < 6; i++) {
                const angle = (i / 6) * Math.PI * 2;
                const x = Math.cos(angle) * this.size;
                const y = Math.sin(angle) * this.size;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            ctx.restore();
        }
    }

    for (let i = 0; i < 15; i++) {
        hexagons.push(new Hexagon());
    }

    // Glowing stars
    const stars = [];
    class Star {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 3 + 1;
            this.opacity = Math.random();
            this.fadeSpeed = (Math.random() - 0.5) * 0.02;
            this.color = `rgba(236, 72, 153, ${this.opacity})`; // Pink
        }

        update() {
            this.opacity += this.fadeSpeed;
            if (this.opacity <= 0 || this.opacity >= 1) this.fadeSpeed *= -1;
            this.color = `rgba(236, 72, 153, ${this.opacity})`;
        }

        draw() {
            ctx.fillStyle = this.color;
            ctx.shadowBlur = 10;
            ctx.shadowColor = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.shadowBlur = 0;
        }
    }

    for (let i = 0; i < 50; i++) {
        stars.push(new Star());
    }

    // Animation loop
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        orbs.forEach(orb => {
            orb.update();
            orb.draw();
        });

        gridLines.forEach(line => {
            line.update();
            line.draw();
        });

        hexagons.forEach(hex => {
            hex.update();
            hex.draw();
        });

        stars.forEach(star => {
            star.update();
            star.draw();
        });

        requestAnimationFrame(animate);
    }

    animate();

    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFloatingUITemplate);
} else {
    initFloatingUITemplate();
}
