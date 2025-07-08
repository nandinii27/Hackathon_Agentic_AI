// src/components/EntityManager.jsx
import React, { useState, useEffect } from "react";
import { Trash2, Edit2, Plus, X, Check } from "lucide-react";
import { apiCall } from "../api"; // Import apiCall
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  TextField,
  Container,
} from "@mui/material";
const EntityManager = ({
  title,
  entityName,
  endpoint,
  formFields,
  idField,
  displayFields,
  uniqueIdentifierFields = [],
  children,
}) => {
  const [entities, setEntities] = useState([]);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [editId, setEditId] = useState(null); // MongoDB _id for editing
  const [editIdentifier, setEditIdentifier] = useState({}); // For PUT/DELETE by uniqueIdentifierFields

  useEffect(() => {
    fetchEntities();
  }, []);

  const fetchEntities = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiCall(endpoint);
      setEntities(data);
    } catch (err) {
      setError(`Failed to fetch ${entityName}s: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      if (isEditing) {
        const identifierPath = uniqueIdentifierFields
          .map((field) => editIdentifier[field])
          .join("/");
        await apiCall(`${endpoint}/${identifierPath}`, "PUT", formData);
        alert(`${entityName} updated successfully!`);
      } else {
        await apiCall(endpoint, "POST", formData);
        alert(`${entityName} added successfully!`);
      }
      setFormData({});
      setIsEditing(false);
      setEditId(null);
      setEditIdentifier({});
      fetchEntities();
    } catch (err) {
      setError(`Failed to save ${entityName}: ${err.message}`);
    }
  };

  const handleEdit = (entity) => {
    // For date inputs, ensure the format is 'YYYY-MM-DD'
    const newFormData = { ...entity };
    formFields.forEach((field) => {
      if (field.type === "date" && newFormData[field.name]) {
        // Assuming date comes as ISO string or similar, convert to YYYY-MM-DD
        newFormData[field.name] = new Date(newFormData[field.name])
          .toISOString()
          .split("T")[0];
      }
    });

    setFormData(newFormData);
    setIsEditing(true);
    setEditId(entity._id);
    const identifier = {};
    uniqueIdentifierFields.forEach((field) => {
      identifier[field] = entity[field];
    });
    setEditIdentifier(identifier);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = async (entity) => {
    if (window.confirm(`Are you sure you want to delete this ${entityName}?`)) {
      setError("");
      try {
        const identifierPath = uniqueIdentifierFields
          .map((field) => entity[field])
          .join("/");
        await apiCall(`${endpoint}/${identifierPath}`, "DELETE");
        alert(`${entityName} deleted successfully!`);
        fetchEntities();
      } catch (err) {
        setError(`Failed to delete ${entityName}: ${err.message}`);
      }
    }
  };

  const handleCancelEdit = () => {
    setFormData({});
    setIsEditing(false);
    setEditId(null);
    setEditIdentifier({});
    setError("");
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-3xl font-bold text-gray-800 mb-6">
        {title} Management
      </h2>

      <form
        onSubmit={handleSubmit}
        className="mb-8 p-6 bg-gray-50 border border-gray-200 rounded-lg shadow-sm"
      >
        <h3 className="text-2xl font-semibold text-gray-700 mb-4">
          {isEditing ? `Edit ${entityName}` : `Add New ${entityName}`}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {formFields.map((field) => (
            <div key={field.name} className="flex flex-col">
              <label
                htmlFor={field.name}
                className="text-sm font-medium text-gray-700 mb-1"
              >
                {field.label}{" "}
                {field.required && <span className="text-red-500">*</span>}
              </label>
              {field.type === "select" ? (
                <select
                  id={field.name}
                  name={field.name}
                  value={formData[field.name] || ""}
                  onChange={handleInputChange}
                  required={field.required}
                  className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
                >
                  <option value="">
                    {field.placeholder || `Select ${field.label}`}
                  </option>
                  {field.options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : field.type === "textarea" ? (
                <textarea
                  id={field.name}
                  name={field.name}
                  value={formData[field.name] || ""}
                  onChange={handleInputChange}
                  required={field.required}
                  placeholder={field.placeholder}
                  rows="3"
                  className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700"
                ></textarea>
              ) : (
                <TextField
                  variant="outlined"
                  size="small"
                  type={field.type || "text"}
                  id={field.name}
                  name={field.name}
                  value={formData[field.name] || ""}
                  onChange={handleInputChange}
                  required={field.required}
                  placeholder={field.placeholder}
                  disabled={isEditing && field.name === idField}
                  className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-700 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
              )}
            </div>
          ))}
        </div>
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
        <br />
        <div className="flex space-x-4">
          <Button
            type="submit"
            variant="contained"
            color="success"
            style={{ margin: "2px" }}
          >
            {isEditing ? (
              <Check size={20} className="mr-2" />
            ) : (
              <Plus size={20} className="mr-2" />
            )}
            {isEditing ? `Update ${entityName}` : `Add ${entityName}`}
          </Button>
          {isEditing && (
            <Button
              style={{ margin: "2px" }}
              type="Button"
              onClick={handleCancelEdit}
              variant="contained"
              color="error"
            >
              <X size={20} className="mr-2" /> Cancel Edit
            </Button>
          )}
        </div>
      </form>

      <h3 className="text-2xl font-semibold text-gray-800 mb-4">
        Existing {title}
      </h3>
      {loading ? (
        <p className="text-gray-600">Loading {entityName}s...</p>
      ) : entities.length === 0 ? (
        <p className="text-gray-600">No {entityName}s found.</p>
      ) : (
        <div className="overflow-x-auto bg-gray-50 p-4 rounded-lg border border-gray-200">
          <table className="min-w-full bg-white rounded-md shadow-sm">
            <thead className="bg-gray-100 border-b border-gray-200">
              <tr>
                {displayFields.map((field) => (
                  <th
                    key={field.key}
                    className="py-3 px-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider"
                  >
                    {field.label}
                  </th>
                ))}
                <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {entities.map((entity, index) => (
                <tr
                  key={entity._id || index}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  {displayFields.map((field) => (
                    <td
                      key={field.key}
                      className="py-3 px-4 text-sm text-gray-800"
                    >
                      {field.format
                        ? field.format(entity[field.key])
                        : entity[field.key]}
                    </td>
                  ))}
                  <td>
                    <div>
                      <Button
                        variant="contained"
                        color="warning"
                        onClick={() => handleEdit(entity)}
                        className="text-blue-600 hover:text-blue-800 transition duration-150 ease-in-out"
                        title="Edit"
                        style={{ margin: "2px" }}
                      >
                        <Edit2 size={18} />
                      </Button>
                      <Button
                        variant="contained"
                        color="error"
                        onClick={() => handleDelete(entity)}
                        className="text-red-600 hover:text-red-800 transition duration-150 ease-in-out"
                        title="Delete"
                      >
                        <Trash2 size={18} />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {children}
    </div>
  );
};

export default EntityManager;
