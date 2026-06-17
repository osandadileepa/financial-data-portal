/**
 * Report form logic: pre-fill data, real-time calculations, and PDF generation.
 */

const ReportForm = {
    clientId: null,
    reportData: null,
    balances: {},
    totalFields: 0,

    async init() {
        // Extract client ID from /report/<id>
        const match = window.location.pathname.match(/\/report\/(\d+)/);
        if (!match) {
            App.showToast("Invalid report URL", "error");
            return;
        }
        this.clientId = parseInt(match[1], 10);

        try {
            App.setLoading(true, "Loading client data...");
            this.reportData = await App.api(`/api/clients/${this.clientId}/report-data`);
            this.renderForm();
            this.attachListeners();
            this.calculateTotals();
        } catch (error) {
            App.showToast(error.message, "error");
        } finally {
            App.setLoading(false);
        }
    },

    renderForm() {
        const data = this.reportData;
        const client = data.client;

        document.getElementById("report-title").textContent = `Generate Report for ${client.full_name}`;
        document.getElementById("client-subtitle").textContent = `Quarterly report data entry`;

        document.getElementById("inflow").value = client.monthly_salary;
        document.getElementById("outflow").value = client.monthly_expenses;

        // Private reserve balance
        const reserveInput = document.getElementById("private_reserve_balance");
        this.balances["private_reserve_balance"] = data.last_values["private_reserve_balance"] || "";
        reserveInput.value = this.balances["private_reserve_balance"];
        reserveInput.dataset.last = data.last_values["private_reserve_balance"] || "";
        this.addLastValueCheckbox(reserveInput.parentElement.parentElement, "private_reserve_balance", data.last_values["private_reserve_balance"]);

        this.renderAccountSection("retirement", data.retirement_accounts, data.last_values, "retirement_");
        this.renderAccountSection("non-retirement", data.non_retirement_accounts, data.last_values, "non_retirement_");
        this.renderTrustSection(data.trusts, data.last_values);
        this.renderLiabilitySection(data.liabilities, data.last_values);

        // Count total required fields
        let total = 1; // private reserve
        total += data.retirement_accounts.length;
        total += data.non_retirement_accounts.length;
        total += data.trusts.length;
        total += data.liabilities.length;
        this.totalFields = total;
        document.getElementById("total-fields").textContent = total;
    },

    renderAccountSection(section, accounts, lastValues, prefix) {
        const container = document.getElementById(`${section}-accounts`);
        container.innerHTML = "";
        if (!accounts.length) {
            container.innerHTML = `<p class="text-sm text-slate-500">No ${section} accounts configured for this client.</p>`;
            return;
        }

        accounts.forEach(account => {
            const key = `${prefix}${account.id}`;
            const lastValue = lastValues[key] || account.balance || "";
            this.balances[key] = "";

            const div = document.createElement("div");
            div.className = "grid grid-cols-1 md:grid-cols-2 gap-4 items-end account-row";
            div.innerHTML = `
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">
                        ${account.account_type} ending in ${account.last4}
                        <span class="text-xs font-normal text-slate-500 block">Owner: ${account.owner === "client2" ? "Client 2" : "Client 1"}</span>
                    </label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                        <input type="number" id="${key}" data-key="${key}" step="0.01" min="0" required
                            value=""
                            class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 focus:border-brand-500 focus:ring-brand-500 balance-input">
                    </div>
                </div>
                <div class="last-value-wrapper"></div>
            `;
            container.appendChild(div);

            const input = div.querySelector(`#${key}`);
            input.dataset.last = lastValue;
            this.addLastValueCheckbox(div.querySelector(".last-value-wrapper"), key, lastValue, input);
        });
    },

    renderTrustSection(trusts, lastValues) {
        const container = document.getElementById("trust-accounts");
        container.innerHTML = "";
        if (!trusts.length) {
            container.innerHTML = `<p class="text-sm text-slate-500">No trust properties configured for this client.</p>`;
            return;
        }

        trusts.forEach(trust => {
            const key = `trust_zillow_${trust.id}`;
            const lastValue = lastValues[key] || trust.zillow_value || "";
            this.balances[key] = "";

            const div = document.createElement("div");
            div.className = "grid grid-cols-1 md:grid-cols-2 gap-4 items-end account-row";
            div.innerHTML = `
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">${trust.property_address}</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                        <input type="number" id="${key}" data-key="${key}" step="0.01" min="0" required
                            value=""
                            class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 focus:border-brand-500 focus:ring-brand-500 balance-input">
                    </div>
                </div>
                <div class="last-value-wrapper"></div>
            `;
            container.appendChild(div);

            const input = div.querySelector(`#${key}`);
            input.dataset.last = lastValue;
            this.addLastValueCheckbox(div.querySelector(".last-value-wrapper"), key, lastValue, input);
        });
    },

    renderLiabilitySection(liabilities, lastValues) {
        const container = document.getElementById("liability-accounts");
        container.innerHTML = "";
        if (!liabilities.length) {
            container.innerHTML = `<p class="text-sm text-slate-500">No liabilities configured for this client.</p>`;
            return;
        }

        liabilities.forEach(liability => {
            const key = `liability_${liability.id}`;
            const lastValue = lastValues[key] || liability.balance || "";
            this.balances[key] = "";

            const div = document.createElement("div");
            div.className = "grid grid-cols-1 md:grid-cols-2 gap-4 items-end account-row";
            div.innerHTML = `
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">
                        ${liability.liability_type.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
                        <span class="text-xs font-normal text-slate-500 block">Interest rate: ${liability.interest_rate}%</span>
                    </label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">$</span>
                        <input type="number" id="${key}" data-key="${key}" step="0.01" min="0" required
                            value=""
                            class="w-full rounded-md border border-slate-300 pl-7 pr-3 py-2 focus:border-brand-500 focus:ring-brand-500 balance-input">
                    </div>
                </div>
                <div class="last-value-wrapper"></div>
            `;
            container.appendChild(div);

            const input = div.querySelector(`#${key}`);
            input.dataset.last = lastValue;
            this.addLastValueCheckbox(div.querySelector(".last-value-wrapper"), key, lastValue, input);
        });
    },

    addLastValueCheckbox(container, key, lastValue, inputToUpdate = null) {
        if (!lastValue && lastValue !== 0) return;

        const wrapper = document.createElement("label");
        wrapper.className = "flex items-center gap-2 text-sm text-slate-600 cursor-pointer";
        wrapper.innerHTML = `
            <input type="checkbox" class="use-last-value rounded border-slate-300 text-brand-600 focus:ring-brand-500" data-key="${key}">
            <span>Use last value (${App.formatCurrency(lastValue)})</span>
        `;
        container.appendChild(wrapper);

        const checkbox = wrapper.querySelector("input");
        checkbox.addEventListener("change", (e) => {
            const input = inputToUpdate || document.querySelector(`#${key}`);
            if (e.target.checked) {
                input.value = lastValue;
                input.disabled = true;
            } else {
                input.value = "";
                input.disabled = false;
                input.focus();
            }
            input.dispatchEvent(new Event("input"));
        });
    },

    attachListeners() {
        document.querySelectorAll(".balance-input").forEach(input => {
            input.addEventListener("input", () => this.calculateTotals());
        });

        document.getElementById("generate-report").addEventListener("click", () => this.generateReport());
    },

    calculateTotals() {
        const data = this.reportData;
        const balances = {};
        let completed = 0;

        // Private reserve
        const reserveInput = document.getElementById("private_reserve_balance");
        balances["private_reserve_balance"] = reserveInput.value;
        if (reserveInput.value !== "") completed++;

        // Collect all balance inputs
        document.querySelectorAll(".balance-input").forEach(input => {
            const key = input.dataset.key;
            balances[key] = input.value;
            if (input.value !== "") completed++;
        });

        this.balances = balances;

        const inflow = App.parseFloat(data.client.monthly_salary);
        const outflow = App.parseFloat(data.client.monthly_expenses);
        const excess = inflow - outflow;
        const reserveTarget = App.parseFloat(data.client.private_reserve_target);

        let client1Retirement = 0;
        let client2Retirement = 0;
        data.retirement_accounts.forEach(account => {
            const key = `retirement_${account.id}`;
            const balance = App.parseFloat(balances[key]);
            if (account.owner === "client2") {
                client2Retirement += balance;
            } else {
                client1Retirement += balance;
            }
        });

        let nonRetirement = 0;
        data.non_retirement_accounts.forEach(account => {
            const key = `non_retirement_${account.id}`;
            nonRetirement += App.parseFloat(balances[key]);
        });

        let trustTotal = 0;
        data.trusts.forEach(trust => {
            const key = `trust_zillow_${trust.id}`;
            trustTotal += App.parseFloat(balances[key]);
        });

        let liabilitiesTotal = 0;
        data.liabilities.forEach(liability => {
            const key = `liability_${liability.id}`;
            liabilitiesTotal += App.parseFloat(balances[key]);
        });

        const grandTotal = client1Retirement + client2Retirement + nonRetirement + trustTotal;

        // Update UI
        document.getElementById("total-excess").textContent = App.formatCurrency(excess);
        document.getElementById("total-reserve-target").textContent = App.formatCurrency(reserveTarget);
        document.getElementById("total-client1-retirement").textContent = App.formatCurrency(client1Retirement);
        document.getElementById("total-client2-retirement").textContent = App.formatCurrency(client2Retirement);
        document.getElementById("total-non-retirement").textContent = App.formatCurrency(nonRetirement);
        document.getElementById("total-trust").textContent = App.formatCurrency(trustTotal);
        document.getElementById("total-grand").textContent = App.formatCurrency(grandTotal);
        document.getElementById("total-liabilities").textContent = App.formatCurrency(liabilitiesTotal);

        document.getElementById("completed-fields").textContent = completed;
        const progress = this.totalFields ? Math.round((completed / this.totalFields) * 100) : 0;
        document.getElementById("validation-progress").style.width = `${progress}%`;

        return {
            inflow, outflow, excess, reserveTarget,
            client1Retirement, client2Retirement, nonRetirement,
            trustTotal, grandTotal, liabilitiesTotal,
        };
    },

    validate() {
        const missing = [];
        const reserveInput = document.getElementById("private_reserve_balance");
        if (reserveInput.value === "") {
            missing.push("Private Reserve balance");
            reserveInput.classList.add("error");
        } else {
            reserveInput.classList.remove("error");
        }

        document.querySelectorAll(".balance-input").forEach(input => {
            if (input.value === "") {
                missing.push(input.previousElementSibling?.previousElementSibling?.textContent || input.dataset.key);
                input.classList.add("error");
            } else {
                input.classList.remove("error");
            }
        });

        const quarter = document.getElementById("quarter").value;
        const year = document.getElementById("year").value;
        if (!quarter) missing.push("Quarter");
        if (!year) missing.push("Year");

        return missing;
    },

    async generateReport() {
        clearErrors();
        const missing = this.validate();
        if (missing.length > 0) {
            App.showToast("Please complete all required fields", "error");
            return;
        }

        const quarter = document.getElementById("quarter").value;
        const year = document.getElementById("year").value;

        const payload = {
            quarter,
            year: parseInt(year, 10),
            balances: { ...this.balances },
        };

        try {
            App.setLoading(true, "Generating PDFs...");
            const result = await App.api(`/api/clients/${this.clientId}/reports`, {
                method: "POST",
                body: JSON.stringify(payload),
            });

            App.showToast("Report generated successfully");

            const downloadSection = document.getElementById("download-section");
            downloadSection.classList.remove("hidden");
            document.getElementById("download-sacs").href = result.download_urls.sacs;
            document.getElementById("download-tcc").href = result.download_urls.tcc;

            // Scroll to download section
            downloadSection.scrollIntoView({ behavior: "smooth", block: "center" });
        } catch (error) {
            App.showToast(error.message, "error");
        } finally {
            App.setLoading(false);
        }
    },
};

function clearErrors() {
    document.querySelectorAll("input.error").forEach(el => el.classList.remove("error"));
}

document.addEventListener("DOMContentLoaded", () => {
    ReportForm.init();
});
