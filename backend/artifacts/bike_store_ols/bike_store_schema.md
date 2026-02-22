# Database Dictionary — uploads/bike_store.db

## Table: brands

| Column | Type |
|--------|------|
| brand_id | INTEGER |
| brand_name | TEXT |

**Primary Key:** brand_id


---

## Table: categories

| Column | Type |
|--------|------|
| category_id | INTEGER |
| category_name | TEXT |

**Primary Key:** category_id


---

## Table: customers

| Column | Type |
|--------|------|
| customer_id | INTEGER |
| first_name | TEXT |
| last_name | TEXT |
| phone | TEXT |
| email | TEXT |
| street | TEXT |
| city | TEXT |
| state | TEXT |
| zip_code | TEXT |

**Primary Key:** customer_id


---

## Table: order_items

| Column | Type |
|--------|------|
| order_id | INTEGER |
| item_id | INTEGER |
| product_id | INTEGER |
| quantity | INTEGER |
| list_price | REAL |
| discount | REAL |

**Primary Key:** order_id, item_id

**Foreign Keys:**
- ['order_id'] → orders(['order_id'])
- ['product_id'] → products(['product_id'])

---

## Table: orders

| Column | Type |
|--------|------|
| order_id | INTEGER |
| customer_id | INTEGER |
| order_status | INTEGER |
| order_date | TEXT |
| required_date | TEXT |
| shipped_date | TEXT |
| store_id | INTEGER |
| staff_id | INTEGER |

**Primary Key:** order_id

**Foreign Keys:**
- ['customer_id'] → customers(['customer_id'])
- ['store_id'] → stores(['store_id'])
- ['staff_id'] → staffs(['staff_id'])

---

## Table: products

| Column | Type |
|--------|------|
| product_id | INTEGER |
| product_name | TEXT |
| brand_id | INTEGER |
| category_id | INTEGER |
| model_year | INTEGER |
| list_price | REAL |

**Primary Key:** product_id

**Foreign Keys:**
- ['brand_id'] → brands(['brand_id'])
- ['category_id'] → categories(['category_id'])

---

## Table: staffs

| Column | Type |
|--------|------|
| staff_id | INTEGER |
| first_name | TEXT |
| last_name | TEXT |
| email | TEXT |
| phone | TEXT |
| active | INTEGER |
| store_id | INTEGER |
| manager_id | INTEGER |

**Primary Key:** staff_id

**Foreign Keys:**
- ['store_id'] → stores(['store_id'])
- ['manager_id'] → staffs(['staff_id'])

---

## Table: stocks

| Column | Type |
|--------|------|
| store_id | INTEGER |
| product_id | INTEGER |
| quantity | INTEGER |

**Primary Key:** store_id, product_id

**Foreign Keys:**
- ['store_id'] → stores(['store_id'])
- ['product_id'] → products(['product_id'])

---

## Table: stores

| Column | Type |
|--------|------|
| store_id | INTEGER |
| store_name | TEXT |
| phone | TEXT |
| email | TEXT |
| street | TEXT |
| city | TEXT |
| state | TEXT |
| zip_code | TEXT |

**Primary Key:** store_id


---
