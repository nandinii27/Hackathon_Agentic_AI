// src/pages/ProductManager.jsx
import React from "react";
import EntityManager from "../components/EntityManager";

const ProductManager = () => (
  <EntityManager
    title="Product"
    entityName="Product"
    endpoint="/products"
    idField="product_id"
    uniqueIdentifierFields={["product_id"]}
    formFields={[
      {
        name: "product_id",
        label: "Product ID",
        type: "text",
        placeholder: "e.g., PRD001",
        required: true,
      },
      {
        name: "product_name",
        label: "Product Name",
        type: "text",
        placeholder: "e.g., Silicon",
        required: true,
      },
      {
        name: "product_type",
        label: "Product Type",
        type: "select",
        required: true,
        options: [
          { value: "raw_material", label: "Raw Material" },
          { value: "manufactured", label: "Manufactured" },
        ],
      },
      {
        name: "unit_of_measure",
        label: "Unit of Measure",
        type: "text",
        placeholder: "e.g., kg, unit",
        required: true,
      },
      {
        name: "description",
        label: "Description",
        type: "textarea",
        placeholder: "Optional product description",
      },
    ]}
    displayFields={[
      { key: "product_id", label: "ID" },
      { key: "product_name", label: "Name" },
      { key: "product_type", label: "Type" },
      { key: "unit_of_measure", label: "Unit" },
      { key: "description", label: "Description" },
    ]}
  />
);

export default ProductManager;
