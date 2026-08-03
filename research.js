(function () {
    "use strict";

    const summaryElements = {
        microbiome: "microbiome-summary",
        probiotics: "probiotics-summary",
        slow_aging: "slow-aging-summary",
        beauty: "beauty-summary"
    };

    function isNonEmptyString(value) {
        return typeof value === "string" && value.trim().length > 0;
    }

    function validateTrends(data) {
        if (!data
            || typeof data !== "object"
            || !Number.isInteger(data.schema_version)
            || !isNonEmptyString(data.generated_at)
            || !data.period
            || typeof data.period !== "object"
            || !isNonEmptyString(data.period.start)
            || !isNonEmptyString(data.period.end)
            || !isNonEmptyString(data.overview)) {
            return false;
        }

        if (!data.areas || typeof data.areas !== "object") {
            return false;
        }

        return Object.keys(summaryElements).every(function (area) {
            return data.areas[area]
                && typeof data.areas[area] === "object"
                && isNonEmptyString(data.areas[area].summary);
        });
    }

    fetch("./research_data/research_trends.json")
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Research trends request failed");
            }
            return response.json();
        })
        .then(function (data) {
            if (!validateTrends(data)) {
                throw new Error("Research trends data is invalid");
            }

            document.getElementById("research-overview").textContent = data.overview;
            Object.keys(summaryElements).forEach(function (area) {
                document.getElementById(summaryElements[area]).textContent = data.areas[area].summary;
            });
        })
        .catch(function () {
            document.getElementById("research-data-error").hidden = false;
        });
}());
