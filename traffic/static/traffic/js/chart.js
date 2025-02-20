document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("trafficChart").getContext("2d");
    let trafficChart;
    const periodSelect = document.getElementById("timePeriod");
    const dateInput = document.getElementById("dateInput");
    const showStatsBtn = document.getElementById("showStatsBtn");
    const errorDiv = document.getElementById("errorMessage");

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = "block";
    }

    function hideError() {
        errorDiv.style.display = "none";
    }

    function getApiPathFromPeriod(period) {
        switch (period) {
            case "day": return "daily";
            case "week": return "weekly";
            case "month": return "monthly";
            case "year": return "yearly";
            default: return "daily";
        }
    }

    function formatDate(period) {
        const today = new Date();
        switch (period) {
            case "day": return today.toISOString().split("T")[0];
            case "week": {
                const weekNumber = getISOWeek(today).week;
                return `${today.getFullYear()}-${String(weekNumber).padStart(2, '0')}`;
            }
            case "month": return today.toISOString().slice(0, 7);
            case "year": return today.getFullYear().toString();
            default: return "";
        }
    }

    function getISOWeek(date = new Date()) {
        const tempDate = new Date(date);
        tempDate.setHours(0, 0, 0, 0);

        tempDate.setDate(tempDate.getDate() + 3 - ((tempDate.getDay() + 6) % 7));

        const firstThursday = new Date(tempDate.getFullYear(), 0, 4);
        firstThursday.setDate(firstThursday.getDate() + 3 - ((firstThursday.getDay() + 6) % 7));
        const weekNumber = Math.round((tempDate - firstThursday) / (7 * 24 * 60 * 60 * 1000)) + 1;

        return { year: tempDate.getFullYear(), week: weekNumber };
    }

    function getFirstDayOfISOWeek(year, week) {
        const simpleDate = new Date(year, 0, 1);
        const days = (week - 1) * 7;
        simpleDate.setDate(simpleDate.getDate() + days);

        const day = simpleDate.getDay();
        const offset = (day <= 1 ? day + 6 : day - 1);
        simpleDate.setDate(simpleDate.getDate() - offset);

        return simpleDate;
    }

    function validateDateInput(period, inputValue) {
        const today = new Date();

        if (period === "week") {
            const match = inputValue.match(/^(\d{4})-(\d{1,2})$/);
            if (!match) {
                showError("Неверный формат недели. Используйте " + getDatePlaceholder(period));
                return false;
            }

            const inputYear = parseInt(match[1], 10);
            const inputWeek = parseInt(match[2], 10);

            const firstDayOfWeek = getFirstDayOfISOWeek(inputYear, inputWeek);

            if (firstDayOfWeek > today) {
                showError("Выбранная неделя не может быть в будущем.");
                return false;
            }
        } else {
            const inputDate = new Date(inputValue);
            if (isNaN(inputDate.getTime())) {
                showError("Неверный формат даты. Используйте " + getDatePlaceholder(period));
                return false;
            }

            if (inputDate > today) {
                showError("Выбранная дата не может быть в будущем.");
                return false;
            }
        }

        hideError();
        return true;
}

    function getDatePlaceholder(period) {
        switch (period){
            case "day": return "YYYY-MM-DD";
            case "week": return "YYYY-WW";
            case "month": return "YYYY-MM";
            case "year": return "YYYY";
            default: return "неизвестный формат";
        }
    }

    function fetchData(period, selectedDate = null) {
        if (selectedDate && !validateDateInput(period, selectedDate)) {
            return;
        }

        const url = getApiUrl(period, selectedDate);
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showError(data.error);
                    return;
                }
                hideError();
                updateChart(data, period);
            })
            .catch(error => {
                showError("Ошибка запроса: " + error.message);
            });
    }

    function updateDateInput(period) {
        const placeholderText = getDatePlaceholder(period);
        dateInput.setAttribute("placeholder", placeholderText);

        dateInput.value = formatDate(period);
    }

    function getApiUrl(period, selectedDate = "") {
        const baseUrl = "/api/traffic/";
        const apiPeriod = getApiPathFromPeriod(period);
        let url = baseUrl + apiPeriod;

        if (selectedDate) {
            let paramKey = "";
            switch (apiPeriod) {
                case "daily":
                    paramKey = "date";
                    break;
                case "weekly":
                    paramKey = "week";
                    break;
                case "monthly":
                    paramKey = "month";
                    break;
                case "yearly":
                    paramKey = "year";
                    break;
            }
            url += `/?${paramKey}=${selectedDate}`;
        }

        return url;
    }

    function generateLabels(period, data){
        let labels = [];

        if (period === "day") {
            labels = Array.from({length: 24}, (_, i) => i);
        } else if (period === "week") {
            labels = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"];
        } else if (period === "month") {
            let date = new Date();
            let year = date.getFullYear();
            let month = date.getMonth();

            let daysInMonth = new Date(year, month + 1, 0).getDate();

            let locale = 'ru-RU';
            labels = Array.from({ length: daysInMonth }, (_, i) =>
                new Date(year, month, i + 1).toLocaleDateString(locale, { day: 'numeric', month: 'long' })
            );
        } else if (period === "year") {
            return Array.from({ length: 12 }, (_, i) => i + 1);
        }
        return labels;
    }

    function getMonthName(monthNum) {
    const months = [
        "январь", "февраль", "март", "апрель", "май", "июнь",
        "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
    ];
    return months[monthNum - 1];
}

    function updateChart(data, period){
        if (data.error) {
            showError(data.error);
            return;
        }

        let labels = [];
        let totalRequests = [];
        let uniqueUsers = [];
        let uniqueGuests = [];
        let uniqueRegisteredUsers = [];

        let allLabels = generateLabels(period);

        allLabels.forEach(label => {
            let found = data.find(stat => {
            if (period === "day") {
                return stat.hour === label;
            } else if (period === "week") {
                return stat.day_of_week === label;
            } else if (period === "month") {
                return stat.day === label;
            } else if (period === "year") {
                return stat.month === label;
            }
        });

            if (found) {
                totalRequests.push(found.count);
                uniqueRegisteredUsers.push(found.unique_registered_users);
                uniqueGuests.push(found.unique_guests);
                uniqueUsers.push(found.unique_registered_users + found.unique_guests);
            } else {
                totalRequests.push(0);
                uniqueRegisteredUsers.push(0);
                uniqueGuests.push(0);
                uniqueUsers.push(0);
            }

            if (period === "year") {
                labels.push(getMonthName(label));
            } else {
                labels.push(label);
            }
        });

        if (trafficChart) {
            trafficChart.destroy();
        }

        trafficChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Всего запросов",
                        borderColor: "rgba(75, 192, 192, 1)",
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                        data: totalRequests,
                        fill: true
                    },
                    {
                        label: "Уникальные пользователи",
                        borderColor: "rgba(255, 99, 132, 1)",
                        backgroundColor: "rgba(255, 99, 132, 0.2)",
                        data: uniqueUsers,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: getXAxisTitle(period)
                        }
                    },
                    y: {title: {display: true, text: "Количество"}}
                },
                plugins: {
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            let datasetLabel = tooltipItem.dataset.label || '';
                            let idx = tooltipItem.dataIndex;

                            if (datasetLabel === "Всего запросов"){
                                return `${datasetLabel}: ${totalRequests[idx]}`;
                            } else if (datasetLabel === "Уникальные пользователи") {
                                let totalUniqueUsers = uniqueUsers[idx];
                                let uniqueRegistered = uniqueRegisteredUsers[idx];
                                let uniqueGuest = uniqueGuests[idx];

                                return `Уникальные пользователи: ${totalUniqueUsers} (зарегистрированные: ${uniqueRegistered}, гости: ${uniqueGuest})`;
                            }
                        }
                    }
                }
            }
            }
        });
    }

    function getXAxisTitle(period) {
        switch (period) {
            case "daily":
                return "Часы";
            case "weekly":
                return "Дни недели";
            case "monthly":
                return "Дни";
            case "yearly":
                return "Месяцы";
            default:
                return "Временной интервал";
        }
    }

    const defaultPeriod = "day";
    periodSelect.value = defaultPeriod;
    updateDateInput(defaultPeriod);
    fetchData(defaultPeriod, formatDate(defaultPeriod));

    periodSelect.addEventListener("change", function () {
        updateDateInput(this.value);
        fetchData(this.value, formatDate(this.value));
    });

    showStatsBtn.addEventListener("click", function () {
        fetchData(periodSelect.value, dateInput.value);
    });
});