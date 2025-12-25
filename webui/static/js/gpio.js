document.addEventListener('DOMContentLoaded', () => {
    const servosConfigContainer = document.getElementById('servos-config');
    const gpiosConfigContainer = document.getElementById('gpios-config');
    const inputsConfigContainer = document.getElementById('inputs-config');
    const form = document.getElementById('gpio-form');

    const scheduleConfigContainer = document.getElementById('schedule-config');

    Promise.all([
        fetch('/gpio_config').then(r => r.json()),
        fetch('/config/schedule').then(r => r.json())
    ]).then(([gpioConfig, scheduleConfig]) => {
        populateServos(gpioConfig.servos);
        populateGpios(gpioConfig.gpios);
        populateInputs(gpioConfig.inputs);

        if (gpioConfig.timeout !== undefined) {
            document.getElementById('freigabe-timeout').value = gpioConfig.timeout;
        }
        if (gpioConfig.presence_trigger_time !== undefined) {
            document.getElementById('presence-trigger-time').value = gpioConfig.presence_trigger_time;
        }
        if (gpioConfig.presence_notice_time !== undefined) {
            document.getElementById('presence-notice-time').value = gpioConfig.presence_notice_time;
        }
        if (gpioConfig.min_detection_confidence !== undefined) {
            document.getElementById('min-detection-confidence').value = gpioConfig.min_detection_confidence;
        }

        populateSchedule(scheduleConfig);
    });

    function createRemoveButton() {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'remove-btn';
        button.innerHTML = '&times;';
        button.addEventListener('click', () => button.parentElement.parentElement.remove());
        return button;
    }

    function populateServos(servos) {
        servosConfigContainer.innerHTML = '';
        if (!servos) return;
        for (const pin in servos) {
            const servo = servos[pin];
            const item = document.createElement('div');
            item.className = 'pin-config-item servo-item';
            item.innerHTML = `
                <div class="pin-header">
                    <h4>Servo on Pin <input type="number" class="pin-number" value="${pin}" required></h4>
                </div>
                <label>Name: <input type="text" name="name" value="${servo.name}" required></label>
                <label>Min Angle: <input type="number" name="min" value="${servo.min}" required></label>
                <label>Max Angle: <input type="number" name="max" value="${servo.max}" required></label>
                <label>Speed: <input type="number" name="speed" value="${servo.speed}" required></label>
                <label>Reversed: <input type="checkbox" name="reversed" ${servo.reversed ? 'checked' : ''}></label>
            `;
            const header = item.querySelector('.pin-header');
            header.appendChild(createRemoveButton());
            servosConfigContainer.appendChild(item);
        }
    }

    function populateGpios(gpios) {
        gpiosConfigContainer.innerHTML = '';
        if (!gpios) return;
        for (const pin in gpios) {
            const gpio = gpios[pin];
            const item = document.createElement('div');
            item.className = 'pin-config-item gpio-item';
            item.innerHTML = `
                <div class="pin-header">
                    <h4>GPIO on Pin <input type="number" class="pin-number" value="${pin}" required></h4>
                </div>
                <label>Name: <input type="text" name="name" value="${gpio.name}" required></label>
            `;
            item.querySelector('.pin-header').appendChild(createRemoveButton());
            gpiosConfigContainer.appendChild(item);
        }
    }

    function populateInputs(inputs) {
        inputsConfigContainer.innerHTML = '';
        if (!inputs) return;
        for (const name in inputs) {
            const pin = inputs[name];
            const item = document.createElement('div');
            item.className = 'input-item';
            const labelName = name.charAt(0).toUpperCase() + name.slice(1);
            item.innerHTML = `
                <span>${labelName} Pin:</span>
                <input type="number" name="${name}" value="${pin}" required>
            `;
            inputsConfigContainer.appendChild(item);
        }
    }

    function populateSchedule(schedule) {
        scheduleConfigContainer.innerHTML = '';
        const days = [
            { key: 'Mon', label: 'Mo' },
            { key: 'Tue', label: 'Di' },
            { key: 'Wed', label: 'Mi' },
            { key: 'Thu', label: 'Do' },
            { key: 'Fri', label: 'Fr' },
            { key: 'Sat', label: 'Sa' },
            { key: 'Sun', label: 'So' }
        ];

        days.forEach(day => {
            const dayRanges = schedule[day.key] || [];
            const dayDiv = document.createElement('div');
            dayDiv.className = 'pin-config-item schedule-item';
            dayDiv.dataset.day = day.key;

            let rangesHtml = '';
            dayRanges.forEach((range, index) => {
                rangesHtml += `
                    <div class="time-range" style="display: flex; gap: 10px; margin-bottom: 5px; align-items: center;">
                        <input type="time" name="start" value="${range.start}" required>
                        <span>-</span>
                        <input type="time" name="end" value="${range.end}" required>
                        <button type="button" class="remove-btn range-remove-btn" style="padding: 2px 6px;">&times;</button>
                    </div>
                `;
            });

            dayDiv.innerHTML = `
                <div class="pin-header">
                    <h4>${day.label}</h4>
                    <button type="button" class="add-btn add-range-btn" style="padding: 2px 8px; font-size: 0.8em;">+ Add Time</button>
                </div>
                <div class="ranges-container">
                    ${rangesHtml}
                </div>
            `;

            // Add event listeners for this day block
            dayDiv.querySelector('.add-range-btn').addEventListener('click', () => {
                const container = dayDiv.querySelector('.ranges-container');
                const rangeDiv = document.createElement('div');
                rangeDiv.className = 'time-range';
                rangeDiv.style.cssText = "display: flex; gap: 10px; margin-bottom: 5px; align-items: center;";
                rangeDiv.innerHTML = `
                    <input type="time" name="start" value="09:00" required>
                    <span>-</span>
                    <input type="time" name="end" value="17:00" required>
                    <button type="button" class="remove-btn range-remove-btn" style="padding: 2px 6px;">&times;</button>
                `;
                rangeDiv.querySelector('.range-remove-btn').addEventListener('click', () => rangeDiv.remove());
                container.appendChild(rangeDiv);
            });

            dayDiv.querySelectorAll('.range-remove-btn').forEach(btn => {
                btn.addEventListener('click', (e) => e.target.closest('.time-range').remove());
            });

            scheduleConfigContainer.appendChild(dayDiv);
        });
    }

    document.getElementById('add-servo').addEventListener('click', () => {
        const item = document.createElement('div');
        item.className = 'pin-config-item servo-item';
        item.innerHTML = `
            <div class="pin-header">
                <h4>Servo on Pin <input type="number" class="pin-number" value="" placeholder="New Pin" required></h4>
            </div>
            <label>Name: <input type="text" name="name" value="NewServo" required></label>
            <label>Min Angle: <input type="number" name="min" value="0" required></label>
            <label>Max Angle: <input type="number" name="max" value="180" required></label>
            <label>Speed: <input type="number" name="speed" value="150" required></label>
            <label>Reversed: <input type="checkbox" name="reversed"></label>
        `;
        item.querySelector('.pin-header').appendChild(createRemoveButton());
        servosConfigContainer.appendChild(item);
    });

    document.getElementById('add-gpio').addEventListener('click', () => {
        const item = document.createElement('div');
        item.className = 'pin-config-item gpio-item';
        item.innerHTML = `
            <div class="pin-header">
                <h4>GPIO on Pin <input type="number" class="pin-number" value="" placeholder="New Pin" required></h4>
            </div>
            <label>Name: <input type="text" name="name" value="NewGPIO" required></label>
        `;
        item.querySelector('.pin-header').appendChild(createRemoveButton());
        gpiosConfigContainer.appendChild(item);
    });

    function saveConfig(andRestart = false) {
        const newConfig = {
            servos: {},
            gpios: {},
            inputs: {},
            timeout: parseInt(document.getElementById('freigabe-timeout').value) || 60,
            presence_trigger_time: parseInt(document.getElementById('presence-trigger-time').value) || 15,
            presence_notice_time: parseInt(document.getElementById('presence-notice-time').value) || 3,
            min_detection_confidence: parseFloat(document.getElementById('min-detection-confidence').value) || 0.8
        };

        document.querySelectorAll('.servo-item').forEach(item => {
            const pin = item.querySelector('.pin-number').value;
            if (!pin) return;
            newConfig.servos[pin] = {
                name: item.querySelector('[name="name"]').value,
                min: parseInt(item.querySelector('[name="min"]').value),
                max: parseInt(item.querySelector('[name="max"]').value),
                speed: parseInt(item.querySelector('[name="speed"]').value),
                reversed: item.querySelector('[name="reversed"]').checked,
            };
        });

        document.querySelectorAll('.gpio-item').forEach(item => {
            const pin = item.querySelector('.pin-number').value;
            if (!pin) return;
            newConfig.gpios[pin] = {
                name: item.querySelector('[name="name"]').value,
            };
        });

        document.querySelectorAll('#inputs-config .input-item input').forEach(input => {
            newConfig.inputs[input.name] = parseInt(input.value);
        });

        // Collect Schedule
        const newSchedule = {};
        document.querySelectorAll('.schedule-item').forEach(item => {
            const dayKey = item.dataset.day;
            const ranges = [];
            item.querySelectorAll('.time-range').forEach(range => {
                const start = range.querySelector('[name="start"]').value;
                const end = range.querySelector('[name="end"]').value;
                if (start && end) {
                    ranges.push({ start, end });
                }
            });
            newSchedule[dayKey] = ranges;
        });

        Promise.all([
            fetch('/gpio_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            }),
            fetch('/config/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newSchedule)
            })
        ])
            .then(([gpioResponse, scheduleResponse]) => {
                if (!gpioResponse.ok || !scheduleResponse.ok) {
                    throw new Error('Failed to save configuration.');
                }
                return Promise.all([gpioResponse.json(), scheduleResponse.json()]);
            })
            .then(([gpioData, scheduleData]) => {
                alert('Configuration and Schedule saved.');
                if (andRestart) {
                    alert('System is restarting now. Please wait a moment before reconnecting.');
                    fetch('/restart', { method: 'POST' });
                }
            })
            .catch(error => alert('Error: ' + error.message));

        /*
        fetch('/gpio_config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to save configuration.');
                }
                return response.json();
            })
            .then(data => {
                alert(data.message || 'Configuration saved.');
                if (andRestart) {
                    alert('System is restarting now. Please wait a moment before reconnecting.');
                    fetch('/restart', { method: 'POST' });
                }
            })
        */
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        saveConfig(false);
    });

    document.getElementById('restart-button').addEventListener('click', () => {
        if (confirm('Are you sure you want to save and restart? The system will be temporarily unavailable.')) {
            saveConfig(true);
        }
    });
});