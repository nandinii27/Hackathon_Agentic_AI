// src/App.jsx
import React, { useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
} from "@mui/material";
import HomeIcon from "@mui/icons-material/Home";
// import PackageIcon from "@mui/icons-material/Package";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import InventoryIcon from "@mui/icons-material/Inventory";
import WarehouseIcon from "@mui/icons-material/Warehouse";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import FactoryIcon from "@mui/icons-material/Factory";
import AttachMoneyIcon from "@mui/icons-material/AttachMoney";
import ChatIcon from "@mui/icons-material/Chat";
// Import components and pages (these would also need to be refactored to use Material-UI)
// For this example, we're assuming these pages/components will be updated separately.
import Dashboard from "./pages/Dashboard";
import ProductManager from "./pages/ProductManager";
import LocationManager from "./pages/LocationManager";
import InventoryManager from "./pages/InventoryManager";
import StoreLimitManager from "./pages/StoreLimitManager";
import SupplierManager from "./pages/SupplierManager";
import RawMaterialCostManager from "./pages/RawMaterialCostManager";
import TransportationRouteManager from "./pages/TransportationRouteManager";
import ChatApp from "./pages/ChatApp";

// NavItem component adapted for Material-UI Button
const NavItem = ({ icon: Icon, label, page, currentPage, onClick }) => (
  <Button
    color="inherit"
    onClick={() => onClick(page)}
    sx={{
      display: "flex",
      alignItems: "center",
      px: 2,
      py: 1,
      borderRadius: 1,
      textTransform: "none",
      fontSize: "1rem",
      fontWeight: currentPage === page ? "bold" : "normal",
      backgroundColor:
        currentPage === page ? "rgba(255, 255, 255, 0.15)" : "transparent",
      "&:hover": {
        backgroundColor: "rgba(255, 255, 255, 0.1)",
      },
    }}
  >
    <Icon sx={{ mr: 1 }} />
    {label}
  </Button>
);

// Main App Component
export default function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard />;
      case "products":
        return <ProductManager />;
      case "locations":
        return <LocationManager />;
      case "inventory":
        return <InventoryManager />;
      case "store_limits":
        return <StoreLimitManager />;
      case "suppliers":
        return <SupplierManager />;
      case "raw_material_costs":
        return <RawMaterialCostManager />;
      case "transportation_routes":
        return <TransportationRouteManager />;
      case "chat":
        return <ChatApp />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        backgroundColor: "#f3f4f6",
        fontFamily: "Inter, sans-serif",
      }}
    >
      <AppBar
        position="static"
        sx={{ background: "linear-gradient(to right, #1976d2, #1565c0)" }}
      >
        <Toolbar
          sx={{
            flexDirection: { xs: "column", md: "row" },
            justifyContent: "space-between",
            alignItems: "center",
            py: 2,
          }}
        >
          <Typography
            variant="h4"
            component="div"
            sx={{ fontWeight: "bold", mb: { xs: 2, md: 0 } }}
          >
            Smart Supply Chain
          </Typography>
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              justifyContent: "center",
              gap: { xs: 1, md: 2 },
            }}
          >
            <NavItem
              icon={HomeIcon}
              label="Dashboard"
              page="dashboard"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
            <NavItem
              icon={InventoryIcon}
              label="Products"
              page="products"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
            <NavItem
              icon={LocationOnIcon}
              label="Locations"
              page="locations"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
            <NavItem
              icon={WarehouseIcon}
              label="Inventory"
              page="inventory"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
            <NavItem
              icon={ShoppingCartIcon}
              label="Store Limits"
              page="store_limits"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
            <NavItem
              icon={FactoryIcon}
              label="Suppliers"
              page="suppliers"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
            <NavItem
              icon={AttachMoneyIcon}
              label="Raw Costs"
              page="raw_material_costs"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
            <NavItem
              icon={LocalShippingIcon}
              label="Routes"
              page="transportation_routes"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
            <NavItem
              icon={ChatIcon}
              label="Chat"
              page="chat"
              currentPage={currentPage}
              onClick={setCurrentPage}
            />
          </Box>
        </Toolbar>
      </AppBar>

      <Container
        maxWidth="lg"
        sx={{
          mt: 4,
          p: 3,
          backgroundColor: "white",
          borderRadius: 2,
          boxShadow: 3,
        }}
      >
        {renderPage()}
      </Container>
    </Box>
  );
}
