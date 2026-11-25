# InsightIQ AI — Dataset Inspection & Data Quality Report

> **Generated at:** 2026-11-25 14:30:37  
> **Scanned Directory:** `insightiq-ai\data\raw`  
> **Total Datasets Analyzed:** 4

---

## 1. Executive Summary

> [!IMPORTANT]
> Found **4 dataset(s)** comprising **1,613 total rows** across the directory.
> Identified **1 data quality issue(s)** requiring handling during ETL ingestion.

## 2. Dataset Inventory

| Dataset Name | File Format | File Size | Row Count | Columns | Duplicates (%) | Candidate PK(s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`customers`** | CSV | 7.4 KB | 100 | 5 | 0 (0.0%) | `customer_id`, `email`, `created_at` |
| **`order_items`** | CSV | 18.5 KB | 983 | 5 | 1 (0.1%) | *None* |
| **`orders`** | CSV | 18.4 KB | 500 | 4 | 0 (0.0%) | `order_id` |
| **`products`** | CSV | 1.6 KB | 30 | 5 | 0 (0.0%) | `product_id`, `product_name` |

---

## 3. Detailed Column Profiles

### 3.1 Dataset: `customers`
- **Source Path:** `insightiq-ai\data\raw\customers.csv`
- **Dimensions:** 100 rows × 5 columns
- **Duplicate Rows:** 0 (0.0%)

| Column Name | Raw Dtype | Inferred Type | Null Count | Null % | Unique | PK Candidate? | Sample Values |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `customer_id` | `int64` | `integer` | 0 | 0.0% | 100 | Yes | `1, 2, 3` |
| `name` | `object` | `string` | 0 | 0.0% | 92 | No | `Christopher Brown, Linda Jones, ...` |
| `email` | `object` | `string` | 0 | 0.0% | 100 | Yes | `christopher.brown1@example.com, ...` |
| `city` | `object` | `string` | 0 | 0.0% | 16 | No | `New York, Seattle, Los Angeles` |
| `created_at` | `object` | `datetime` | 0 | 0.0% | 100 | Yes | `2023-10-19 16:00:00, 2023-07-24 ...` |

**Numeric Distribution & Validation:**

| Numeric Column | Min | Max | Mean | Negative Count | Non-Positive (<=0) Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `customer_id` | 1.0 | 100.0 | 50.5 | 0 | 0 |

**Temporal Analysis & Formatting:**

| Date Column | Earliest Date | Latest Date | Unparseable Count | Format Style |
| :--- | :---: | :---: | :---: | :---: |
| `created_at` | `2023-06-03 08:00:00` | `2024-03-24 04:00:00` | 0 | ISO/Standard |

### 3.2 Dataset: `order_items`
- **Source Path:** `insightiq-ai\data\raw\order_items.csv`
- **Dimensions:** 983 rows × 5 columns
- **Duplicate Rows:** 1 (0.1%)

| Column Name | Raw Dtype | Inferred Type | Null Count | Null % | Unique | PK Candidate? | Sample Values |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `item_id` | `int64` | `integer` | 0 | 0.0% | 982 | No | `1, 2, 3` |
| `order_id` | `int64` | `integer` | 0 | 0.0% | 500 | No | `1, 1, 1` |
| `product_id` | `int64` | `integer` | 0 | 0.0% | 30 | No | `23, 9, 5` |
| `quantity` | `int64` | `integer` | 0 | 0.0% | 4 | No | `1, 1, 1` |
| `unit_price` | `float64` | `float` | 0 | 0.0% | 26 | No | `38.0, 59.99, 39.99` |

**Numeric Distribution & Validation:**

| Numeric Column | Min | Max | Mean | Negative Count | Non-Positive (<=0) Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `item_id` | 1.0 | 982.0 | 491.0 | 0 | 0 |
| `order_id` | 1.0 | 500.0 | 250.25 | 0 | 0 |
| `product_id` | 1.0 | 30.0 | 15.87 | 0 | 0 |
| `quantity` | 1.0 | 4.0 | 1.54 | 0 | 0 |
| `unit_price` | 14.99 | 349.99 | 66.21 | 0 | 0 |

**Identified Data Quality Warnings:**

- ⚠️ Found 1 (0.1%) completely duplicate row(s).

### 3.3 Dataset: `orders`
- **Source Path:** `insightiq-ai\data\raw\orders.csv`
- **Dimensions:** 500 rows × 4 columns
- **Duplicate Rows:** 0 (0.0%)

| Column Name | Raw Dtype | Inferred Type | Null Count | Null % | Unique | PK Candidate? | Sample Values |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `order_id` | `int64` | `integer` | 0 | 0.0% | 500 | Yes | `1, 2, 3` |
| `customer_id` | `int64` | `integer` | 0 | 0.0% | 99 | No | `53, 43, 95` |
| `order_date` | `object` | `datetime` | 0 | 0.0% | 499 | No | `2024-01-26 20:11:00, 2024-01-06 ...` |
| `status` | `object` | `string` | 0 | 0.0% | 4 | No | `completed, completed, completed` |

**Numeric Distribution & Validation:**

| Numeric Column | Min | Max | Mean | Negative Count | Non-Positive (<=0) Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `order_id` | 1.0 | 500.0 | 250.5 | 0 | 0 |
| `customer_id` | 1.0 | 100.0 | 52.49 | 0 | 0 |

**Temporal Analysis & Formatting:**

| Date Column | Earliest Date | Latest Date | Unparseable Count | Format Style |
| :--- | :---: | :---: | :---: | :---: |
| `order_date` | `2024-01-01 08:15:00` | `2024-06-28 19:43:00` | 0 | ISO/Standard |

### 3.4 Dataset: `products`
- **Source Path:** `insightiq-ai\data\raw\products.csv`
- **Dimensions:** 30 rows × 5 columns
- **Duplicate Rows:** 0 (0.0%)

| Column Name | Raw Dtype | Inferred Type | Null Count | Null % | Unique | PK Candidate? | Sample Values |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `product_id` | `int64` | `integer` | 0 | 0.0% | 30 | Yes | `1, 2, 3` |
| `product_name` | `object` | `string` | 0 | 0.0% | 30 | Yes | `Noise-Canceling Headphones, Mech...` |
| `category` | `object` | `string` | 0 | 0.0% | 5 | No | `Electronics, Electronics, Electr...` |
| `price` | `float64` | `float` | 0 | 0.0% | 26 | No | `199.99, 89.99, 349.99` |
| `stock` | `int64` | `integer` | 0 | 0.0% | 24 | No | `150, 200, 80` |

**Numeric Distribution & Validation:**

| Numeric Column | Min | Max | Mean | Negative Count | Non-Positive (<=0) Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `product_id` | 1.0 | 30.0 | 15.5 | 0 | 0 |
| `price` | 14.99 | 349.99 | 70.41 | 0 | 0 |
| `stock` | 80.0 | 500.0 | 208.5 | 0 | 0 |

---

## 4. Target Schema Comparison

Comparison against the required InsightIQ AI PostgreSQL database schema:

| Target Table | Status | Matched File | Missing Columns | Extra Columns | PK Present |
| :--- | :---: | :---: | :--- | :--- | :---: |
| `customers` | **MATCHED** | `customers` | *None* | *None* | Yes |
| `products` | **MATCHED** | `products` | *None* | *None* | Yes |
| `orders` | **MATCHED** | `orders` | *None* | *None* | Yes |
| `order_items` | **MATCHED** | `order_items` | *None* | *None* | Yes |

---

## 5. Inferred Foreign Key Relationships

| Origin Table & Column | Target Table & Column | Match Ratio | Referential Status | Notes |
| :--- | :--- | :---: | :---: | :--- |
| `orders.customer_id` | `customers.customer_id` | 100.0% | **VALID FK** | 99/99 distinct foreign keys exist in parent table. |
| `order_items.order_id` | `orders.order_id` | 100.0% | **VALID FK** | 500/500 distinct foreign keys exist in parent table. |
| `order_items.product_id` | `products.product_id` | 100.0% | **VALID FK** | 30/30 distinct foreign keys exist in parent table. |

---

## 6. Recommendations for Data Cleaning & Ingestion (Phase 4)

1. **Deduplication:** Ensure ingestion pipelines implement `ON CONFLICT DO NOTHING` or upsert patterns to drop duplicate rows gracefully.
2. **Whitespace Trimming:** Strip leading/trailing whitespaces across all string fields (e.g. `name`, `city`, `category`, `status`).
3. **Null Handling:** Reject orders or line items lacking valid customer or product foreign keys; log dropped records in an ingestion audit log.
4. **Status Normalization:** Normalize order status strings to lowercase (`completed`, `cancelled`, `pending`, `returned`) to guarantee accurate revenue aggregation.
5. **Numeric Precision:** Enforce `Decimal` / PostgreSQL `NUMERIC(12, 2)` for prices to prevent floating-point rounding errors in AOV and revenue metrics.
