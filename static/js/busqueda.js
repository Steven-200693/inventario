document.addEventListener("DOMContentLoaded", () => {
    const buscador = document.getElementById("buscador");
    const enlaceExportacion = document.querySelector("[data-export-link]");
    const items = document.querySelectorAll("[data-search-item]");
    const mensajesSinResultados = document.querySelectorAll("[data-no-results]");

    if (!buscador) {
        return;
    }

    const normalizar = (texto) => texto
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase();

    const actualizarEnlaceExportacion = () => {
        if (!enlaceExportacion) {
            return;
        }

        const url = new URL(enlaceExportacion.dataset.exportUrl, window.location.origin);
        const valor = buscador.value.trim();
        if (valor) {
            url.searchParams.set("q", valor);
        }
        enlaceExportacion.href = `${url.pathname}${url.search}`;
    };

    const filtrar = () => {
        const valor = normalizar(buscador.value.trim());
        let principalesVisibles = 0;

        items.forEach((item) => {
            const detalles = item.dataset.detailsId
                ? document.getElementById(item.dataset.detailsId)
                : null;
            const texto = normalizar(
                item.textContent + (detalles ? detalles.textContent : ""),
            );
            const coincide = texto.includes(valor);

            item.hidden = !coincide;
            if (detalles) {
                const boton = document.querySelector(
                    `[data-details-toggle="${item.dataset.detailsId}"]`,
                );
                detalles.hidden = !coincide
                    || !boton
                    || boton.getAttribute("aria-expanded") !== "true";
            }
            if (coincide && item.hasAttribute("data-search-primary")) {
                principalesVisibles += 1;
            }
        });

        mensajesSinResultados.forEach((mensaje) => {
            mensaje.classList.toggle("hidden", principalesVisibles > 0);
        });
        actualizarEnlaceExportacion();
    };

    buscador.addEventListener("input", filtrar);

    document.querySelectorAll("[data-details-toggle]").forEach((boton) => {
        boton.addEventListener("click", () => {
            const detalles = document.getElementById(boton.dataset.detailsToggle);
            const abierto = boton.getAttribute("aria-expanded") === "true";
            boton.setAttribute("aria-expanded", String(!abierto));
            boton.textContent = abierto ? "Ver detalles" : "Ocultar detalles";
            detalles.hidden = abierto;
        });
    });

    filtrar();
});
