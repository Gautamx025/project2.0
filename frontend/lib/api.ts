export type Language = "en" | "hi" | "mr";
export type Style = "studio" | "shadow" | "lifestyle" | "color";
export type Channel = "shopify" | "woocommerce";
export type Copy = {
  title: string;
  description: string;
  tags: string[];
  bullet_points: string[];
  seo_title: string;
  seo_description: string;
};
export type Stage = {
  key: string;
  name: string;
  description: string;
  status: "pending" | "running" | "completed" | "failed";
  elapsed_ms: number;
  demo: boolean;
  reason: string;
  attempts: number;
};
export type Comparable = {
  title: string;
  url: string;
  price: number;
  demo: boolean;
};
export type Listing = {
  id: string;
  sku: string;
  category: string;
  material: string;
  color: string;
  copy: Copy;
  translations: Record<Language, Copy>;
  language: Language;
  price: {
    low: number;
    median: number;
    high: number;
    sources: Comparable[];
    cached: boolean;
  };
  final_price: number;
  variants: Record<Style, string>;
  variant_provenance: Record<
    Style,
    { demo: boolean; reason: string; provider: string }
  >;
  selected_style: Style;
  source_images: string[];
  demo_data: boolean;
  approved: boolean;
};
export type Job = {
  id: string;
  status:
    "queued" | "processing" | "ready" | "published" | "failed" | "cancelled";
  revision: number;
  created_at: number;
  updated_at: number;
  source_images: string[];
  sample_key: string;
  elapsed_ms: number;
  publish_elapsed_ms?: number;
  demo_data: boolean;
  queue: string;
  queue_warning: string;
  stages: Stage[];
  error: string;
  result: Listing | null;
  store_result: {
    id: string;
    url: string;
    channel: Channel;
    demo: boolean;
    status: string;
    message: string;
    price_synced: boolean;
  } | null;
};
export type AppSettings = {
  settings_readonly?: boolean;
  demo_mode: boolean;
  vision_provider: string;
  price_provider: string;
  segmentation_provider: string;
  background_provider: string;
  gemini_model: string;
  shopify_domain: string;
  woocommerce_url: string;
  configured: Record<string, boolean>;
};
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  if (init?.body instanceof FormData) {
    // Keep multi-photo uploads below the cloud request limit; small fixtures
    // retain their original bytes and content-hash recognition.
    const prepared = new FormData();
    for (const [key, value] of init.body.entries()) {
      prepared.append(key, value instanceof File ? await uploadPhoto(value) : value);
    }
    init = { ...init, body: prepared };
  }
  const response = await fetch("/api" + path, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = "The request could not finish. Try again.";
    try {
      const body = await response.json();
      detail =
        typeof body.detail === "string"
          ? body.detail
          : "Please check the required fields and photo format.";
    } catch {}
    throw new Error(detail);
  }
  return response.json();
}

async function uploadPhoto(file: File): Promise<File> {
  if (file.size <= 900_000 || !file.type.startsWith("image/")) return file;
  const bitmap = await createImageBitmap(file);
  try {
    const canvas = document.createElement("canvas");
    const scale = Math.min(1, 1400 / Math.max(bitmap.width, bitmap.height));
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Could not prepare this photo. Try another image.");
    context.fillStyle = "white";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    for (const quality of [0.85, 0.65, 0.45, 0.25]) {
      const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
      if (blob && blob.size <= 900_000) return new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg", { type: "image/jpeg" });
    }
    throw new Error("This photo could not be reduced for upload. Choose a smaller photo.");
  } finally {
    bitmap.close();
  }
}
export const money = (value: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(value);
export const seconds = (ms: number) => (ms / 1000).toFixed(2) + " s";
export const styles: { key: Style; label: string; note: string }[] = [
  { key: "studio", label: "White studio", note: "A clean catalog essential" },
  {
    key: "shadow",
    label: "Soft shadow",
    note: "Stone, light & a little depth",
  },
  { key: "lifestyle", label: "Lifestyle", note: "A place in the everyday" },
  { key: "color", label: "Colored paper", note: "A warm terracotta backdrop" },
];
export const samples = [
  {
    key: "bottle",
    name: "Steel bottle",
    category: "DRINKWARE",
    alt: "White steel water bottle with a silver cap",
  },
  {
    key: "watch",
    name: "Digital watch",
    category: "ACCESSORIES",
    alt: "White-band digital watch on a light surface",
  },
  {
    key: "bag",
    name: "Everyday backpack",
    category: "CARRY GOODS",
    alt: "Brown leather backpack with a front pocket",
  },
];
export const stageLabels = [
  "Photo ingestion",
  "Foreground isolation",
  "Studio background",
  "Product copy",
  "Market pricing",
  "Draft assembly",
];
