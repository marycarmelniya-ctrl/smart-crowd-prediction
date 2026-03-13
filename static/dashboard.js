document.addEventListener('DOMContentLoaded', () => {

    // UI Elements
    const domLiveClock = document.getElementById('live-clock');
    
    // Cards
    const cardStatus = document.getElementById('card-status');
    const valStatus = document.getElementById('val-status');
    
    const cardCrowd = document.getElementById('card-crowd');
    const valCrowd = document.getElementById('val-crowd');
    
    const valCount = document.getElementById('val-count');
    
    const cardFire = document.getElementById('card-fire');
    const valFire = document.getElementById('val-fire');
    
    // System Status
    const sysDot = document.getElementById('system-dot');
    const sysText = document.getElementById('system-text');

    // Logs
    const logContainer = document.getElementById('log-container');

    // Time Updater
    setInterval(() => {
        const now = new Date();
        domLiveClock.textContent = now.toLocaleTimeString('en-US', { hour12: false });
    }, 1000);

    let lastKnownEvents = [];

    // Helper: Reset Card State
    function resetCardState(cardObj) {
        cardObj.classList.remove('state-safe', 'state-warning', 'state-danger', 'emergency-mode');
    }

    // Polling Function
    async function fetchSystemStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            // Connection Status
            if (data.system_active) {
                sysDot.className = 'status-dot active';
                sysText.textContent = 'Engine Active';
            } else {
                sysDot.className = 'status-dot offline';
                sysText.textContent = 'Engine Offline (Waiting or stopped)';
            }

            // --- Update UI based on System State ---

            // Overall Status
            valStatus.textContent = data.status;
            resetCardState(cardStatus);
            if (data.status === "FIRE EMERGENCY") {
                cardStatus.classList.add('state-danger', 'emergency-mode');
            } else if (data.status === "CROWD ALERT") {
                cardStatus.classList.add('state-warning');
            } else {
                cardStatus.classList.add('state-safe');
            }

            // Crowd Level
            valCrowd.textContent = data.crowd_level;
            valCount.textContent = data.people_count;
            resetCardState(cardCrowd);
            if (data.crowd_level === "High") {
                cardCrowd.classList.add('state-warning');
            } else if (data.crowd_level === "Medium") {
                cardCrowd.classList.add('state-warning'); // Could be custom yellow style
            } else {
                cardCrowd.classList.add('state-safe');
            }

            // Fire Detection
            resetCardState(cardFire);
            if (data.fire_detected) {
                valFire.textContent = "DETECTED";
                cardFire.classList.add('state-danger', 'emergency-mode');
            } else {
                valFire.textContent = "Secure";
                cardFire.classList.add('state-safe');
            }

        } catch (err) {
            console.error("Failed to fetch status:", err);
            sysDot.className = 'status-dot offline';
            sysText.textContent = 'Dashboard Disconnected';
        }
    }

    // Polling Event Logs
    async function fetchEventLogs() {
        try {
            const res = await fetch('/api/events');
            const newEvents = await res.json();
            
            // If new events array differs from previous by length or ids, re-render
            // For simplicity, we just check if top item ID is different
            if (newEvents.length > 0 && 
                (lastKnownEvents.length === 0 || newEvents[0].id !== lastKnownEvents[0].id)) {
                
                logContainer.innerHTML = ""; // clear
                newEvents.forEach(ev => {
                    const el = document.createElement('div');
                    el.className = `log-item ${ev.type}`;
                    el.innerHTML = `
                        <span class="log-time">${ev.time}</span>
                        <p>${ev.message}</p>
                    `;
                    logContainer.appendChild(el);
                });
                
                lastKnownEvents = newEvents;
            }
        } catch (err) {
            console.error("Failed to fetch events:", err);
        }
    }

    // Start Polling Loops
    setInterval(fetchSystemStatus, 1000);
    setInterval(fetchEventLogs, 2000);

    // Initial Fetch
    fetchSystemStatus();
    fetchEventLogs();
});
