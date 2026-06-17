/**
 * Dashboard page logic: list clients, show last report date, and provide
 * quick actions to generate or edit a report.
 */

document.addEventListener("DOMContentLoaded", async () => {
    const grid = document.getElementById("client-grid");
    if (!grid) return;

    try {
        const clients = await App.api("/api/clients");
        renderClients(clients);
    } catch (error) {
        grid.innerHTML = `<div class="text-center py-12 text-red-500 col-span-full">Failed to load clients: ${error.message}</div>`;
    }
});

function renderClients(clients) {
    const grid = document.getElementById("client-grid");
    if (!clients.length) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12 bg-white rounded-xl border border-slate-200">
                <p class="text-slate-500 mb-4">No clients yet.</p>
                <a href="/client/new" class="inline-block bg-brand-700 text-white px-4 py-2 rounded-md font-medium hover:bg-brand-800">Add your first client</a>
            </div>
        `;
        return;
    }

    grid.innerHTML = clients.map(client => `
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between hover:shadow-md transition">
            <div>
                <h3 class="text-lg font-bold text-slate-900">${escapeHtml(client.full_name)}</h3>
                <p class="text-sm text-slate-500 mt-1">Age: ${client.age ?? "—"}</p>
                <p class="text-sm text-slate-500">Last report: ${client.last_report_date ? formatDate(client.last_report_date) : "No reports yet"}</p>
            </div>
            <div class="mt-5 flex flex-col gap-2">
                <a href="/report/${client.id}" class="w-full text-center bg-brand-700 text-white px-4 py-2 rounded-md font-medium hover:bg-brand-800 transition">Generate Report</a>
                <div class="flex gap-2">
                    <a href="/client/${client.id}/reports" class="flex-1 text-center bg-white border border-slate-300 text-slate-700 px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-50 transition">Reports</a>
                    <a href="/client/${client.id}" class="flex-1 text-center bg-white border border-slate-300 text-slate-700 px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-50 transition">Edit</a>
                </div>
                <div class="flex gap-2">
                    <button type="button" data-id="${client.id}" class="delete-client flex-1 text-center bg-white border border-red-200 text-red-600 px-3 py-2 rounded-md text-sm font-medium hover:bg-red-50 transition">Delete</button>
                </div>
            </div>
        </div>
    `).join("");

    document.querySelectorAll(".delete-client").forEach(btn => {
        btn.addEventListener("click", handleDelete);
    });
}

async function handleDelete(event) {
    const id = event.target.dataset.id;
    if (!confirm("Are you sure you want to delete this client and all related reports?")) return;

    try {
        await App.api(`/api/clients/${id}`, { method: "DELETE" });
        App.showToast("Client deleted");
        const clients = await App.api("/api/clients");
        renderClients(clients);
    } catch (error) {
        App.showToast(error.message, "error");
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
