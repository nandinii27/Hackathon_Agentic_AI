// src/pages/TransportationRouteManager.jsx
import React from "react";
import EntityManager from "../components/EntityManager";

const TransportationRouteManager = () => (
  <EntityManager
    title="Transportation Route"
    entityName="Transportation Route"
    endpoint="/transportation_routes"
    idField="origin_location_id"
    uniqueIdentifierFields={["origin_location_id", "destination_location_id"]}
    formFields={[
      {
        name: "origin_location_id",
        label: "Origin Location ID",
        type: "text",
        placeholder: "e.g., LOC003",
        required: true,
      },
      {
        name: "destination_location_id",
        label: "Destination Location ID",
        type: "text",
        placeholder: "e.g., LOC004",
        required: true,
      },
      {
        name: "base_cost_per_kg",
        label: "Base Cost Per KG",
        type: "number",
        placeholder: "e.g., 1.50",
        required: true,
      },
      {
        name: "estimated_travel_time_hours",
        label: "Est. Travel Time (Hours)",
        type: "number",
        placeholder: "e.g., 3.0",
      },
      {
        name: "distance_km",
        label: "Distance (KM)",
        type: "number",
        placeholder: "e.g., 350",
      },
    ]}
    displayFields={[
      { key: "origin_location_id", label: "Origin ID" },
      { key: "destination_location_id", label: "Destination ID" },
      {
        key: "base_cost_per_kg",
        label: "Base Cost/KG",
        format: (val) => `$${val.toFixed(2)}`,
      },
      { key: "estimated_travel_time_hours", label: "Travel Time (h)" },
      { key: "distance_km", label: "Distance (km)" },
    ]}
  />
);

export default TransportationRouteManager;
