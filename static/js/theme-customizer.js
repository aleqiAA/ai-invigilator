// Theme Customization System
class ThemeCustomizer {
    constructor() {
        this.themes = {
            'default': {
                name: 'Default',
                primary: '#008080',
                secondary: '#0ea5e9',
                accent: '#f97316',
                success: '#10b981',
                warning: '#f59e0b',
                danger: '#ef4444'
            },
            'dark-blue': {
                name: 'Dark Blue',
                primary: '#1e40af',
                secondary: '#3b82f6',
                accent: '#f97316',
                success: '#10b981',
                warning: '#f59e0b',
                danger: '#ef4444'
            },
            'purple': {
                name: 'Purple',
                primary: '#7e22ce',
                secondary: '#a855f7',
                accent: '#ec4899',
                success: '#10b981',
                warning: '#f59e0b',
                danger: '#ef4444'
            },
            'green': {
                name: 'Green',
                primary: '#059669',
                secondary: '#10b981',
                accent: '#f59e09',
                success: '#10b981',
                warning: '#f59e0b',
                danger: '#ef4444'
            }
        };
        
        this.currentTheme = localStorage.getItem('selectedTheme') || 'default';
        this.init();
    }
    
    init() {
        this.applyTheme(this.currentTheme);
        this.createThemeSelector();
        this.createThemeControls();
    }
    
    applyTheme(themeName) {
        const theme = this.themes[themeName];
        if (!theme) return;
        
        // Apply CSS variables
        document.documentElement.style.setProperty('--primary', theme.primary);
        document.documentElement.style.setProperty('--secondary', theme.secondary);
        document.documentElement.style.setProperty('--accent', theme.accent);
        document.documentElement.style.setProperty('--success', theme.success);
        document.documentElement.style.setProperty('--warning', theme.warning);
        document.documentElement.style.setProperty('--danger', theme.danger);
        
        // Update background gradients
        document.body.style.background = `linear-gradient(135deg, ${this.adjustColor(theme.primary, -40)} 0%, ${this.adjustColor(theme.primary, -20)} 25%, ${this.adjustColor(theme.primary, -10)} 50%, ${this.adjustColor(theme.primary, 10)} 75%, ${this.adjustColor(theme.primary, -40)} 100%)`;
        
        // Save to localStorage
        localStorage.setItem('selectedTheme', themeName);
        this.currentTheme = themeName;
        
        // Trigger custom event
        document.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: themeName } }));
    }
    
    adjustColor(color, percent) {
        // Convert hex to RGB
        let R = parseInt(color.substring(1, 3), 16);
        let G = parseInt(color.substring(3, 5), 16);
        let B = parseInt(color.substring(5, 7), 16);
        
        // Adjust each component
        R = Math.min(255, Math.max(0, R + R * percent / 100));
        G = Math.min(255, Math.max(0, G + G * percent / 100));
        B = Math.min(255, Math.max(0, B + B * percent / 100));
        
        // Convert back to hex
        return `#${Math.round(R).toString(16).padStart(2, '0')}${Math.round(G).toString(16).padStart(2, '0')}${Math.round(B).toString(16).padStart(2, '0')}`;
    }
    
    createThemeSelector() {
        // Create theme selector dropdown
        const themeSelector = document.createElement('div');
        themeSelector.id = 'theme-selector';
        themeSelector.innerHTML = `
            <div class="theme-toggle-btn">
                <i class="fas fa-palette"></i>
            </div>
            <div class="theme-options">
                ${Object.entries(this.themes).map(([key, theme]) => 
                    `<div class="theme-option ${key === this.currentTheme ? 'active' : ''}" data-theme="${key}">
                        <div class="theme-preview" style="background: linear-gradient(45deg, ${theme.primary}, ${theme.secondary});"></div>
                        <span>${theme.name}</span>
                    </div>`
                ).join('')}
            </div>
        `;
        
        // Add CSS for theme selector
        const style = document.createElement('style');
        style.textContent = `
            #theme-selector {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10000;
                font-family: 'Poppins', sans-serif;
            }
            
            .theme-toggle-btn {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                transition: all 0.3s ease;
            }
            
            .theme-toggle-btn:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 25px rgba(0, 0, 0, 0.4);
            }
            
            .theme-options {
                position: absolute;
                bottom: 70px;
                right: 0;
                background: rgba(30, 41, 59, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                padding: 15px;
                width: 200px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                display: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            #theme-selector.active .theme-options {
                display: block;
            }
            
            .theme-option {
                display: flex;
                align-items: center;
                padding: 10px;
                border-radius: 10px;
                margin-bottom: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .theme-option:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            
            .theme-option.active {
                background: rgba(0, 128, 128, 0.3);
                border: 1px solid rgba(0, 128, 128, 0.5);
            }
            
            .theme-preview {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                margin-right: 10px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            .theme-option span {
                color: white;
                font-size: 14px;
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(themeSelector);
        
        // Add event listeners
        const toggleBtn = themeSelector.querySelector('.theme-toggle-btn');
        toggleBtn.addEventListener('click', () => {
            themeSelector.classList.toggle('active');
        });
        
        const themeOptions = themeSelector.querySelectorAll('.theme-option');
        themeOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const themeName = e.currentTarget.getAttribute('data-theme');
                this.applyTheme(themeName);
                
                // Update active class
                themeOptions.forEach(opt => opt.classList.remove('active'));
                e.currentTarget.classList.add('active');
                
                // Close dropdown
                themeSelector.classList.remove('active');
            });
        });
        
        // Close dropdown when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!themeSelector.contains(e.target)) {
                themeSelector.classList.remove('active');
            }
        });
    }
    
    createThemeControls() {
        // Create advanced theme controls
        const themeControls = document.createElement('div');
        themeControls.id = 'theme-controls';
        themeControls.innerHTML = `
            <div class="theme-control-panel">
                <h3>Theme Customization</h3>
                <div class="control-group">
                    <label>Primary Color</label>
                    <input type="color" id="primary-color" value="${this.themes[this.currentTheme].primary}">
                </div>
                <div class="control-group">
                    <label>Secondary Color</label>
                    <input type="color" id="secondary-color" value="${this.themes[this.currentTheme].secondary}">
                </div>
                <div class="control-group">
                    <label>Accent Color</label>
                    <input type="color" id="accent-color" value="${this.themes[this.currentTheme].accent}">
                </div>
                <button id="apply-custom-theme" class="btn-modern">Apply Custom Theme</button>
                <button id="reset-theme" class="btn-modern btn-danger">Reset to Default</button>
            </div>
        `;
        
        // Add CSS for theme controls
        const controlStyle = document.createElement('style');
        controlStyle.textContent = `
            .theme-control-panel {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(30, 41, 59, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 25px;
                width: 350px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.2);
                display: none;
                z-index: 10001;
            }
            
            .theme-control-panel.active {
                display: block;
            }
            
            .theme-control-panel h3 {
                color: white;
                margin-top: 0;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .control-group {
                margin-bottom: 15px;
            }
            
            .control-group label {
                display: block;
                color: rgba(255, 255, 255, 0.8);
                margin-bottom: 5px;
                font-size: 14px;
            }
            
            .control-group input[type="color"] {
                width: 100%;
                height: 40px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }
            
            #apply-custom-theme, #reset-theme {
                width: 100%;
                margin-top: 10px;
            }
            
            #reset-theme {
                margin-top: 5px;
            }
            
            .overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 10000;
                display: none;
            }
            
            .overlay.active {
                display: block;
            }
        `;
        document.head.appendChild(controlStyle);
        
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'overlay';
        document.body.appendChild(overlay);
        
        document.body.appendChild(themeControls);
        
        // Add event listeners for theme controls
        document.getElementById('apply-custom-theme').addEventListener('click', () => {
            const primary = document.getElementById('primary-color').value;
            const secondary = document.getElementById('secondary-color').value;
            const accent = document.getElementById('accent-color').value;
            
            // Create custom theme
            this.themes.custom = {
                name: 'Custom',
                primary: primary,
                secondary: secondary,
                accent: accent,
                success: '#10b981',
                warning: '#f59e0b',
                danger: '#ef4444'
            };
            
            this.applyTheme('custom');
            
            // Update theme selector
            this.updateThemeSelector();
            
            // Close panel
            themeControls.classList.remove('active');
            overlay.classList.remove('active');
        });
        
        document.getElementById('reset-theme').addEventListener('click', () => {
            this.applyTheme('default');
            
            // Reset color pickers
            document.getElementById('primary-color').value = this.themes.default.primary;
            document.getElementById('secondary-color').value = this.themes.default.secondary;
            document.getElementById('accent-color').value = this.themes.default.accent;
            
            // Close panel
            themeControls.classList.remove('active');
            overlay.classList.remove('active');
        });
        
        // Add button to open theme controls
        const customizeBtn = document.createElement('div');
        customizeBtn.innerHTML = '<i class="fas fa-sliders-h"></i>';
        customizeBtn.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            cursor: pointer;
            font-size: 18px;
            z-index: 10002;
        `;
        
        customizeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            themeControls.classList.add('active');
            overlay.classList.add('active');
        });
        
        // Add to theme selector
        document.querySelector('#theme-selector').appendChild(customizeBtn);
        
        // Close panel when clicking overlay
        overlay.addEventListener('click', () => {
            themeControls.classList.remove('active');
            overlay.classList.remove('active');
        });
    }
    
    updateThemeSelector() {
        const themeOptionsContainer = document.querySelector('.theme-options');
        if (!themeOptionsContainer) return;
        
        themeOptionsContainer.innerHTML = Object.entries(this.themes).map(([key, theme]) => 
            `<div class="theme-option ${key === this.currentTheme ? 'active' : ''}" data-theme="${key}">
                <div class="theme-preview" style="background: linear-gradient(45deg, ${theme.primary}, ${theme.secondary});"></div>
                <span>${theme.name}</span>
            </div>`
        ).join('');
        
        // Re-add event listeners
        const themeOptions = themeOptionsContainer.querySelectorAll('.theme-option');
        themeOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const themeName = e.currentTarget.getAttribute('data-theme');
                this.applyTheme(themeName);
                
                // Update active class
                themeOptions.forEach(opt => opt.classList.remove('active'));
                e.currentTarget.classList.add('active');
                
                // Close dropdown
                document.getElementById('theme-selector').classList.remove('active');
            });
        });
    }
}

// Initialize theme customizer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ThemeCustomizer();
});