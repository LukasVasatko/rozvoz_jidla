let alertCount = 0;

function addAlert(name, message) {
    alertCount++;
    const alertContainer = document.getElementById('alertContainer');
    const newAlert = document.createElement('div');
    newAlert.classList.add('alert-box');
    newAlert.id = 'alertBox' + alertCount;

    newAlert.innerHTML = `
    <div class="alert-strip"></div>
        <div class="alert-body">
            <div class="alert-header">
                <span class="alert-title">${name}</span>
                <span class="alert-close" onclick="hideAlert('alertBox${alertCount}')">&times;</span>
            </div>
            <p class="alert-message">${message}</p>
        </div>`;

    alertContainer.appendChild(newAlert);

    setTimeout(() => {
        newAlert.classList.add('show');
    }, 100);

    setTimeout((function(alertId) {
        return function() {
            hideAlert(alertId);
        };
    })(newAlert.id), 5000);
}

function hideAlert(id) {
    const alertBox = document.getElementById(id);
    if (alertBox) {
        alertBox.classList.remove('show');
        setTimeout(() => {
            alertBox.remove();
        }, 400);
    }
}
