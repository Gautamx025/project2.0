# Provider contracts

Official documentation checked 2026-10-17. These are documented contracts, not live authenticated API verification. Keys, paid credits, account access, public media hosting and store permissions still need validation in the deployment account. Keep model IDs and API versions configurable.

## fal.ai: preferred SAM + FLUX path

Use `fal_client.run_async(model_id, arguments=body)` or HTTP `POST https://fal.run/{model_id}` with `Authorization: Key <FAL_KEY>` and JSON. The direct call blocks; the subscribe client submits and polls a queue. Both image models accept a public HTTPS image URL or a Base64 data URI.

SAM model: `fal-ai/sam2/image`.

```json
{"image_url":"data:image/jpeg;base64,...","prompts":[{"x":400,"y":400,"label":1}],"apply_mask":true,"output_format":"png"}
```

Coordinates are pixels in the submitted image. Foreground label is `1`; background label is `0`. Supply the resized image dimensions when choosing a center point. Read `response.image.url`; this endpoint does **not** return `mask_urls`.

FLUX editing model: `fal-ai/flux-pro/kontext`.

```json
{"image_url":"data:image/png;base64,...","prompt":"Keep the product unchanged. Replace only its background with a warm white studio and soft shadow.","num_images":1,"output_format":"png","aspect_ratio":"1:1"}
```

Read `response.images[0].url`. Generate each requested style separately; multiple images alone do not guarantee distinct styles. Download provider outputs to application storage.

Sources: [SAM schema](https://fal.ai/models/fal-ai/sam2/image/api), [FLUX schema](https://fal.ai/models/fal-ai/flux-pro/kontext/api), [inference methods](https://fal.ai/docs/documentation/model-apis/inference/synchronous).

## Replicate alternative

`POST https://api.replicate.com/v1/predictions`, Bearer authentication, JSON `{"version":"MODEL_OR_FULL_VERSION","input":{...}}`. Optional `Prefer: wait=30`; poll returned `urls.get` until `status` is `succeeded`, `failed` or `canceled`. Do not treat `starting`/`processing` as complete. API outputs expire by default, so persist files.

Official FLUX model `black-forest-labs/flux-kontext-pro` accepts `input_image` (not fal's `image_url`), `prompt`, `aspect_ratio:"match_input_image"`, `output_format:"png"`; the HTTP prediction `output` is a URL string. Official models can be addressed without a version hash.

Community SAM 2 requires a full version. Published latest version observed:

```text
meta/sam-2:fe97b453a6455861e3bac769b441ca1f1086110da7466dbb65cf1eecfd60dc83
```

Input `{"image":"data:image/jpeg;base64,...","mask_limit":12}`. Output is `{"combined_mask":"URL","individual_masks":["URL",...]}`. The combined image is a colored diagnostic overlay, **not** a transparent cutout. Individual masks are black/white and sorted largest first; select a suitable centered foreground mask and apply it to the original with Pillow. The largest mask may be background. Do not claim automatic product selection is infallible.

Sources: [HTTP contracts and version rules](https://replicate.com/docs/reference/http), [SAM versions](https://replicate.com/meta/sam-2/versions), [SAM predictor source](https://raw.githubusercontent.com/zsxkib/segment-anything-2/main/predict.py), [FLUX model](https://replicate.com/black-forest-labs/flux-kontext-pro).

## Vision: Gemini primary, GPT-4o selectable

**Gemini 1.5 Flash was shut down September 29, 2025.** Keeping it as the default would make every real call fall back. Keep the provider Gemini and document the replacement in DECISIONS.md. Current official guidance recommends `gemini-3.8-flash` for new projects; `gemini-2.5-flash` is restricted to previous users.

REST: `POST https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent`, header `x-goog-api-key`.

```json
{
  "contents":[{"parts":[{"text":"Read this product photo. Return only supported observations using the supplied schema."},{"inlineData":{"mimeType":"image/jpeg","data":"BASE64_WITHOUT_DATA_PREFIX"}}]}],
  "generationConfig":{"responseFormat":{"text":{"mimeType":"application/json","schema":{"type":"object","properties":{"title":{"type":"string"},"tags":{"type":"array","items":{"type":"string"}}},"required":["title","tags"],"additionalProperties":false}}}}
}
```

Read and concatenate `candidates[0].content.parts[].text`, parse JSON, then validate against Pydantic. Use the app's full metadata schema, not the abbreviated example. `responseMimeType`/`responseSchema` are older deprecated fields; current docs use `responseFormat`. Structured JSON still needs semantic validation and refusal/blocked-response handling.

Sources: [shutdown release notes](https://ai.google.dev/gemini-api/docs/changelog?release=09-18-2026), [current model guidance](https://ai.google.dev/gemini-api/docs/deprecations), [structured JSON](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), [GenerateContent reference](https://ai.google.dev/api/generate-content).

GPT-4o REST: `POST https://api.openai.com/v1/chat/completions`, Bearer key. Keep the requested model `gpt-4o` (configurable; do not silently substitute a newer family).

```json
{
  "model":"gpt-4o",
  "messages":[{"role":"user","content":[{"type":"text","text":"Extract product metadata."},{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,..."}}]}],
  "response_format":{"type":"json_schema","json_schema":{"name":"product_metadata","strict":true,"schema":{"type":"object","properties":{"title":{"type":"string"}},"required":["title"],"additionalProperties":false}}}
}
```

Use the full app schema. All object properties must be in `required`; every object must set `additionalProperties:false`. Parse `choices[0].message.content`; handle `message.refusal` and incomplete output before validation. Strict output is supported by GPT-4o August 2024 snapshots and later.

Sources: [official OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat), [official OpenAI vision inputs](https://developers.openai.com/api/docs/guides/images-vision).

## Price research

Tavily: `POST https://api.tavily.com/search`, `Authorization: Bearer <TAVILY_API_KEY>`.

```json
{"query":"stainless steel bottle 750 ml price INR India","topic":"general","search_depth":"basic","max_results":5,"include_answer":false,"include_raw_content":false,"country":"india"}
```

Read `results[].title`, `.url`, `.content`, `.score`. Tavily returns search text, **not** guaranteed structured prices. Extract only explicit currency-qualified prices, attach each observed price to its actual result URL, exclude different currencies and unrealistic outliers, then compute low/median/high. No usable prices is a visible fallback reason; never invent live comparables.

SerpAPI: `GET https://serpapi.com/search.json` with `engine=google_shopping`, `q`, `api_key`, `gl=in`, `hl=en`. Read `shopping_results[].title`, `.source`, `.price`, `.extracted_price`; URL may be `product_link` rather than legacy `link`. Check provider `error` even on HTTP 200. `extracted_price` is numeric, but still check locale/currency.

Sources: [Tavily Search](https://docs.tavily.com/documentation/api-reference/endpoint/search), [SerpAPI Google Shopping](https://serpapi.com/google-shopping-api).

## Shopify draft + price + media

Current stable API documented as `2026-10`: `POST https://{shop}.myshopify.com/admin/api/2026-10/graphql.json`, header `X-Shopify-Access-Token`. Product write access is required. Test read access with `query { shop { name myshopifyDomain } }`.

```graphql
mutation CreateDraft($product: ProductCreateInput!, $media: [CreateMediaInput!]) {
  productCreate(product: $product, media: $media) {
    product { id title status variants(first:1) { nodes { id } } }
    userErrors { field message }
  }
}
```

```json
{"product":{"title":"Steel water bottle, 750 ml","descriptionHtml":"<p>Product description</p>","status":"DRAFT","tags":["bottle"],"productType":"Drinkware","seo":{"title":"Steel water bottle","description":"SEO description"}},"media":[{"originalSource":"https://PUBLIC_HOST/image.png","mediaContentType":"IMAGE","alt":"Steel water bottle"}]}
```

`productCreate` creates an initial variant; price is not a product-level field. Use its returned product and variant IDs for a second mutation:

```graphql
mutation SetPrice($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId:$productId, variants:$variants) {
    productVariants { id price }
    userErrors { field message }
  }
}
```

Variables: `{"productId":"gid://shopify/Product/123","variants":[{"id":"gid://shopify/ProductVariant/456","price":"799.00","inventoryItem":{"sku":"S2S-001"}}]}`.

Check top-level `errors` and mutation `userErrors`. Preserve the created draft ID if price update fails so retry does not create duplicates. Media must be publicly accessible; local `/media/...`, localhost and private file paths do not work. Never report an image was synced if it was omitted. Keep status DRAFT; do not call publishablePublish.

Sources: [productCreate and media](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productCreate), [variant mutation](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productVariantsBulkUpdate), [variant price input](https://shopify.dev/docs/api/admin-graphql/latest/input-objects/ProductVariantsBulkInput).

## WooCommerce draft

`POST https://{site}/wp-json/wc/v3/products`, HTTPS Basic authentication with consumer key as username and secret as password.

```json
{"name":"Steel water bottle, 750 ml","type":"simple","status":"draft","regular_price":"799.00","sku":"S2S-001","description":"<p>Product description</p>","short_description":"Steel bottle.","images":[{"src":"https://PUBLIC_HOST/image.png","alt":"Steel water bottle"}]}
```

Expect HTTP 201 and a product object containing `id`, `status`, `permalink`. Always send `status:"draft"`: WooCommerce's default is publish. `regular_price` is a decimal string; `price` is read-only. `tags` expects existing term IDs, not raw tag strings. SEO fields require the relevant WordPress SEO plugin integration; core WooCommerce does not define portable SEO fields. Test credentials with `GET /wp-json/wc/v3/products?per_page=1`. Validate reachability and HTTPS before sending credentials.

Sources: [WooCommerce products](https://developer.woocommerce.com/docs/apis/rest-api/v3/products/), [authentication](https://developer.woocommerce.com/docs/apis/rest-api/authentication/).
