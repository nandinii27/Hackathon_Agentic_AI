import React from "react";

const NavItem = ({ icon: Icon, label, page, currentPage, onClick }) => (
  <button
    onClick={() => onClick(page)}
    className={`flex items-center px-3 py-2 rounded-md transition duration-200 ease-in-out
      ${
        currentPage === page
          ? "bg-blue-800 text-white shadow-md"
          : "text-blue-200 hover:bg-blue-700 hover:text-white"
      }`}
  >
    <Icon size={20} className="mr-2" />
    {label}
  </button>
);

export default NavItem;
