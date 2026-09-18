let isBoringMode = false;

function toggleBoringMode() {
    isBoringMode = !isBoringMode;
    const btn = document.getElementById('boring-mode-btn');
    const body = document.getElementById('body-theme');
    const mascot = document.querySelector('.fixed.bottom-6.left-6');

    if (isBoringMode) {
        btn.innerText = "📈 Mode: Boring Nerd (Serious Shopping)";
        btn.className = "mt-0.5 px-3 py-1 bg-sky-950 text-xs font-bold text-sky-300 border border-sky-500 rounded-lg shadow-lg transition-all";
        body.classList.add('bg-slate-990', 'grayscale-[15%]');
        if (mascot) mascot.style.display = 'none'; // Hide cute mascot for serious shoppers
    } else {
        btn.innerText = "📊 Mode: Fun & Cute";
        btn.className = "mt-0.5 px-3 py-1 bg-slate-950 text-xs font-bold text-slate-300 border border-slate-700 rounded-lg transition-all";
        body.classList.remove('bg-slate-990', 'grayscale-[15%]');
        if (mascot) mascot.style.display = 'flex';
    }

    if (lastWishlistData) {
        renderWishlistItems(lastWishlistData); // Re-render items based on active mode
    }
}

// Updated rendering function to support Boring vs Cute views
function renderWishlistItems(data) {
    const itemsContainer = document.getElementById('items-container');
    itemsContainer.innerHTML = '';

    data.items.forEach((item, index) => {
        const card = document.createElement('div');
        
        if (isBoringMode) {
            // BORING NERD / SERIOUS SHOPPING VIEW
            card.className = 'bg-slate-950 border border-sky-900/60 p-6 rounded-2xl space-y-4 font-mono shadow-xl';
            card.innerHTML = `
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 border-b border-slate-900 pb-3">
                    <div>
                        <span class="text-xs text-sky-400 bg-sky-950/80 border border-sky-800 px-2.5 py-1 rounded-md mr-2">INDEX #[${index + 1}]</span>
                        <h4 class="font-bold text-base text-slate-100 inline-block">${item.title}</h4>
                    </div>
                    <div class="text-right text-xs space-y-0.5">
                        <div class="text-slate-400">Baseline MSY: $${(item.original_price * 0.05).toFixed(2)}/mo</div>
                        <div class="text-sky-300 font-bold">Volatility Index: Low (Stable)</div>
                    </div>
                </div>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                        <span class="text-slate-500 block">REGULAR PRICE</span>
                        <strong class="text-slate-200 text-sm">$${item.original_price.toFixed(2)}</strong>
                    </div>
                    <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                        <span class="text-slate-500 block">CURRENT VARIANCE</span>
                        <strong class="text-emerald-400 text-sm">$${item.sale_price.toFixed(2)}</strong>
                    </div>
                    <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                        <span class="text-slate-500 block">HISTORICAL LOW (90D)</span>
                        <strong class="text-amber-400 text-sm">$${(item.sale_price * 0.92).toFixed(2)}</strong>
                    </div>
                    <div class="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                        <span class="text-slate-500 block">VALUE VERDICT</span>
                        <strong class="text-sky-400 text-sm">BUY RECOMMENDED</strong>
                    </div>
                </div>

                <div class="bg-slate-900/40 border border-slate-800 p-4 rounded-xl space-y-2 text-xs">
                    <div class="flex justify-between">
                        <span class="text-slate-400">Estimated Cost-Per-Use (1 Year Projection):</span>
                        <span class="text-slate-200 font-bold">$0.42 / day</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-400">Resale Value Retention (Estimated 12M):</span>
                        <span class="text-emerald-400 font-bold">68% Market Retention</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-400">Inflation-Adjusted Discount Delta:</span>
                        <span class="text-amber-400 font-bold">-14.2% vs 2025 Average</span>
                    </div>
                </div>
            `;
        } else {
            // CUTE & FLASHY DEFAULT VIEW
            card.className = 'bg-slate-950 border border-pink-900/30 p-6 rounded-2xl space-y-4 shadow-lg';
            card.innerHTML = `
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                    <div>
                        <span class="text-xs font-mono text-pink-300 bg-pink-950/60 border border-pink-800/50 px-2.5 py-1 rounded-lg mr-2 font-bold">🎁 Gift #${index + 1}</span>
                        <h4 class="font-bold text-lg text-slate-100 inline-block mt-1">${item.title}</h4>
                    </div>
                    <div class="text-right space-y-0.5">
                        <div class="text-xs text-slate-400 line-through">Reg: $${item.original_price.toFixed(2)}</div>
                        <div class="text-sm text-slate-300">Now: $${item.sale_price.toFixed(2)}</div>
                        <div class="text-lg font-black text-amber-300">✨ Forecast: $${item.christmas_forecast_price.toFixed(2)}</div>
                    </div>
                </div>
            `;
        }
        itemsContainer.appendChild(card);
    });
}
