# Database Dictionary — bike_store.db

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


---

# AI-Generated Table Summaries

## brands

This table stores a comprehensive list of all distinct brands managed within the system. Its primary purpose is to provide a central reference for brand information, ensuring consistency and accuracy when associating products, sales, or other data points with a specific brand.

### Column Descriptions

- **brand_id**: A unique numerical identifier for each brand, serving as the primary key for this table.
- **brand_name**: The official and descriptive name of the brand.

### Data Quality Notes
All columns are fully complete with no missing values, indicating high data integrity for brand identification and naming.

---

## categories

This table stores a definitive list of categories used across the business. Its purpose is to provide a standardized classification system for various items or services, ensuring consistency and ease of grouping.

### Column Descriptions

- **category_id**: A unique numerical identifier for each specific category.
- **category_name**: The clear, human-readable name or title of the category (e.g., 'Electronics', 'Books', 'Home Goods').

### Data Quality Notes
The table is small, containing 7 distinct categories. Data quality is excellent, as all columns are fully complete with no missing values.

---

## customers

This table contains comprehensive contact and location details for all registered customers. Its primary purpose is to uniquely identify customers and provide necessary information for communication, order fulfillment, and marketing activities.

### Column Descriptions

- **customer_id**: A unique identifier assigned to each customer.
- **first_name**: The customer's given name.
- **last_name**: The customer's family name.
- **phone**: The customer's primary contact phone number.
- **email**: The customer's primary contact email address.
- **street**: The street address of the customer.
- **city**: The city of the customer's address.
- **state**: The state or province of the customer's address.
- **zip_code**: The postal code of the customer's address.

### Data Quality Notes
The 'phone' column has missing values for some customer records, indicating that not all customers have a phone number on file.

---

## order_items

This table represents individual items within a customer order. Each row captures details about a specific product ordered, including its quantity, list price, and any applied discounts. Its business purpose is to provide granular insight into the contents of each order, facilitating analysis of product sales, pricing strategies, and discount effectiveness.

### Column Descriptions

- **order_id**: A unique identifier for the main customer order to which this item belongs.
- **item_id**: A unique identifier for this specific item line within its respective order.
- **product_id**: A unique identifier for the product that was ordered.
- **quantity**: The number of units of the product included in this specific order item.
- **list_price**: The original price of a single unit of the product at the time it was ordered, before any discounts.
- **discount**: The discount amount or percentage applied to this specific item line in the order.

### Relationships
This table is related to the 'orders' table via 'order_id', linking each item to its overall order. It also relates to the 'products' table via 'product_id', providing details about the specific product ordered.

### Data Quality Notes
All columns in this table are fully complete, with no missing values. The table currently contains 4722 rows.

---

## orders

This table records all customer orders, detailing when an order was placed, its current status, and key dates throughout its lifecycle. It serves as a central point for tracking and managing the fulfillment of customer requests.

### Column Descriptions

- **order_id**: A unique identifier for each individual order.
- **customer_id**: Identifies the customer who placed this specific order.
- **order_status**: Indicates the current status of the order (e.g., pending, completed, cancelled).
- **order_date**: The date when the order was originally placed.
- **required_date**: The date by which the order is expected to be fulfilled or shipped.
- **shipped_date**: The actual date when the order was shipped to the customer.
- **store_id**: Identifies the store location where the order was placed.
- **staff_id**: Identifies the staff member who processed or is responsible for this order.

### Relationships
This table links to the 'customers' table via 'customer_id' to retrieve customer details, to the 'stores' table via 'store_id' for store information, and to the 'staffs' table via 'staff_id' to identify staff members.

### Data Quality Notes
The table contains 1615 orders. The 'shipped_date' column has missing values, suggesting that not all orders have been shipped yet or the shipping date information is incomplete for some records.

---

## products

This table stores detailed information about individual products offered. Its primary business purpose is to catalog each product, providing essential attributes like its name, brand, category, model year, and standard retail price.

### Column Descriptions

- **product_id**: A unique identifier for each distinct product.
- **product_name**: The full name or title of the product.
- **brand_id**: An identifier linking the product to its specific brand. This allows for retrieving full brand details from the 'brands' table.
- **category_id**: An identifier linking the product to its specific category. This allows for retrieving full category details from the 'categories' table.
- **model_year**: The manufacturing or release year of the product's model.
- **list_price**: The standard retail or recommended list price for the product.

### Relationships
This table links to the 'brands' table via 'brand_id' to provide details about the product's brand, and to the 'categories' table via 'category_id' to provide details about the product's category.

### Data Quality Notes
The table is highly complete, with no null values observed across any column, indicating robust data entry and integrity. It contains 321 product records.

---

## staffs

This table stores comprehensive information about individual staff members within the organization. Its purpose is to manage employee details, track their active status, and define their association with specific stores and their reporting structure.

### Column Descriptions

- **staff_id**: A unique identifier for each staff member.
- **first_name**: The first name of the staff member.
- **last_name**: The last name or surname of the staff member.
- **email**: The primary email address for contacting the staff member.
- **phone**: The primary phone number for contacting the staff member.
- **active**: Indicates if the staff member is currently active (e.g., 1 for active, 0 for inactive).
- **store_id**: The unique identifier of the store where the staff member is employed.
- **manager_id**: The unique identifier of the staff member's direct manager. This manager is also a staff member listed in this table.

### Relationships
Each staff member is linked to a specific store via the 'store_id' column, connecting to the 'stores' table. Additionally, staff members can report to a manager, where the 'manager_id' column refers back to another staff member's 'staff_id' within this same table, establishing a hierarchical reporting structure.

### Data Quality Notes
All columns in this table are fully complete with no missing values, indicating high data completeness for all recorded staff member attributes.

---

## stocks

This table records the current inventory levels for specific products at each individual store. It details how many units of a particular product are available in a given store, which is crucial for inventory management, tracking product availability, and fulfilling customer orders.

### Column Descriptions

- **store_id**: A unique identifier for the specific retail store where the product is currently stocked.
- **product_id**: A unique identifier for the product whose stock level is being recorded.
- **quantity**: The current number of units of a specific product available in the identified store.

### Relationships
This table links to the 'stores' table via the 'store_id' to provide detailed information about each store, and to the 'products' table via the 'product_id' to provide details about each product.

### Data Quality Notes
The table contains 939 records. All columns (store_id, product_id, quantity) are fully complete with no missing values, indicating a robust and clean dataset for current stock levels.

---

## stores

This table stores essential information for each business location or store. It provides key details such as the store's name, contact information (phone, email), and full physical address. Its primary business purpose is to uniquely identify and manage store-specific attributes.

### Column Descriptions

- **store_id**: A unique numerical identifier for each individual store.
- **store_name**: The official or registered name of the store.
- **phone**: The primary contact phone number for the store.
- **email**: The primary contact email address for the store.
- **street**: The street address component of the store's location.
- **city**: The city where the store is located.
- **state**: The state or province where the store is located.
- **zip_code**: The postal code for the store's location.

### Data Quality Notes
All columns are fully complete with no missing values. The table currently contains only 3 records, which might indicate a small dataset or a staging/test environment.

---
