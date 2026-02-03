const API_BASE = "http://localhost:8000";
let priceChart = null;

const elements = {
  websiteFilter: document.getElementById("websiteFilter"),
  searchInput: document.getElementById("searchInput"),
  sortFilter: document.getElementById("sortFilter"),
  productsTable: document.getElementById("productsTable"),
  runScrapeBtn: document.getElementById("runScrapeBtn"),
  totalProducts: document.getElementById("totalProducts"),
  lastRun: document.getElementById("lastRun"),
  discountOver20: document.getElementById("discountOver20"),
  activeWebsites: document.getElementById("activeWebsites"),
  logsList: document.getElementById("logsList"),
};

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Error en API: ${response.status}`);
  }
  return response.json();
}

async function loadWebsites() {
  const websites = await fetchJSON(`${API_BASE}/api/websites`);
  websites.forEach((site) => {
    const option = document.createElement("option");
    option.value = site.id;
    option.textContent = site.name;
    elements.websiteFilter.appendChild(option);
  });
  return websites;
}

async function loadStats() {
  const stats = await fetchJSON(`${API_BASE}/api/stats`);
  elements.totalProducts.textContent = stats.total_products;
  elements.lastRun.textContent = stats.last_run ? new Date(stats.last_run).toLocaleString() : "-";
  elements.discountOver20.textContent = stats.discount_over_20;
  elements.activeWebsites.textContent = stats.active_websites;
}

async function loadProducts() {
  const params = new URLSearchParams();
  if (elements.websiteFilter.value) params.append("website_id", elements.websiteFilter.value);
  if (elements.searchInput.value) params.append("search", elements.searchInput.value);
  if (elements.sortFilter.value) params.append("sort_by", elements.sortFilter.value);

  const products = await fetchJSON(`${API_BASE}/api/products?${params.toString()}`);
  elements.productsTable.innerHTML = "";

  products.forEach((product) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${product.name}</td>
      <td>${product.website_id}</td>
      <td>$${product.current_price.toLocaleString()}</td>
      <td>${product.original_price ? `$${product.original_price.toLocaleString()}` : "-"}</td>
      <td>${product.discount ? `${product.discount}%` : "-"}</td>
      <td>${new Date(product.last_scraped).toLocaleString()}</td>
    `;
    row.addEventListener("click", () => loadChart(product.id, product.name));
    elements.productsTable.appendChild(row);
  });
}

async function loadChart(productId, name) {
  try {
    const history = await fetchJSON(`${API_BASE}/api/products/${productId}/history`);
    const labels = history.map((item) => new Date(item.scraped_at).toLocaleString());
    const data = history.map((item) => item.price);

    const ctx = document.getElementById("priceChart").getContext("2d");
    if (priceChart) {
      priceChart.destroy();
    }
    priceChart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: `Histórico de ${name}`,
            data,
            borderColor: "#2563eb",
            backgroundColor: "rgba(37, 99, 235, 0.2)",
            tension: 0.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  } catch (error) {
    console.error("Error cargando histórico", error);
  }
}

async function loadLogs() {
  const logs = await fetchJSON(`${API_BASE}/api/scraping-logs`);
  elements.logsList.innerHTML = "";
  logs.forEach((log) => {
    const item = document.createElement("li");
    const status = log.status === "success" ? "✅" : "⚠️";
    item.textContent = `${status} Sitio ${log.website_id} - ${log.status} - Productos: ${log.products_found}`;
    elements.logsList.appendChild(item);
  });
}

async function runManualScrape() {
  elements.runScrapeBtn.disabled = true;
  try {
    await fetchJSON(`${API_BASE}/api/scrape/manual`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    await Promise.all([loadProducts(), loadLogs(), loadStats()]);
  } catch (error) {
    console.error("Error al ejecutar scraping", error);
  } finally {
    elements.runScrapeBtn.disabled = false;
  }
}

function addEventListeners() {
  elements.websiteFilter.addEventListener("change", loadProducts);
  elements.searchInput.addEventListener("input", () => {
    clearTimeout(window.searchTimer);
    window.searchTimer = setTimeout(loadProducts, 300);
  });
  elements.sortFilter.addEventListener("change", loadProducts);
  elements.runScrapeBtn.addEventListener("click", runManualScrape);
}

async function init() {
  try {
    await loadWebsites();
    await Promise.all([loadStats(), loadProducts(), loadLogs()]);
    addEventListeners();
    setInterval(loadLogs, 10000);
  } catch (error) {
    console.error("Error inicializando dashboard", error);
  }
}

init();
