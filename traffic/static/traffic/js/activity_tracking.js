(function() {
    const idleTimeout = 30 * 60 * 1000
    const activityInterval = 30 * 1000;
    let lastActivityTime = Date.now();

    function sendActivityData() {
        const data = {
            last_activity_time: new Date().toISOString(),
        };

        fetch('api/traffic/track-activity/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(data),
            credentials: 'same-origin'
        })
            .then(response => response.json())
            .catch(error => console.error('Ошибка при отправке данных активности: ', error));
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== ''){
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++){
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue
    }

    function checkInactivity() {
        if (Date.now() - lastActivityTime > idleTimeout) {
            console.log("Пользователь неактивен более 30 минут.");
        } else {
            sendActivityData();
        }
    }

    document.addEventListener('mousemove', () => lastActivityTime = Date.now());
    document.addEventListener('keydown', () => lastActivityTime = Date.now());

    setInterval(checkInactivity, activityInterval);
})();