// src/pages/StoreLimitManager.jsx
import React from "react";
import EntityManager from "../components/EntityManager";

const StoreLimitManager = () => (
  <EntityManager
    title="Store Limit"
    entityName="Store Limit"
    endpoint="/store_limits"
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
        name: "base_limit",
        label: "Base Limit",
        type: "number",
        placeholder: "e.g., 10",
        required: true,
      },
      {
        name: "max_limit",
        label: "Max Limit",
        type: "number",
        placeholder: "e.g., 100",
        required: true,
      },
    ]}
    displayFields={[
      { key: "product_id", label: "Product ID" },
      { key: "location_id", label: "Location ID" },
      { key: "base_limit", label: "Base Limit" },
      { key: "max_limit", label: "Max Limit" },
    ]}
  />
);

export default StoreLimitManager;
