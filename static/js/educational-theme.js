// Clean Educational Canvas Background
function initEducationalTheme() {
    const canvas = document.getElementById('pencil-bg');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Subtle grid pattern (like notebook paper)
    function drawGrid() {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
        ctx.lineWidth = 1;
        
        // Vertical lines
        for (let x = 0; x < canvas.width; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        
        // Horizontal lines
        for (let y = 0; y < canvas.height; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }

    // Floating book icons
    const books = [];
    class Book {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 20 + 15;
            this.speedY = Math.random() * 0.3 + 0.1;
            this.opacity = Math.random() * 0.1 + 0.05;
        }

        update() {
            this.y += this.speedY;
            if (this.y > canvas.height + 50) {
                this.y = -50;
                this.x = Math.random() * canvas.width;
            }
        }

        draw() {
            ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
            ctx.fillRect(this.x, this.y, this.size, this.size * 1.3);
            ctx.strokeStyle = `rgba(255, 255, 255, ${this.opacity * 2})`;
            ctx.strokeRect(this.x, this.y, this.size, this.size * 1.3);
        }
    }

    for (let i = 0; i < 20; i++) {
        books.push(new Book());
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawGrid();
        
        books.forEach(book => {
            book.update();
            book.draw();
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
    document.addEventListener('DOMContentLoaded', initEducationalTheme);
} else {
    initEducationalTheme();
}
