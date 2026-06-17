/**
 * Client form logic: dynamic sections, age calculation, and save.
 */

document.addEventListener("DOMContentLoaded", () => {
    const clientData = window.initialClientData || null;

    if (clientData) {
        document.getElementById("form-title").textContent = "Edit Client";
        updateAgeDisplays();
    }

    initDynamicSection("retirement", clientData?.retirement_accounts || [], createRetirementRow, 6);
    initDynamicSection("non-retirement", clientData?.non_retirement_accounts || [], createNonRetirementRow, 6);
    initDynamicSection("trust", clientData?.trusts || [], createTrustRow, 10);
    initDynamicSection("liability", clientData?.liabilities || [], createLiabilityRow, 3);

    document.getElementById("dob")?.addEventListener("change", updateAgeDisplays);
    document.getElementById("spouse_dob")?.addEventListener("change", updateAgeDisplays);
    document.getElementById("client-form")?.addEventListener("submit", handleSubmit);

    // Add a default row for required sections if empty
    if (!clientData || !clientData.retirement_accounts?.length) {
        document.getElementById("add-retirement")?.click();
    }
    if (!clientData || !clientData.non_retirement_accounts?.length) {
        document.getElementById("add-non-retirement")?.click();
    }
    // Trust and liabilities are optional
});

function updateAgeDisplays() {
    const dob = document.getElementById("dob")?.value;
    const age = App.calculateAge(dob);
    const ageEl = document.getElementById("age-display");
    if (ageEl && age !== null) ageEl.textContent = `Age: ${age}`;

    const spouseDob = document.getElementById("spouse_dob")?.value;
    const spouseAge = App.calculateAge(spouseDob);
    const spouseAgeEl = document.getElementById("spouse-age-display");
    if (spouseAgeEl && spouseAge !== null) spouseAgeEl.textContent = `Age: ${spouseAge}`;
}

function initDynamicSection(section, existingRows, createRow, maxRows) {
    const container = document.getElementById(`${section}-accounts`);
    const addButton = document.getElementById(`add-${section}`);
    if (!container || !addButton) return;

    let counter = 0;

    function addRow(data = {}) {
        if (container.children.length >= maxRows) {
            App.showToast(`Maximum ${maxRows} ${section} entries allowed`, "error");
            return;
        }
        const row = createRow(counter++, data);
        container.appendChild(row);
    }

    addButton.addEventListener("click", () => addRow());

    container.addEventListener("click", (e) => {
        if (e.target.closest(".remove-row")) {
            e.target.closest(".account-row").remove();
            updatePrivateReserveTarget();
        }
    });

    existingRows.forEach(data => addRow(data));

    // If trusts is empty and we want at least one, add a default
    if (section === "trust" && existingRows.length === 0) {
        // Trust is optional, don't auto-add
    }
}

function createRetirementRow(index, data = {}) {
    const div = document.createElement("div");
    div.className = "account-row grid grid-cols-1 md:grid-cols-7 gap-4 items-end";
    div.innerHTML = `
        <div class="md:col-span-2">
            <label class="block text-xs font-medium text-slate-600 mb-1">Owner</label>
            <select name="retirement_owner_${index}" class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm owner-select">
                <option value="client1" ${data.owner === "client1" ? "selected" : ""}>Client 1</option>
                <option value="client2" ${data.owner === "client2" ? "selected" : ""}>Client 2</option>
            </select>
        </div>
        <div class="md:col-span-2">
            <label class="block text-xs font-medium text-slate-600 mb-1">Account Type</label>
            <select name="retirement_type_${index}" required class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
                <option value="">Select...</option>
                <option value="IRA" ${data.account_type === "IRA" ? "selected" : ""}>IRA</option>
                <option value="Roth IRA" ${data.account_type === "Roth IRA" ? "selected" : ""}>Roth IRA</option>
                <option value="401K" ${data.account_type === "401K" ? "selected" : ""}>401K</option>
                <option value="Pension" ${data.account_type === "Pension" ? "selected" : ""}>Pension</option>
            </select>
        </div>
        <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Last 4</label>
            <input type="text" name="retirement_last4_${index}" maxlength="4" required value="${data.last4 || ""}"
                class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
        </div>
        <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Balance</label>
            <div class="relative">
                <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                <input type="number" name="retirement_balance_${index}" step="0.01" min="0" value="${data.balance || ""}"
                    class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 text-sm">
            </div>
        </div>
        <div class="flex gap-2">
            <div class="flex-1">
                <label class="block text-xs font-medium text-slate-600 mb-1">Cash Balance</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                    <input type="number" name="retirement_cash_balance_${index}" step="0.01" min="0" value="${data.cash_balance || ""}"
                        class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 text-sm">
                </div>
            </div>
            <button type="button" class="remove-row text-red-500 hover:text-red-700 px-2">×</button>
        </div>
    `;
    return div;
}

function createNonRetirementRow(index, data = {}) {
    const div = document.createElement("div");
    div.className = "account-row grid grid-cols-1 md:grid-cols-4 gap-4 items-end";
    div.innerHTML = `
        <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Account Type</label>
            <select name="non_retirement_type_${index}" required class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
                <option value="">Select...</option>
                <option value="brokerage" ${data.account_type === "brokerage" ? "selected" : ""}>Brokerage</option>
                <option value="joint" ${data.account_type === "joint" ? "selected" : ""}>Joint</option>
            </select>
        </div>
        <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Last 4</label>
            <input type="text" name="non_retirement_last4_${index}" maxlength="4" required value="${data.last4 || ""}"
                class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
        </div>
        <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Balance</label>
            <div class="relative">
                <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                <input type="number" name="non_retirement_balance_${index}" step="0.01" min="0" value="${data.balance || ""}"
                    class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 text-sm">
            </div>
        </div>
        <div class="flex gap-2">
            <div class="flex-1">
                <label class="block text-xs font-medium text-slate-600 mb-1">Cash Balance</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                    <input type="number" name="non_retirement_cash_balance_${index}" step="0.01" min="0" value="${data.cash_balance || ""}"
                        class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 text-sm">
                </div>
            </div>
            <button type="button" class="remove-row text-red-500 hover:text-red-700 px-2">×</button>
        </div>
    `;
    return div;
}

function createTrustRow(index, data = {}) {
    const div = document.createElement("div");
    div.className = "account-row grid grid-cols-1 md:grid-cols-2 gap-4 items-end";
    div.innerHTML = `
        <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Property Address</label>
            <input type="text" name="trust_address_${index}" required value="${data.property_address || ""}"
                class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
        </div>
        <div class="flex gap-2">
            <div class="flex-1">
                <label class="block text-xs font-medium text-slate-600 mb-1">Zillow Value</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                    <input type="number" name="trust_value_${index}" step="0.01" min="0" value="${data.zillow_value || ""}"
                        class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 text-sm">
                </div>
            </div>
            <button type="button" class="remove-row text-red-500 hover:text-red-700 px-2">×</button>
        </div>
    `;
    return div;
}

function createLiabilityRow(index, data = {}) {
    const div = document.createElement("div");
    div.className = "account-row grid grid-cols-1 md:grid-cols-4 gap-4 items-end";
    div.innerHTML = `
        <div class="md:col-span-2">
            <label class="block text-xs font-medium text-slate-600 mb-1">Liability Type</label>
            <select name="liability_type_${index}" required class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
                <option value="">Select...</option>
                <option value="mortgage" ${data.liability_type === "mortgage" ? "selected" : ""}>Mortgage</option>
                <option value="auto_loan" ${data.liability_type === "auto_loan" ? "selected" : ""}>Auto Loan</option>
            </select>
        </div>
        <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Interest Rate</label>
            <div class="relative">
                <input type="number" name="liability_rate_${index}" step="0.01" min="0" value="${data.interest_rate || ""}"
                    class="w-full rounded-md border border-slate-300 pr-8 pl-3 py-2 text-sm">
                <span class="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500">%</span>
            </div>
        </div>
        <div class="flex gap-2">
            <div class="flex-1">
                <label class="block text-xs font-medium text-slate-600 mb-1">Balance</label>
                <div class="relative">
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                    <input type="number" name="liability_balance_${index}" step="0.01" min="0" value="${data.balance || ""}"
                        class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 text-sm">
                </div>
            </div>
            <button type="button" class="remove-row text-red-500 hover:text-red-700 px-2">×</button>
        </div>
    `;
    return div;
}

function updatePrivateReserveTarget() {
    // Not currently needed on the client side; target is computed on save.
}

async function handleSubmit(event) {
    event.preventDefault();
    clearErrors();

    const clientId = document.getElementById("client-id")?.value;
    const isEdit = !!clientId;

    const payload = buildPayload();
    const missing = validatePayload(payload);
    if (missing.length > 0) {
        highlightErrors(missing);
        App.showToast("Please fill all required fields", "error");
        return;
    }

    try {
        App.setLoading(true, isEdit ? "Updating client..." : "Creating client...");
        const url = isEdit ? `/api/clients/${clientId}` : "/api/clients";
        const method = isEdit ? "PUT" : "POST";
        const result = await App.api(url, {
            method,
            body: JSON.stringify(payload),
        });
        App.showToast(isEdit ? "Client updated" : "Client created");
        window.location.href = "/";
    } catch (error) {
        App.setLoading(false);
        App.showToast(error.message, "error");
    }
}

function buildPayload() {
    const payload = {
        first_name: document.getElementById("first_name").value.trim(),
        last_name: document.getElementById("last_name").value.trim(),
        spouse_first_name: document.getElementById("spouse_first_name").value.trim() || null,
        spouse_last_name: document.getElementById("spouse_last_name").value.trim() || null,
        dob: document.getElementById("dob").value || null,
        spouse_dob: document.getElementById("spouse_dob").value || null,
        ssn_last4: document.getElementById("ssn_last4").value.trim(),
        spouse_ssn_last4: document.getElementById("spouse_ssn_last4").value.trim() || null,
        monthly_salary: document.getElementById("monthly_salary").value,
        monthly_expenses: document.getElementById("monthly_expenses").value,
        private_reserve_target: document.getElementById("private_reserve_target").value,
        retirement_accounts: [],
        non_retirement_accounts: [],
        trusts: [],
        liabilities: [],
    };

    document.querySelectorAll("#retirement-accounts .account-row").forEach(row => {
        const owner = row.querySelector('select[name^="retirement_owner_"]').value;
        const type = row.querySelector('select[name^="retirement_type_"]').value;
        const last4 = row.querySelector('input[name^="retirement_last4_"]').value.trim();
        const balance = row.querySelector('input[name^="retirement_balance_"]').value;
        const cashBalance = row.querySelector('input[name^="retirement_cash_balance_"]').value;
        if (type && last4) {
            payload.retirement_accounts.push({ owner, account_type: type, last4, balance, cash_balance: cashBalance });
        }
    });

    document.querySelectorAll("#non-retirement-accounts .account-row").forEach(row => {
        const type = row.querySelector('select[name^="non_retirement_type_"]').value;
        const last4 = row.querySelector('input[name^="non_retirement_last4_"]').value.trim();
        const balance = row.querySelector('input[name^="non_retirement_balance_"]').value;
        const cashBalance = row.querySelector('input[name^="non_retirement_cash_balance_"]').value;
        if (type && last4) {
            payload.non_retirement_accounts.push({ account_type: type, last4, balance, cash_balance: cashBalance });
        }
    });

    document.querySelectorAll("#trusts .account-row").forEach(row => {
        const address = row.querySelector('input[name^="trust_address_"]').value.trim();
        const value = row.querySelector('input[name^="trust_value_"]').value;
        if (address) {
            payload.trusts.push({ property_address: address, zillow_value: value });
        }
    });

    document.querySelectorAll("#liabilities .account-row").forEach(row => {
        const type = row.querySelector('select[name^="liability_type_"]').value;
        const rate = row.querySelector('input[name^="liability_rate_"]').value;
        const balance = row.querySelector('input[name^="liability_balance_"]').value;
        if (type) {
            payload.liabilities.push({ liability_type: type, interest_rate: rate, balance });
        }
    });

    return payload;
}

function validatePayload(payload) {
    const missing = [];
    const required = ["first_name", "last_name", "dob", "ssn_last4", "monthly_salary", "monthly_expenses"];
    required.forEach(field => {
        if (!payload[field]) missing.push(field);
    });

    if (payload.retirement_accounts.length === 0) missing.push("retirement_accounts");
    if (payload.non_retirement_accounts.length === 0) missing.push("non_retirement_accounts");
    if (payload.liabilities.length > 3) missing.push("liabilities");

    return missing;
}

function highlightErrors(missing) {
    missing.forEach(field => {
        const el = document.getElementById(field);
        if (el) el.classList.add("error");
    });
    if (missing.includes("retirement_accounts")) {
        document.getElementById("retirement-accounts")?.classList.add("error");
    }
    if (missing.includes("non_retirement_accounts")) {
        document.getElementById("non-retirement-accounts")?.classList.add("error");
    }
}

function clearErrors() {
    document.querySelectorAll("input.error, select.error, textarea.error").forEach(el => el.classList.remove("error"));
    document.querySelectorAll(".account-row.error").forEach(el => el.classList.remove("error"));
}
