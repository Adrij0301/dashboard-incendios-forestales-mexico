(function () {
    const GRAPH_IDS = [
        "main_map",
        "graph_barras",
        "graph_pastel",
        "graph_linea",
        "graph_scatter",
        "hover_graph_1",
        "hover_graph_2"
    ];

    function resizePlot(id) {
        const host = document.getElementById(id);
        if (!host || !window.Plotly) return;
        const plot = host.querySelector(".js-plotly-plot");
        if (!plot || !plot.data) return;
        try {
            window.Plotly.Plots.resize(plot);
        } catch (error) {
            console.debug("No se pudo redimensionar", id, error);
        }
    }

    function resizeAll() {
        GRAPH_IDS.forEach(resizePlot);
    }

    function scheduleResize() {
        window.requestAnimationFrame(resizeAll);
        window.setTimeout(resizeAll, 120);
        window.setTimeout(resizeAll, 450);
    }

    window.addEventListener("load", scheduleResize);
    window.addEventListener("resize", scheduleResize);

    const observer = new MutationObserver(function () {
        scheduleResize();
    });

    function startObserver() {
        const root = document.getElementById("_dash-app-content") || document.body;
        observer.observe(root, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ["data-theme"]
        });
        scheduleResize();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", startObserver, { once: true });
    } else {
        startObserver();
    }
})();
