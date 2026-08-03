(function () {
    "use strict";

    const allowedAreas = new Set(["microbiome", "probiotics", "slow_aging", "beauty"]);
    const area = new URLSearchParams(window.location.search).get("area");
    const titleElement = document.getElementById("area-title");
    const listElement = document.getElementById("article-list");

    function showMessage(message, isError) {
        listElement.replaceChildren();
        const card = document.createElement("div");
        card.className = "card";
        const text = document.createElement("p");
        text.className = isError ? "message error" : "message";
        text.textContent = message;
        card.appendChild(text);
        listElement.appendChild(card);
    }

    function addText(parent, className, text) {
        if (typeof text !== "string" || !text.trim()) {
            return;
        }
        const element = document.createElement("p");
        element.className = className;
        element.textContent = text;
        parent.appendChild(element);
    }

    function getSafeExternalUrl(value) {
        if (typeof value !== "string" || !value.trim()) {
            return null;
        }
        try {
            const url = new URL(value);
            return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
        } catch (error) {
            return null;
        }
    }

    function renderArticle(article) {
        const card = document.createElement("article");
        card.className = "card";

        const title = document.createElement("h2");
        title.className = "article-title";
        title.textContent = typeof article.title === "string" ? article.title : "제목 없음";
        card.appendChild(title);

        if (Array.isArray(article.authors) && article.authors.length) {
            const authors = article.authors.filter(function (author) {
                return typeof author === "string";
            }).join(", ");
            addText(card, "article-meta", "저자: " + authors);
        }
        addText(card, "article-meta", article.journal ? "저널: " + article.journal : "");
        addText(card, "article-meta", article.published_date ? "발행일: " + article.published_date : "");
        addText(card, "article-meta", article.article_type ? "논문 유형: " + article.article_type : "");
        addText(card, "article-description", article.one_line_description);

        const externalUrl = getSafeExternalUrl(article.url);
        if (externalUrl) {
            const link = document.createElement("a");
            link.className = "paper-link";
            link.href = externalUrl;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = "원문 보기";
            card.appendChild(link);
        }

        return card;
    }

    if (!area || !allowedAreas.has(area)) {
        titleElement.textContent = "대표 논문";
        showMessage("올바른 연구 분야를 선택해 주세요.", true);
        return;
    }

    fetch("./research_data/research_articles.json")
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Research articles request failed");
            }
            return response.json();
        })
        .then(function (data) {
            if (!data || typeof data !== "object" || !data.areas || typeof data.areas !== "object") {
                throw new Error("Research articles data is invalid");
            }

            const areaData = data.areas[area];
            if (!areaData || typeof areaData.label !== "string" || !Array.isArray(areaData.articles)) {
                throw new Error("Selected research area is invalid");
            }

            titleElement.textContent = areaData.label + " 대표 논문";
            document.title = areaData.label + " Research Articles";
            listElement.replaceChildren();

            if (areaData.articles.length === 0) {
                showMessage("현재 이 분야에 소개할 논문이 없습니다.", false);
                return;
            }

            areaData.articles.forEach(function (article) {
                if (article && typeof article === "object") {
                    listElement.appendChild(renderArticle(article));
                }
            });
        })
        .catch(function () {
            showMessage("논문 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.", true);
        });
}());
