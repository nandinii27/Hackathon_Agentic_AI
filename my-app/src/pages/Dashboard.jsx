// src/pages/Dashboard.jsx
import React, { useState, useEffect } from "react";
import { RefreshCcw, Eye } from "lucide-react";
import { apiCall } from "../api";
import Modal from "../components/Modal";
import { Button, Box } from "@mui/material";
const style = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  border: "2px solid #000",
  boxShadow: 24,
  p: 4,
};

const Dashboard = () => {
  const [automationLog, setAutomationLog] = useState([]);
  const [loadingAutomation, setLoadingAutomation] = useState(false);
  const [automationError, setAutomationError] = useState("");
  const [optimizationRuns, setOptimizationRuns] = useState([]);
  const [orders, setOrders] = useState([]);
  const [viewLogModalOpen, setViewLogModalOpen] = useState(false);
  const [currentLogDetails, setCurrentLogDetails] = useState("");

  const fetchOptimizationRuns = async () => {
    try {
      const data = await apiCall("/optimization_runs");
      setOptimizationRuns(
        data.sort(
          (a, b) => new Date(b.run_timestamp) - new Date(a.run_timestamp)
        )
      );
    } catch (error) {
      console.error("Failed to fetch optimization runs:", error);
    }
  };

  const fetchOrders = async () => {
    try {
      const data = await apiCall("/orders");
      setOrders(
        data.sort((a, b) => new Date(b.order_date) - new Date(a.order_date))
      );
    } catch (error) {
      console.error("Failed to fetch orders:", error);
    }
  };

  useEffect(() => {
    fetchOptimizationRuns();
    fetchOrders();
  }, []);

  const runAutomation = async () => {
    setLoadingAutomation(true);
    setAutomationError("");
    setAutomationLog([]);
    try {
      const result = await apiCall("/run_automation", "POST");
      setAutomationLog(result.log || []);
      alert(result.message);
      fetchOptimizationRuns();
      fetchOrders();
    } catch (error) {
      setAutomationError(error.message);
      alert(`Automation failed: ${error.message}`);
    } finally {
      setLoadingAutomation(false);
    }
  };

  const onViewLog = (details) => {
    setCurrentLogDetails(details);
    setViewLogModalOpen(true);
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-3xl font-bold text-gray-800 mb-6">
        Supply Chain Dashboard
      </h2>

      <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-lg shadow-sm">
        <h3 className="text-2xl font-semibold text-blue-700 mb-4">
          Automation Control
        </h3>
        <Button
          variant="contained"
          onClick={runAutomation}
          disabled={loadingAutomation}
        >
          {loadingAutomation ? (
            <>
              <RefreshCcw className="animate-spin mr-2" size={20} /> Running
              Automation...
            </>
          ) : (
            <>
              <RefreshCcw className="mr-2" size={20} /> Run Supply Chain
              Automation
            </>
          )}
        </Button>
        {automationError && (
          <p className="text-red-600 mt-4 text-sm">{automationError}</p>
        )}
        {automationLog.length > 0 && (
          <div className="mt-6 bg-blue-100 p-4 rounded-md border border-blue-300">
            <h4 className="font-semibold text-blue-800 mb-2">
              Latest Automation Log:
            </h4>
            <ul className="list-disc list-inside text-sm text-blue-800 max-h-40 overflow-y-auto">
              {automationLog.map((log, index) => (
                <li key={index}>{log}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h3 className="text-2xl font-semibold text-gray-800 mb-4">
            Recent Optimization Runs
          </h3>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
            {optimizationRuns.length === 0 ? (
              <p className="text-gray-600">No optimization runs found.</p>
            ) : (
              <ul className="space-y-3">
                {optimizationRuns.map((run) => (
                  <li key={run._id}>
                    <p className="font-medium text-gray-900">
                      Run ID: {run._id}
                    </p>
                    <p className="text-sm text-gray-700">
                      Timestamp: {new Date(run.run_timestamp).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-700">
                      Status:{" "}
                      <span
                        className={`font-semibold ${
                          run.status === "success"
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {run.status}
                      </span>
                    </p>
                    <p className="text-sm text-gray-700">
                      Summary: {run.summary}
                    </p>
                    {run.details && (
                      <Button
                        onClick={() =>
                          onViewLog(JSON.parse(run.details).log.join("\n"))
                        }
                        className="text-blue-600 hover:underline text-sm mt-1 flex items-center"
                      >
                        <Eye size={16} className="mr-1" /> View Full Log
                      </Button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-2xl font-semibold text-gray-800 mb-4">
            Recent Orders
          </h3>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
            {orders.length === 0 ? (
              <p className="text-gray-600">No orders found.</p>
            ) : (
              <ul className="space-y-3">
                {orders.map((order) => (
                  <li
                    key={order._id}
                    className="p-3 bg-white rounded-md shadow-sm border border-gray-100"
                  >
                    <p className="font-medium text-gray-900">
                      Order ID: {order._id}
                    </p>
                    <p className="text-sm text-gray-700">
                      Product: {order.product_id}
                    </p>
                    <p className="text-sm text-gray-700">
                      Quantity: {order.quantity}
                    </p>
                    <p className="text-sm text-gray-700">
                      Type: {order.order_type}
                    </p>
                    <p className="text-sm text-gray-700">
                      Source: {order.source_location_id}
                    </p>
                    <p className="text-sm text-gray-700">
                      Destination: {order.destination_location_id}
                    </p>
                    <p className="text-sm text-gray-700">
                      Status:{" "}
                      <span className="font-semibold text-purple-600">
                        {order.status}
                      </span>
                    </p>
                    <p className="text-sm text-gray-700">
                      Cost: $
                      {order.calculated_cost
                        ? order.calculated_cost.toFixed(2)
                        : "N/A"}
                    </p>
                    <p className="text-sm text-gray-700">
                      Order Date: {new Date(order.order_date).toLocaleString()}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
      {/*
      <Modal
        isOpen={viewLogModalOpen}
        onClose={() => setViewLogModalOpen(false)}
        title="Automation Log Details"
      ></Modal> */}

      <Modal isOpen={viewLogModalOpen}>
        <Box sx={style}>
          <pre>{currentLogDetails}</pre>
          <Button
            variant="contained"
            color="error"
            onClick={() => setViewLogModalOpen(false)}
          >
            close
          </Button>
        </Box>
      </Modal>
    </div>
  );
};

export default Dashboard;
