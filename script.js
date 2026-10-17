// ====================================================================
// 🔑 PUT YOUR API KEY HERE FOR LIVE BACKEND/API CALLS
// ====================================================================
const API_CONFIG = {
  AI_MODEL_API_KEY: "YOUR_API_KEY_HERE"  // Replace with your Gemini / OpenAI / Search API key
};

// App State Management
let currentImageSrc = null;
let currentKey = null;
let isProcessing = false;
let generatedData = null;

// Sample Datasets in Rupees (INR)
const SAMPLE_DATA = {
  watch: {
    rawImg: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80",
    synthImg: "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=800&auto=format&fit=crop&q=80",
    title: "Minimalist Executive Quartz Wristwatch",
    category: "Watches & Accessories / Analog",
    price: "₹2,929 - ₹3,995 (Market Avg: ₹3,450)",
    price_num: 3450,
    description: "Crafted for timeless elegance, this minimalist quartz wristwatch features a polished stainless steel casing and an ultra-durable dial. Designed for everyday sophistication and waterproof performance.",
    tags: ["Wristwatch", "Luxury", "Minimalist", "Quartz", "Waterproof"]
  },
  shoe: {
    rawImg: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80",
    synthImg: "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=800&auto=format&fit=crop&q=80",
    title: "Performance Lightweight Running Sneakers",
    category: "Footwear / Athletic Sneakers",
    price: "₹1,599 - ₹2,499 (Market Avg: ₹1,999)",
    price_num: 1999,
    description: "Engineered with responsive cushioned soles and breathable mesh uppers, these athletic running sneakers deliver high-traction grip and ergonomic comfort for daily wear.",
    tags: ["Running Shoes", "Athletic", "Sneakers", "Lightweight", "Breathable"]
  }
};

// DOM Elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const rawPreview = document.getElementById('rawPreview');
const dropzoneContent = document.getElementById('dropzoneContent');
const processBtn = document.getElementById('processBtn');
const stageLoader = document.getElementById('stageLoader');
const loaderText = document.getElementById('loaderText');
const emptyStage = document.getElementById('emptyStage');
const synthesizedImage = document.getElementById('synthesizedImage');
const stageContainer = document.getElementById('stageContainer');
const statusBadge = document.getElementById('statusBadge');
const publishBtn = document.getElementById('publishBtn');

// Drag and Drop Handling
dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('border-blue-500'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('border-blue-500'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('border-blue-500');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', (e) => {
  if (e.target.files.length) handleFile(e.target.files[0]);
});

function handleFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    currentImageSrc = e.target.result;
    currentKey = 'custom';
    setRawImage(currentImageSrc);
  };
  reader.readAsDataURL(file);
}

function loadSample(key, event) {
  if(event) event.stopPropagation();
  const sample = SAMPLE_DATA[key];
  currentImageSrc = sample.synthImg;
  currentKey = key;
  setRawImage(sample.rawImg);
}

function setRawImage(src) {
  rawPreview.src = src;
  rawPreview.classList.remove('hidden');
  dropzoneContent.classList.add('hidden');
  processBtn.disabled = false;
  statusBadge.innerText = 'Photo Ready';
  statusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium';
}

// Advanced Canvas Engine: Simulates SAM background isolation & Diffusion studio lighting
async function generateStudioProcessedImage(imgSrc) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.src = imgSrc;
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = 800;
      canvas.height = 800;

      // 1. Draw Professional Commercial Studio Gradient Background (Diffusion Light Simulation)
      const grad = ctx.createRadialGradient(400, 400, 50, 400, 400, 500);
      grad.addColorStop(0, '#ffffff');
      grad.addColorStop(0.5, '#f8fafc');
      grad.addColorStop(1, '#cbd5e1');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 800, 800);

      // 2. Add Realistic Soft Studio Floor Shadow for Authentic Depth
      ctx.save();
      ctx.beginPath();
      ctx.ellipse(400, 710, 220, 35, 0, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(15, 23, 42, 0.25)';
      ctx.filter = 'blur(15px)';
      ctx.fill();
      ctx.restore();

      // 3. Draw and Center Product Foreground
      const scale = Math.min(560 / img.width, 560 / img.height);
      const w = img.width * scale;
      const h = img.height * scale;
      const x = (800 - w) / 2;
      const y = (800 - h) / 2 - 20;

      // Draw subtle product shadow
      ctx.save();
      ctx.shadowColor = 'rgba(0, 0, 0, 0.35)';
      ctx.shadowBlur = 30;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 15;
      ctx.drawImage(img, x, y, w, h);
      ctx.restore();

      resolve(canvas.toDataURL('image/png'));
    };
  });
}

// Pipeline Execution Handler with Automated Studio Background & Lighting Processing
processBtn.addEventListener('click', async () => {
  if (isProcessing) return;
  isProcessing = true;
  processBtn.disabled = true;
  emptyStage.classList.add('hidden');
  stageLoader.classList.remove('hidden');

  // Step 1: SAM Isolation Simulation
  setStepActive('step-sam', 'SAM Isolating Foreground...');
  await sleep(700);

  // Step 2: Diffusion Background & Studio Lighting Synthesis
  setStepActive('step-flux', 'Synthesizing Studio Lighting & Background...');
  let finalImgSrc = '';
  if (currentKey && SAMPLE_DATA[currentKey]) {
    finalImgSrc = SAMPLE_DATA[currentKey].synthImg;
  } else {
    // Dynamically process custom uploaded image with studio background & lighting simulation
    finalImgSrc = await generateStudioProcessedImage(currentImageSrc);
  }
  await sleep(900);

  // Step 3: Vision LLM Metadata Analysis
  setStepActive('step-llm', 'Vision LLM Extracting SEO Metadata...');
  await sleep(800);

  // Step 4: Price Search API (INR)
  setStepActive('step-price', 'Benchmarking Market Price in INR (₹)...');
  await sleep(600);

  // Load results
  stageLoader.classList.add('hidden');
  
  let title = '';
  let category = '';
  let priceStr = '';
  let priceNum = 1499;
  let desc = '';
  let tags = [];

  if (currentKey && SAMPLE_DATA[currentKey]) {
    const data = SAMPLE_DATA[currentKey];
    title = data.title;
    category = data.category;
    priceStr = data.price;
    priceNum = data.price_num;
    desc = data.description;
    tags = data.tags;
  } else {
    // Custom Upload Metadata Generation
    title = "Autonomous AI-Enhanced Retail Merchandise";
    category = "General Retail / eCommerce SKU";
    priceStr = "₹1,299 - ₹2,499 (Market Avg: ₹1,850)";
    priceNum = 1850;
    desc = "Cleanly isolated and enhanced with professional studio lighting and soft shadows. Generated autonomously via Snap-2-Store agent pipeline for high conversion rates.";
    tags = ["Studio Enhanced", "Verified SKU", "Trending", "Premium", "D2C Ready"];
  }

  // Apply Studio Backdrop Styling Class to Canvas
  stageContainer.className = "relative studio-backdrop rounded-xl border border-emerald-500/40 h-64 overflow-hidden flex items-center justify-center shadow-2xl transition-all duration-700";
  
  synthesizedImage.src = finalImgSrc;
  synthesizedImage.classList.remove('hidden');

  document.getElementById('metaTitle').value = title;
  document.getElementById('metaCategory').value = category;
  document.getElementById('metaPrice').value = priceStr;
  document.getElementById('metaDescription').value = desc;

  const tagBox = document.getElementById('tagContainer');
  tagBox.innerHTML = tags.map(t => `<span class="bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs px-2.5 py-1 rounded-md">${t}</span>`).join('');

  generatedData = {
    sku: "SKU-S2S-" + Math.floor(100000 + Math.random() * 900000),
    title: title,
    category: category,
    currency: "INR",
    price_range_inr: priceStr,
    suggested_price_inr: priceNum,
    description: desc,
    tags: tags,
    studio_image_url: finalImgSrc,
    pipeline_execution_time: "21.6 seconds",
    agent_status: "DRAFT_READY"
  };

  document.getElementById('jsonPayload').innerText = JSON.stringify(generatedData, null, 2);

  statusBadge.innerText = 'Pipeline Complete (<25s)';
  statusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium';
  
  publishBtn.disabled = false;
  isProcessing = false;
});

function setStepActive(id, text) {
  loaderText.innerText = text;
  document.querySelectorAll('[id^="step-"]').forEach(el => {
    el.className = 'p-2 rounded bg-slate-900 border border-slate-800 text-slate-500';
  });
  document.getElementById(id).className = 'p-2 rounded bg-blue-600/20 border border-blue-500 text-blue-400 font-semibold animate-pulse';
}

function publishListing() {
  const channel = document.querySelector('input[name="channel"]:checked').value;
  alert(`Success! Published draft listing "${generatedData.title}" priced at ₹${generatedData.suggested_price_inr} directly to ${channel.toUpperCase()} backend via GraphQL/REST API.`);
}

function copyPayload() {
  navigator.clipboard.writeText(document.getElementById('jsonPayload').innerText);
  alert('FastAPI payload copied to clipboard.');
}

document.getElementById('resetBtn').addEventListener('click', () => {
  rawPreview.classList.add('hidden');
  dropzoneContent.classList.remove('hidden');
  synthesizedImage.classList.add('hidden');
  emptyStage.classList.remove('hidden');
  stageContainer.className = "relative bg-slate-900 rounded-xl border border-slate-800 h-64 overflow-hidden flex items-center justify-center bg-grid transition-all duration-500";
  processBtn.disabled = true;
  publishBtn.disabled = true;
  currentImageSrc = null;
  currentKey = null;
  document.getElementById('metaTitle').value = '';
  document.getElementById('metaCategory').value = '';
  document.getElementById('metaPrice').value = '';
  document.getElementById('metaDescription').value = '';
  document.getElementById('tagContainer').innerHTML = '<span class="text-xs text-slate-600 italic">Tags will populate after execution...</span>';
  document.getElementById('jsonPayload').innerText = '{\n  "status": "idle",\n  "currency": "INR",\n  "message": "Upload photo to initiate autonomous agent pipeline"\n}';
  statusBadge.innerText = 'Awaiting Input';
  statusBadge.className = 'text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-medium';
});

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}