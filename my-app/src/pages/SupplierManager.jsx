// src/pages/SupplierManager.jsx
import React from "react";
import EntityManager from "../components/EntityManager";

const SupplierManager = () => (
  <EntityManager
    title="Supplier"
    entityName="Supplier"
    endpoint="/suppliers"
    idField="supplier_id"
    uniqueIdentifierFields={["supplier_id"]}
    formFields={[
      {
        name: "supplier_id",
        label: "Supplier ID",
        type: "text",
        placeholder: "e.g., SUP001",
        required: true,
      },
      {
        name: "supplier_name",
        label: "Supplier Name",
        type: "text",
        placeholder: "e.g., Silicon Inc.",
        required: true,
      },
      {
        name: "contact_person",
        label: "Contact Person",
        type: "text",
        placeholder: "e.g., John Doe",
      },
      {
        name: "contact_email",
        label: "Contact Email",
        type: "email",
        placeholder: "e.g., john@example.com",
      },
      {
        name: "contact_phone",
        label: "Contact Phone",
        type: "text",
        placeholder: "e.g., +1234567890",
      },
      {
        name: "supplier_location_id",
        label: "Location ID",
        type: "text",
        placeholder: "e.g., LOC001 (must exist)",
        required: true,
      },
    ]}
    displayFields={[
      { key: "supplier_id", label: "ID" },
      { key: "supplier_name", label: "Name" },
      { key: "contact_person", label: "Contact Person" },
      { key: "contact_email", label: "Email" },
      { key: "supplier_location_id", label: "Location ID" },
    ]}
  />
);

export default SupplierManager;
