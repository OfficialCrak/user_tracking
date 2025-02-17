document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("trafficChart").getContext("2d");
    let trafficChart;
    const periodSelect = document.getElementById("timePeriod");
    const dateInput = document.getElementById("dateInput");
    const showStatsBtn = document.getElementById("showStatsBtn");

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
            case "daily": return today.toISOString().split("T")[0];
            case "weekly": return `${today.getFullYear()}-W${String(Math.ceil(today.getDate() / 7)).padStart(2, '0')}`;
            case "monthly": return today.toISOString().slice(0, 7);
            case "yearly": return today.getFullYear().toString();
            default: return "";
        }
    }

    function getDatePlaceholder(period) {
        switch (period){
            case "daily": return "YYYY-MM-DD";
            case "weekly": return "YYYY-WW";
            case "monthly": return "YYYY-MM";
            case "yearly": return "YYYY";
            default: return "";
        }
    }

    function fetchData(period, selectedDate = null) {
        const url = getApiUrl(period, selectedDate);
        fetch(url)
            .then(response => response.json())
            .then(data => updateChart(data, period))
            .catch(error => console.error("Ошибка загрузки данных: ", error));
    }

    function updateDateInput(period) {
        const placeholderText = getDatePlaceholder(period);
        if (!dateInput.value) {
            dateInput.setAttribute("placeholder", placeholderText);
        }
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

    function updateChart(data, period){
        if (data.error) {
            console.error(data.error);
            return;
        }

        let labels = [];
        let totalRequests = [];
        let uniqueUsers = [];

        data.forEach(stat => {
            labels.push(stat.hour || stat.day || stat.month);
            totalRequests.push(stat.count);
            uniqueUsers.push(stat.unique_users);
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
                    x: {title: {display: true, text: getXAxisTitle(period)}},
                    y: {title: {display: true, text: "Количество"}}
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
                return "Время";
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