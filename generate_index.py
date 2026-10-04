import re

with open("backup/index.html", "r") as f:
    old_code = f.read()

# I will construct a completely new index.html string using Tailwind CSS
html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PrintHub SaaS</title>
    
    <!-- CDNs -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script src="https://cdn.jsdelivr.net/npm/pdf-lib/dist/pdf-lib.min.js"></script>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js"></script>

    <!-- Google Fonts: Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #0f172a; padding-bottom: 120px; }
        
        /* Smooth animations */
        .fade-in { animation: fadeIn 0.3s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        /* Dropzone animations */
        .dropzone-pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); } 70% { box-shadow: 0 0 0 15px rgba(59, 130, 246, 0); } 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); } }

        /* Hide scrollbar for grid */
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        
        /* Checkbox/Radio styles */
        .radio-custom:checked + div { border-color: #3b82f6; background-color: #eff6ff; }
        .radio-custom:checked + div .radio-circle { border-color: #3b82f6; background-color: #3b82f6; }
    </style>
</head>
<body class="antialiased min-h-screen selection:bg-blue-200">

    <!-- Top Loading Bar (Optional, but looks nice) -->
    <div id="top-loader" class="fixed top-0 left-0 w-full h-1 bg-blue-600 hidden z-50 transition-all duration-300"></div>

    <main class="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
        
        <!-- HEADER -->
        <header class="flex flex-col items-center justify-center text-center space-y-4 my-8 fade-in">
            <div id="shop-header-container" class="flex flex-col items-center justify-center gap-3">
                <div class="h-20 w-20 bg-slate-200 rounded-full flex items-center justify-center animate-pulse" id="header-skeleton-logo"></div>
                <h1 class="text-3xl font-bold tracking-tight text-slate-900" id="shop-title">Loading...</h1>
            </div>
            <p class="text-slate-500 font-medium flex items-center gap-2" id="shop-location">
                <i data-lucide="map-pin" class="w-4 h-4"></i> <span>Initializing Secure Terminal...</span>
            </p>
        </header>

        <!-- OFFER BANNER -->
        <div id="offer-banner" class="hidden fade-in w-full bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-4 shadow-lg shadow-blue-500/30 text-white mb-8 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="bg-white/20 p-2 rounded-lg backdrop-blur-sm"><i data-lucide="sparkles" class="w-5 h-5 text-yellow-300"></i></div>
                <div class="font-medium text-sm sm:text-base" id="offer-text">Special Offer: 50% Off!</div>
            </div>
        </div>

        <!-- UPLOAD ZONE -->
        <div id="dropzone" class="fade-in bg-white border-2 border-dashed border-blue-300 hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 rounded-3xl p-10 text-center cursor-pointer group shadow-sm flex flex-col items-center justify-center gap-4" onclick="document.getElementById('file-input').click()">
            <div class="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300 dropzone-pulse">
                <i data-lucide="upload-cloud" class="w-8 h-8"></i>
            </div>
            <div>
                <h3 class="text-xl font-bold text-slate-800">Tap to upload documents</h3>
                <p class="text-slate-500 mt-2 text-sm">PDF, PNG, and JPG up to 50MB</p>
            </div>
            <input type="file" id="file-input" multiple accept=".pdf,.png,.jpg,.jpeg" class="hidden">
        </div>

        <!-- FILE LIST -->
        <div id="file-list" class="mt-8 space-y-4"></div>

        <!-- USER DETAILS -->
        <div class="fade-in bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-100 mt-8">
            <h2 class="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <i data-lucide="user" class="w-5 h-5 text-blue-600"></i> Your Details
            </h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Full Name</label>
                    <input type="text" id="c_name" placeholder="John Doe" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all">
                </div>
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Phone Number</label>
                    <input type="tel" id="c_phone" placeholder="9876543210" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all">
                </div>
                <div class="sm:col-span-2">
                    <label class="block text-sm font-semibold text-slate-700 mb-2">Special Instructions <span class="text-slate-400 font-normal">(Optional)</span></label>
                    <textarea id="c_notes" rows="2" placeholder="Staple the pages together..." class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"></textarea>
                </div>
            </div>
        </div>

        <!-- PAYMENT METHOD -->
        <div class="fade-in bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-slate-100 mt-8 mb-12">
            <h2 class="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <i data-lucide="credit-card" class="w-5 h-5 text-blue-600"></i> Payment Method
            </h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <label class="relative cursor-pointer">
                    <input type="radio" name="payment_method" value="shop" checked class="radio-custom sr-only" onchange="updatePaymentUI()">
                    <div class="flex items-center gap-4 p-4 rounded-2xl border-2 border-slate-200 hover:bg-slate-50 transition-all">
                        <div class="radio-circle w-5 h-5 rounded-full border-2 border-slate-300 flex items-center justify-center transition-colors"></div>
                        <div class="flex flex-col">
                            <span class="font-bold text-slate-800">Pay at Shop</span>
                            <span class="text-xs text-slate-500">Pay directly when you pick up</span>
                        </div>
                        <i data-lucide="store" class="w-6 h-6 text-slate-400 ml-auto"></i>
                    </div>
                </label>
                <label class="relative cursor-pointer">
                    <input type="radio" name="payment_method" value="online" class="radio-custom sr-only" onchange="updatePaymentUI()">
                    <div class="flex items-center gap-4 p-4 rounded-2xl border-2 border-slate-200 hover:bg-slate-50 transition-all">
                        <div class="radio-circle w-5 h-5 rounded-full border-2 border-slate-300 flex items-center justify-center transition-colors"></div>
                        <div class="flex flex-col">
                            <span class="font-bold text-slate-800">Pay Online</span>
                            <span class="text-xs text-slate-500">Fast, secure UPI & Cards</span>
                        </div>
                        <i data-lucide="smartphone" class="w-6 h-6 text-slate-400 ml-auto"></i>
                    </div>
                </label>
            </div>
        </div>
    </main>

    <!-- FLOATING CHECKOUT FOOTER (Glassmorphism) -->
    <div class="fixed bottom-0 left-0 w-full bg-white/80 backdrop-blur-xl border-t border-slate-200 p-4 sm:p-6 z-40 pb-safe">
        <div class="max-w-4xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
            <div class="flex flex-col text-center sm:text-left">
                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Amount</span>
                <strong id="total-price" class="text-3xl font-extrabold text-blue-600 leading-none mt-1">₹0.00</strong>
            </div>
            <button onclick="handleCheckout()" class="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-10 rounded-2xl shadow-xl shadow-blue-500/30 transition-all active:scale-95 flex items-center justify-center gap-2">
                <i data-lucide="zap" class="w-5 h-5"></i> Place Order
            </button>
        </div>
    </div>

    <!-- FULL SCREEN LOADER / OVERLAY -->
    <div id="loading-overlay" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4 transition-opacity duration-300">
        <div class="bg-white rounded-3xl p-8 max-w-sm w-full text-center shadow-2xl scale-100 transition-transform">
            <div class="w-16 h-16 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin mx-auto mb-6"></div>
            <h2 id="overlay-title" class="text-xl font-bold text-slate-800 mb-2">Connecting...</h2>
            <p id="overlay-desc" class="text-slate-500 text-sm">Initializing secure terminal.</p>
            <div id="overlay-error" class="hidden mt-4 bg-red-50 text-red-600 p-3 rounded-lg text-sm text-left"></div>
            <button id="btn-close-error" class="hidden mt-6 w-full bg-slate-900 text-white font-bold py-3 rounded-xl hover:bg-slate-800" onclick="closeError()">Dismiss</button>
        </div>
    </div>

    <!-- OTP SUCCESS MODAL -->
    <div id="otp-modal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-8 max-w-sm w-full text-center shadow-2xl relative overflow-hidden">
            <div class="absolute top-0 left-0 w-full h-2 bg-green-500"></div>
            <div class="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <i data-lucide="check-circle-2" class="w-8 h-8"></i>
            </div>
            <h2 class="text-2xl font-bold text-slate-800 mb-2">Order Successful!</h2>
            <p class="text-slate-500 text-sm mb-6">Your files have been securely transmitted to the shop printer.</p>
            
            <div class="bg-slate-50 border-2 border-slate-200 rounded-2xl p-6 mb-6">
                <div class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Your Pickup PIN</div>
                <div id="otp-display-value" class="text-5xl font-extrabold text-slate-900 tracking-widest">1234</div>
            </div>
            
            <div class="bg-red-50 text-red-700 p-4 rounded-xl text-sm font-semibold mb-6 flex items-start gap-3 text-left">
                <i data-lucide="alert-triangle" class="w-5 h-5 shrink-0 mt-0.5"></i>
                <p>Take a screenshot now! This PIN will disappear forever when you close this window.</p>
            </div>
            
            <button onclick="finishOrder()" class="w-full bg-slate-900 text-white font-bold py-4 rounded-xl hover:bg-slate-800 transition-colors">I have saved the PIN</button>
        </div>
    </div>

    <!-- VISUAL SMART SLICER MODAL -->
    <div id="slicer-modal" class="hidden fixed inset-0 bg-white/95 backdrop-blur-xl z-[200] flex-col">
        <div class="flex items-center justify-between p-4 sm:p-6 border-b border-slate-200 bg-white shadow-sm">
            <div class="flex items-center gap-3">
                <div class="bg-blue-100 text-blue-600 p-2 rounded-lg"><i data-lucide="scissors" class="w-5 h-5"></i></div>
                <div>
                    <h2 class="text-lg sm:text-xl font-bold text-slate-900">Visual Smart Slicer</h2>
                    <p class="text-xs text-slate-500 hidden sm:block">Tap pages to select or deselect.</p>
                </div>
            </div>
            <button onclick="closeSlicer()" class="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors">
                <i data-lucide="x" class="w-6 h-6"></i>
            </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-50">
            <div id="slicer-grid" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6 auto-rows-max">
                <!-- Javascript injects thumbnails here -->
            </div>
        </div>
        
        <div class="border-t border-slate-200 bg-white p-4 sm:p-6 flex flex-col sm:flex-row items-center gap-4">
            <div class="flex-1 w-full relative">
                <label class="absolute -top-2 left-3 bg-white px-1 text-xs font-semibold text-blue-600">Selected Pages</label>
                <input type="text" id="slicer-range-input" onkeyup="syncSlicerGridFromInput()" placeholder="e.g. 1-3, 5, 7" class="w-full border-2 border-slate-200 rounded-xl p-4 font-mono text-slate-800 focus:border-blue-500 focus:ring-0 outline-none transition-colors">
            </div>
            <button onclick="saveSlicerSelection()" class="w-full sm:w-auto bg-blue-600 text-white font-bold py-4 px-8 rounded-xl shadow-lg shadow-blue-500/30 hover:bg-blue-700 active:scale-95 transition-all flex items-center justify-center gap-2 whitespace-nowrap">
                <i data-lucide="check" class="w-5 h-5"></i> Confirm Selection
            </button>
        </div>
    </div>
"""
with open("index.html", "w") as f:
    f.write(html_content)

print("index.html base HTML generated.")
