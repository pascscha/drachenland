document.addEventListener('DOMContentLoaded', () => {
    const servosConfigContainer = document.getElementById('servos-config');
    const gpiosConfigContainer = document.getElementById('gpios-config');
    const inputsConfigContainer = document.getElementById('inputs-config');
    const form = document.getElementById('gpio-form');

    fetch('/gpio_config')
        .then(response => response.json())
        .then(config => {
            populateServos(config.servos);
            populateGpios(config.gpios);
            populateInputs(config.inputs);
            if (config.timeout !== undefined) {
                document.getElementById('freigabe-timeout').value = config.timeout;
            }
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
            timeout: parseInt(document.getElementById('freigabe-timeout').value) || 60
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
            .catch(error => alert('Error: ' + error.message));
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