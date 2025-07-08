// src/pages/LocationManager.jsx
import React from "react";
import EntityManager from "../components/EntityManager";

const LocationManager = () => (
  <EntityManager
    title="Location"
    entityName="Location"
    endpoint="/locations"
    idField="location_id"
    uniqueIdentifierFields={["location_id"]}
    formFields={[
      {
        name: "location_id",
        label: "Location ID",
        type: "text",
        placeholder: "e.g., LOC001",
        required: true,
      },
      {
        name: "location_name",
        label: "Location Name",
        type: "text",
        placeholder: "e.g., Rouen Supplier",
        required: true,
      },
      {
        name: "location_type",
        label: "Location Type",
        type: "select",
        required: true,
        options: [
          { value: "manufacturing", label: "Manufacturing" },
          { value: "store", label: "Store" },
          { value: "supplier", label: "Supplier" },
        ],
      },
      {
        name: "address",
        label: "Address",
        type: "textarea",
        placeholder: "Street, City, Country",
      },
      { name: "city", label: "City", type: "text", placeholder: "e.g., Rouen" },
      {
        name: "state_province",
        label: "State/Province",
        type: "text",
        placeholder: "e.g., Normandy",
      },
      {
        name: "country",
        label: "Country",
        type: "text",
        placeholder: "e.g., France",
      },
      {
        name: "latitude",
        label: "Latitude",
        type: "number",
        placeholder: "e.g., 49.4431",
      },
      {
        name: "longitude",
        label: "Longitude",
        type: "number",
        placeholder: "e.g., 1.0993",
      },
    ]}
    displayFields={[
      { key: "location_id", label: "ID" },
      { key: "location_name", label: "Name" },
      { key: "location_type", label: "Type" },
      { key: "city", label: "City" },
      { key: "country", label: "Country" },
      { key: "latitude", label: "Lat" },
      { key: "longitude", label: "Long" },
    ]}
  />
);

export default LocationManager;
