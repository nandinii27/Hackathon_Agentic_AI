// src/pages/RawMaterialCostManager.jsx
import React from "react";
import EntityManager from "../components/EntityManager";

const RawMaterialCostManager = () => (
  <EntityManager
    title="Raw Material Cost"
    entityName="Raw Material Cost"
    endpoint="/raw_material_costs"
    idField="product_id"
    uniqueIdentifierFields={["product_id", "supplier_id", "effective_date"]}
    formFields={[
      {
        name: "product_id",
        label: "Product ID",
        type: "text",
        placeholder: "e.g., PRD001",
        required: true,
      },
      {
        name: "supplier_id",
        label: "Supplier ID",
        type: "text",
        placeholder: "e.g., SUP001",
        required: true,
      },
      {
        name: "cost_per_unit",
        label: "Cost Per Unit",
        type: "number",
        placeholder: "e.g., 10.50",
        required: true,
      },
      {
        name: "currency",
        label: "Currency",
        type: "text",
        placeholder: "e.g., USD",
        defaultValue: "USD",
      },
      {
        name: "effective_date",
        label: "Effective Date",
        type: "date",
        required: true,
      },
    ]}
    displayFields={[
      { key: "product_id", label: "Product ID" },
      { key: "supplier_id", label: "Supplier ID" },
      {
        key: "cost_per_unit",
        label: "Cost/Unit",
        format: (val) => `$${val.toFixed(2)}`,
      },
      { key: "currency", label: "Currency" },
      {
        key: "effective_date",
        label: "Effective Date",
        format: (val) => new Date(val).toLocaleDateString(),
      },
    ]}
  />
);

export default RawMaterialCostManager;
