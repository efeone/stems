# STEMS User Manual

STEMS (Service & Trading Enterprise Management System) is designed to manage the end-to-end workflow from lead generation to project completion and invoicing.

---

## 1. Lead Management

### Lead Creation
To start, open **Lead** and enter the customer details such as Name, Phone Number, Email, etc. Save the Lead once the details are entered.

After saving, the Lead page will display:
*   **Sales Person**: The assigned sales employee.
*   **Owner**: The user who created the lead.
*   **Activity Section**: Used to add To-Do items, Events, or log communications related to the customer.

### Creating an Enquiry
To proceed, create an **Enquiry (Opportunity)** directly from the Lead:
1.  Open the required Lead.
2.  Click on **Create > Enquiry**.

---

## 2. Enquiry (Opportunity)

When the Enquiry opens, most customer information is automatically fetched from the Lead.

### Key Options:
*   **Drawing Required**: If selected, a **Sketch** table appears where drawing descriptions and files can be added.
*   **Site Visit Required**: If selected, you must:
    1.  Select the **Site Visit Date**.
    2.  Select the **Site Engineer/Supervisor** (must have the *Site Engineer* role).

### Automated Actions:
*   Upon saving an Enquiry with a scheduled site visit, the system automatically creates a **To-Do** and an **Event** for the assigned engineer.
*   From the Enquiry, you can create related records such as **Customer**, **BOQ**, and **Customer Need Profile (CNP)** using the **Create** button.

---

## 3. Customer Need Profile (CNP)

The CNP captures detailed requirements before finalizing a quote.

### Features:
*   **Auto-fetch**: Details like site location and contact info are fetched from the Enquiry.
*   **Billing Type**:
    *   *Service Only*: The "Customer Provided" checkbox for stock items will be automatically selected.
    *   *Items and Service*: Standard billing for both goods and labor.
*   **Item Table**: Enter the Item Name, Quantity, and Description. Use the **Customer Provided** checkbox to indicate if the item is not being supplied by us.
*   **Drawing Details**: A dedicated section for drawing attachments, preparer details, and remarks.

After submitting the CNP, use the **Create > Bill of Quantity** button to proceed.

---

## 4. Bill of Quantity (BOQ)

The BOQ serves as the master document for project material and service planning.

### Stock Planning & Tracking:
In the Item table, three fields help track stock:
*   **Stock Balance**: Current available stock in the item's default warehouse.
*   **Additional Quantity Needed**: Calculated as `(Qty - Transferred Qty) - Stock Balance`.
*   **Transferred Quantity**: Quantity already moved to the project warehouse.

### Actions:
*   **Request for Quotation (RFQ)**: If there is a stock shortage (**Additional Quantity Needed > 0**), a button to create an **RFQ** appears under the **Create** menu.
*   **Stock Transfer**: Once a Project is linked, use the **Transfer Stock to Project** button to create a **Stock Entry (Material Transfer)** to move items to the project warehouse.
*   **Create Quotation**: Use the **Create > Quotation** button to generate a quote for the customer.

---

## 5. Quotation

Quotations are mapped from the BOQ.

*   **Item Mapping**: Items marked as "Customer Provided" in the BOQ are moved to the **Required Items** table, while billable items remain in the main **Items** table.
*   **Workflow**: Once the Quotation is reviewed, it is shared with the customer. The Quotation must reach the **Customer Approved** state before a Sales Order can be created.

---

## 6. Sales Order and Project Creation

### Delivery Date Calculation:
When an item with a linked **Task Template** is selected, the system calculates the delivery time based on the total hours defined in the template. The **Delivery Date** is then automatically set based on the latest calculated task completion time.

### Project & Team Assignment:
*   **Employee Group**: Selecting an Employee Group in the Sales Order assigns the resulting Project to that specific team.
*   **Project Name**: Can be entered manually. If left blank, the system generates one automatically (e.g., `PROJ-CUSTOMER-0001`).

### Automation on Submission:
Upon submitting the Sales Order:
1.  A **Project** is automatically created.
2.  **Tasks** are generated based on the Item's **Task Templates**.
3.  The Project is automatically assigned to the users in the selected Employee Group.

---

## 7. Percentage-Based Invoicing

STEMS supports flexible, partial invoicing through the **Enable Percentage-Based Invoicing** feature.

### How it Works:
1.  Check **Enable Percentage-Based Invoicing** in the Sales Order (this remains editable after submission).
2.  Click the **Create > Sales Invoice** button. A popup dialog will appear.
3.  **Filters**: You can filter the items by *All*, *Stock*, or *Service*.
4.  **Invoicing Logic**:
    *   **Stock Items**: Billing is primarily based on **Quantity**. If the UOM requires whole numbers, the rate may be adjusted to match the target percentage.
    *   **Service Items**: Billing is primarily based on **Rate** adjustment.
5.  **Tracking**: After invoicing, the Sales Order updates the **Remaining Percentage** available to bill. The system prevents billing more than 100% of any item.

---

## 8. Task Progress and Payments

### Task-Wise Payment:
In the **Task** master:
*   **Payment Required**: Check this to mark a task as billable.
*   **Payment Percentage**: Define what percentage of the Sales Order value is triggered upon task completion.

### Integration with Sales Order:
When a billable task is marked as **Completed**:
1.  A notification is sent to the configured accounting/finance roles.
2.  The task is automatically added to the **Task Wise Pay** table in the linked Sales Order, calculating the amount due.

### Project Dashboard:
The **Project** view includes a progress card displaying the overall completion percentage of all project tasks.

---

## 9. Delivery Note

### Automated Warehouse Selection:
When a **Delivery Note** is created for a Project:
*   The system automatically sets the **Source Warehouse** to the *Default Project Warehouse* configured in **STEMS Settings**.
*   This ensures items are deducted from the correct project-specific stock location.

---

## 10. Automated Notifications

The system includes several automated alerts:
*   **Quotation Follow-up**: Sends a notification to the Sales Person if a Quotation remains in "Draft" beyond a set number of days.
*   **Quotation Approval**: Sends an email with a PDF attachment to the Customer/Lead when the Quotation is ready for approval.
*   **Payment Task Alert**: Notifies relevant roles when a payment-triggering task is completed.
