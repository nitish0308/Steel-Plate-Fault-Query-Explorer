const FAULT_TYPES = ["Pastry", "Z_Scratch", "K_Scatch", "Stains", "Dirtiness", "Bumps", "Other_Faults"];

function buildActionsCell(row, tr) {
  const td = document.createElement("td");

  const select = document.createElement("select");
  FAULT_TYPES.forEach((ft) => {
    const option = document.createElement("option");
    option.value = ft;
    option.textContent = ft;
    if (ft === row.fault_type) option.selected = true;
    select.appendChild(option);
  });

  const updateBtn = document.createElement("button");
  updateBtn.textContent = "Update";
  updateBtn.addEventListener("click", async () => {
    updateBtn.disabled = true;
    try {
      const response = await fetch(`/api/faults/${row.rowid}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fault_type: select.value }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        alert(body.detail ? JSON.stringify(body.detail) : `Update failed (${response.status})`);
        return;
      }
      const faultTypeCell = tr.querySelector('td[data-fault-type-cell="true"]');
      if (faultTypeCell) faultTypeCell.textContent = select.value;
    } finally {
      updateBtn.disabled = false;
    }
  });

  const deleteBtn = document.createElement("button");
  deleteBtn.textContent = "Delete";
  deleteBtn.classList.add("danger");
  deleteBtn.addEventListener("click", async () => {
    if (!confirm(`Delete fault record rowid=${row.rowid}?`)) return;
    deleteBtn.disabled = true;
    try {
      const response = await fetch(`/api/faults/${row.rowid}`, { method: "DELETE" });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        alert(body.detail ? JSON.stringify(body.detail) : `Delete failed (${response.status})`);
        deleteBtn.disabled = false;
        return;
      }
      tr.remove();
    } catch (err) {
      alert(err.message);
      deleteBtn.disabled = false;
    }
  });

  td.appendChild(select);
  td.appendChild(updateBtn);
  td.appendChild(deleteBtn);
  return td;
}

function renderTable(container, rows) {
  container.innerHTML = "";

  if (!Array.isArray(rows) || rows.length === 0) {
    container.innerHTML = "<p>No results.</p>";
    return;
  }

  const hasActions = Object.prototype.hasOwnProperty.call(rows[0], "rowid");
  const columns = Object.keys(rows[0]);
  const table = document.createElement("table");

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headRow.appendChild(th);
  });
  if (hasActions) {
    const th = document.createElement("th");
    th.textContent = "Actions";
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((col) => {
      const td = document.createElement("td");
      td.textContent = row[col];
      if (col === "fault_type") td.dataset.faultTypeCell = "true";
      tr.appendChild(td);
    });
    if (hasActions) {
      tr.appendChild(buildActionsCell(row, tr));
    }
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

async function postQuery(endpoint, body, containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = "<p>Loading...</p>";

  try {
    const response = await fetch(`/api/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const responseBody = await response.json().catch(() => ({}));
      renderError(container, responseBody.detail ? JSON.stringify(responseBody.detail) : `Request failed (${response.status})`);
      return;
    }
    const data = await response.json();
    renderTable(container, data);
  } catch (err) {
    renderError(container, err.message);
  }
}

async function putFaultType(rowid, faultType, containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = "<p>Loading...</p>";

  try {
    const response = await fetch(`/api/faults/${rowid}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fault_type: faultType }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      renderError(container, data.detail ? JSON.stringify(data.detail) : `Request failed (${response.status})`);
      return;
    }
    container.innerHTML = `<p>Updated rowid ${data.rowid} to fault_type "${data.fault_type}".</p>`;
  } catch (err) {
    renderError(container, err.message);
  }
}

async function deleteFaultRow(rowid, containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = "<p>Loading...</p>";

  try {
    const response = await fetch(`/api/faults/${rowid}`, { method: "DELETE" });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      renderError(container, data.detail ? JSON.stringify(data.detail) : `Request failed (${response.status})`);
      return;
    }
    container.innerHTML = `<p>Deleted rowid ${data.rowid}.</p>`;
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
      case "search-batch": {
        const selected = Array.from(document.getElementById("fault_types").selectedOptions).map((o) => o.value);
        postQuery(
          endpoint,
          { fault_types: selected, min_area: Number(document.getElementById("batch_min_area").value) },
          containerId
        );
        return;
      }
      case "update-fault": {
        const rowid = document.getElementById("update_rowid").value;
        const faultType = document.getElementById("update_fault_type").value;
        if (!rowid) {
          renderError(document.getElementById(containerId), "Row ID is required.");
          return;
        }
        putFaultType(rowid, faultType, containerId);
        return;
      }
      case "delete-fault": {
        const rowid = document.getElementById("delete_rowid").value;
        if (!rowid) {
          renderError(document.getElementById(containerId), "Row ID is required.");
          return;
        }
        if (!confirm(`Delete fault record rowid=${rowid}?`)) return;
        deleteFaultRow(rowid, containerId);
        return;
      }
      default:
        params = {};
    }

    runQuery(endpoint, params, containerId);
  });
});
