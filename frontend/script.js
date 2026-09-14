const form = document.getElementById("shortenForm");
const result = document.getElementById("result");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const longUrl = document.getElementById("longUrl").value;
    const customCode = document.getElementById("customCode").value;
    const expiresDate = document.getElementById("expiresDate").value;
    const expiresTime = document.getElementById("expiresTime").value;

    let expiresAt = null;

    if (expiresDate && expiresTime) {
        expiresAt = `${expiresDate}T${expiresTime}:00`;
    }

    const data = {
        long_url: longUrl,
        custom_code: customCode || null,
        expires_at: expiresAt
    };

    try {
        const response = await fetch(
            "shorten",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(data)
            }
        );

        const resultData = await response.json();

        if (!response.ok) {
            result.textContent =
                resultData.detail || "Something went wrong.";
            return;
        }

        // Display result
        result.innerHTML = `
            <p><strong>Your short URL:</strong></p>

            <div class="short-url-container">
                <a
                    href="${resultData.short_url}"
                    target="_blank"
                    id="shortUrl"
                >
                    ${resultData.short_url}
                </a>

                <button type="button" id="copyButton">
                    Copy
                </button>
            </div>

            <button
                type="button"
                id="statsButton"
                class="stats-button"
            >
                View Stats
            </button>

            <div id="statsResult"></div>
        `;

        // Copy button
        const copyButton =
            document.getElementById("copyButton");

        copyButton.addEventListener("click", async function () {
            await navigator.clipboard.writeText(
                resultData.short_url
            );

            copyButton.textContent = "Copied!";

            setTimeout(() => {
                copyButton.textContent = "Copy";
            }, 2000);
        });


        // Stats button
        const statsButton =
            document.getElementById("statsButton");

        const statsResult =
            document.getElementById("statsResult");

        statsButton.addEventListener("click", async function () {

            statsButton.textContent = "Loading...";

            try {
                const response = await fetch(
                    `stats/${resultData.short_code}`
                );

                const statsData = await response.json();

                if (!response.ok) {
                    statsResult.textContent =
                        statsData.detail ||
                        "Unable to fetch stats.";

                    return;
                }

                statsResult.innerHTML = `
                    <p>
                        <strong>Clicks:</strong>
                        ${statsData.click_count}
                    </p>

                    <p>
                        <strong>Created:</strong>
                        ${statsData.created_at}
                    </p>

                    <p>
                        <strong>Expires:</strong>
                        ${
                            statsData.expires_at ||
                            "Never"
                        }
                    </p>
                `;

            } catch (error) {

                statsResult.textContent =
                    "Unable to fetch statistics.";

                console.error(error);

            } finally {

                statsButton.textContent = "View Stats";

            }
        });

    } catch (error) {

        result.textContent =
            "Unable to connect to the server.";

        console.error(error);
    }
});