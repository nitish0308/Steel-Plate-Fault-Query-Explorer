function renderTable(container, rows) {
  container.innerHTML = "";

  if (!Array.isArray(rows) || rows.length === 0) {
    container.innerHTML = "<p>No results.</p>";
    return;
  }

  const columns = Object.keys(rows[0]);
  const table = document.createElement("table");

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((col) => {
      const td = document.createElement("td");
      td.textContent = row[col];
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  container.appendChild(table);
}

function renderError(container, message) {
  container.innerHTML = `<p class="error">${message}</p>`;
}

async function runQuery(endpoint, params, containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = "<p>Loading...</p>";

  const url = new URL(`/api/${endpoint}`, window.location.origin);
  Object.entries(params || {}).forEach(([key, value]) => {
    url.searchParams.set(key, value);
  });

  try {
    const response = await fetch(url);
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      renderError(container, body.detail ? JSON.stringify(body.detail) : `Request failed (${response.status})`);
      return;
    }
    const data = await response.json();
    renderTable(container, data);
  } catch (err) {
    renderError(container, err.message);
  }
}

document.querySelectorAll("button[data-endpoint]").forEach((button) => {
  button.addEventListener("click", () => {
    const endpoint = button.dataset.endpoint;
    const containerId = `result-${endpoint}`;
    let params = {};

    switch (endpoint) {
      case "filter":
        params = {
          steel_type: document.getElementById("steel_type").value,
          min_thickness: document.getElementById("min_thickness").value,
          max_thickness: document.getElementById("max_thickness").value,
        };
        break;
      case "top-defects":
        params = { n: document.getElementById("n").value };
        break;
      case "search":
        params = {
          fault_type: document.getElementById("fault_type").value,
          min_area: document.getElementById("min_area").value,
        };
        break;
      default:
        params = {};
    }

    runQuery(endpoint, params, containerId);
  });
});
