// src/api.js

// Base URL for your Flask API
// IMPORTANT: If running locally, ensure your Flask app is on http://localhost:5000
// If deployed, replace this with your Flask app's deployed URL.
const API_BASE_URL = "http://localhost:5000/api";

// Helper function for API calls
export async function apiCall(endpoint, method = "GET", data = null) {
  const url = `${API_BASE_URL}${endpoint}`;
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };
  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);
    const result = await response.json();
    if (!response.ok) {
      // If the server returns an error message, use it. Otherwise, a generic one.
      throw new Error(result.error || "Something went wrong");
    }
    return result;
  } catch (error) {
    console.error(`API Call Error (${method} ${url}):`, error);
    throw error;
  }
}
