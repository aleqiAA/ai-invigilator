// Pencil.js animated background graphics
const { Scene, Circle, Rectangle, Polygon, Color } = Pencil;

function initPencilBackground(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const scene = new Scene(container, {
        fill: 'transparent'
    });

    // Floating circles
    for (let i = 0; i < 15; i++) {
        const circle = new Circle([Math.random() * window.innerWidth, Math.random() * window.innerHeight], 
            Math.random() * 50 + 20);
        circle.options.fill = new Color(0, 128, 128, Math.random() * 0.1 + 0.05);
        circle.options.stroke = new Color(255, 255, 255, 0.1);
        scene.add(circle);

        // Animate
        setInterval(() => {
            circle.position.x += (Math.random() - 0.5) * 2;
            circle.position.y += (Math.random() - 0.5) * 2;
            
            if (circle.position.x < -100) circle.position.x = window.innerWidth + 100;
            if (circle.position.x > window.innerWidth + 100) circle.position.x = -100;
            if (circle.position.y < -100) circle.position.y = window.innerHeight + 100;
            if (circle.position.y > window.innerHeight + 100) circle.position.y = -100;
        }, 50);
    }

    // Geometric shapes
    for (let i = 0; i < 8; i++) {
        const points = [];
        const sides = Math.floor(Math.random() * 3) + 3;
        for (let j = 0; j < sides; j++) {
            const angle = (j / sides) * Math.PI * 2;
            const radius = Math.random() * 30 + 20;
            points.push([Math.cos(angle) * radius, Math.sin(angle) * radius]);
        }
        
        const poly = new Polygon([Math.random() * window.innerWidth, Math.random() * window.innerHeight], points);
        poly.options.fill = new Color(0, 168, 168, Math.random() * 0.08 + 0.03);
        poly.options.stroke = new Color(255, 255, 255, 0.15);
        scene.add(poly);

        // Rotate animation
        let rotation = 0;
        setInterval(() => {
            rotation += 0.01;
            poly.rotation = rotation;
            poly.position.x += Math.sin(rotation) * 0.5;
            poly.position.y += Math.cos(rotation) * 0.5;
        }, 50);
    }

    scene.startLoop();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initPencilBackground('pencil-bg');
});
