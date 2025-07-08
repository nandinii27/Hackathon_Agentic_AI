// src/pages/InventoryManager.jsx
import React from "react";
import EntityManager from "../components/EntityManager";

const InventoryManager = () => (
  <EntityManager
    title="Inventory"
    entityName="Inventory Item"
    endpoint="/inventory"
    idField="product_id"
    uniqueIdentifierFields={["product_id", "location_id"]}
    formFields={[
      {
        name: "product_id",
        label: "Product ID",
        type: "text",
        placeholder: "e.g., PRD003",
        required: true,
      },
      {
        name: "location_id",
        label: "Location ID",
        type: "text",
        placeholder: "e.g., LOC004",
        required: true,
      },
      {
        name: "current_stock",
        label: "Current Stock",
        type: "number",
        placeholder: "e.g., 50",
        required: true,
      },
    ]}
    displayFields={[
      { key: "product_id", label: "Product ID" },
      { key: "location_id", label: "Location ID" },
      { key: "current_stock", label: "Stock" },
      {
        key: "updated_at",
        label: "Last Updated",
        format: (val) => new Date(val).toLocaleString(),
      },
    ]}
  />
);

export default InventoryManager;
