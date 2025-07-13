import React, { useState } from "react";
import {
  Button,
  CircularProgress,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";
import axios from "axios";

export default function DataForm({ integration, setIntegrationParams }) {
  const [loading, setLoading] = useState(false);
  const [loadedData, setLoadedData] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);

  const ITEMS_PER_PAGE = 10;

  // --- Custom Alert/Message Box Function ---
  // Instead of alert(), use a custom message box for better UX
  const showCustomAlert = (message, type = 'info', duration = 3000) => {
    let alertBox = document.getElementById('customAlertBox');
    if (!alertBox) {
        alertBox = document.createElement('div');
        alertBox.id = 'customAlertBox';
        document.body.appendChild(alertBox);
        // Basic styling for the alert box is in index.css
    }

    // Set background color based on type
    switch (type) {
        case 'success':
            alertBox.style.backgroundColor = 'var(--success-color)';
            alertBox.style.color = 'white';
            break;
        case 'error':
            alertBox.style.backgroundColor = 'var(--danger-color)';
            alertBox.style.color = 'white';
            break;
        case 'warning':
            alertBox.style.backgroundColor = '#ecc94b'; // Yellow/Gold from dark theme
            alertBox.style.color = '#1a202c'; // Dark text for warning
            break;
        case 'info':
        default:
            alertBox.style.backgroundColor = 'var(--primary-color)';
            alertBox.style.color = 'white';
            break;
    }

    alertBox.textContent = message;
    alertBox.style.opacity = '1';
    alertBox.style.transform = 'translateX(-50%) translateY(0)';

    // Hide the alert after a duration
    setTimeout(() => {
        alertBox.style.opacity = '0';
        alertBox.style.transform = 'translateX(-50%) translateY(20px)'; // Slide down slightly
        setTimeout(() => {
            // Optionally remove the element after it's fully hidden
            // alertBox.remove();
        }, 500); // Match transition duration
    }, duration);
  };


  const handleLoad = async () => {
    if (!integration?.credentials || !integration?.type) {
      showCustomAlert("Integration not configured or type missing.", "warning");
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("credentials", JSON.stringify(integration.credentials));
      const response = await axios.post(
        `http://localhost:8000/integrations/${integration.type.toLowerCase()}/load`,
        formData
      );
      const data = response.data;
      setLoadedData(data);
      setCurrentPage(1);
      showCustomAlert("Data Loaded!", "success");
    } catch (e) {
      console.error("Error loading data:", e);
      showCustomAlert(e?.response?.data?.detail || "Error loading data", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = () => {
    setLoadedData([]);
    setIntegrationParams({});
    showCustomAlert("Disconnected!", "info");
  };

  const handleExport = () => {
    if (loadedData.length === 0) {
      showCustomAlert("No data to export!", "warning");
      return;
    }
    const dataStr = JSON.stringify(loadedData, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "table.json";
    link.click();
    URL.revokeObjectURL(url);
    showCustomAlert("Table data exported as JSON!", "success");
  };

  const totalPages = Math.ceil(loadedData.length / ITEMS_PER_PAGE);
  const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
  const pageData = loadedData.slice(startIdx, startIdx + ITEMS_PER_PAGE);

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const getTableHeaders = () => {
    if (pageData.length === 0) return [];
    // Filter out keys that might not be suitable as table headers or are internal
    const headers = Object.keys(pageData[0]);
    // Example: if you want to exclude a specific key like '__v' or '_id'
    // return headers.filter(key => !key.startsWith('__') && key !== '_id');
    return headers;
  };

  const formatHeader = (key) =>
    key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

  // Function to determine lead status badge color (example, extend as needed)
  const getLeadStatusColor = (status) => {
    switch (status) {
      case 'UNQUALIFIED': return { backgroundColor: '#ecc94b', color: '#1a202c' }; // Yellow/Gold
      case 'CONNECTED': return { backgroundColor: 'var(--success-color)', color: 'white' };
      case 'QUALIFIED': return { backgroundColor: 'var(--primary-color)', color: 'white' };
      case 'NEW': return { backgroundColor: '#9f7aea', color: 'white' }; // Purple
      default: return { backgroundColor: 'var(--secondary-color)', color: 'white' };
    }
  };

  return (
    <Box
      sx={{
        marginTop: "auto", // Adjusted margin-top
        backgroundColor: "var(--card-background)",
        padding: "1.5rem 1.8rem",
        borderRadius: "var(--border-radius)",
        boxShadow: "0 4px 15px var(--shadow-color)",
        border: "1px solid var(--border-color)",
      }}
    >
      {/* Connection Status Badge inside DataForm */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-start",
          marginBottom: "20px",
        }}
      >
      </Box>

      <Box
        mb={2}
        display="flex"
        gap={2}
        justifyContent="flex-start" // Align to start for consistency
        flexWrap="wrap"
      >
        <Button
          onClick={handleLoad}
          variant="contained"
          disabled={!integration?.connected || loading} // Disabled if not connected or loading
          sx={{
            backgroundColor: "var(--primary-color)",
            color: "#1a202c",
            "&:hover": { backgroundColor: "var(--primary-dark)" },
            borderRadius: "var(--border-radius)",
            padding: "12px 25px",
            fontWeight: "600",
            boxShadow: "0 2px 5px rgba(99, 179, 237, 0.2)",
            "&:disabled": {
              backgroundColor: "var(--table-row-odd-bg)", // Darker disabled background
              color: "var(--text-light-color)", // Lighter text for disabled
              boxShadow: "none",
            }
          }}
        >
          {loading ? <CircularProgress size={20} sx={{ color: "#1a202c" }} /> : "Load Data"}
        </Button>

        <Button
          onClick={() => {
            setLoadedData([]);
            showCustomAlert("Table Cleared!", "info");
          }}
          variant="outlined"
          disabled={!integration?.connected} // Disabled if not connected
          sx={{
            backgroundColor: "#4a5568", // Secondary button background
            color: "var(--text-color)",
            border: "1px solid var(--border-color)",
            "&:hover": { backgroundColor: "#5a657a", borderColor: "#5a657a" },
            borderRadius: "var(--border-radius)",
            padding: "12px 25px",
            fontWeight: "600",
            boxShadow: "0 2px 5px rgba(0, 0, 0, 0.15)",
            "&:disabled": {
              backgroundColor: "var(--table-row-odd-bg)", // Darker disabled background
              color: "var(--text-light-color)", // Lighter text for disabled
              boxShadow: "none",
              border: "1px solid var(--table-row-odd-bg)", // Match border to background
            }
          }}
        >
          Clear
        </Button>

        <Button
          onClick={handleDisconnect}
          variant="outlined"
          color="error"
          disabled={!integration?.connected} // Disabled if not connected
          sx={{
            backgroundColor: "var(--danger-color)",
            color: "#1a202c",
            "&:hover": { backgroundColor: "#e53e3e" },
            borderRadius: "var(--border-radius)",
            padding: "12px 25px",
            fontWeight: "600",
            boxShadow: "0 2px 5px rgba(252, 129, 129, 0.2)",
            "&:disabled": {
              backgroundColor: "var(--table-row-odd-bg)", // Darker disabled background
              color: "var(--text-light-color)", // Lighter text for disabled
              boxShadow: "none",
              border: "1px solid var(--table-row-odd-bg)", // Match border to background
            }
          }}
        >
          Disconnect
        </Button>

        <Button
          onClick={handleExport}
          variant="outlined"
          disabled={loadedData.length === 0 || !integration?.connected} // Disabled if no data or not connected
          sx={{
            backgroundColor: "var(--primary-color)",
            color: "#1a202c",
            "&:hover": { backgroundColor: "var(--primary-dark)" },
            borderRadius: "var(--border-radius)",
            padding: "12px 25px",
            fontWeight: "600",
            boxShadow: "0 2px 5px rgba(99, 179, 237, 0.2)",
            "&:disabled": {
              backgroundColor: "var(--table-row-odd-bg)",
              color: "var(--text-light-color)",
              boxShadow: "none",
            }
          }}
        >
          Export Table
        </Button>
      </Box>

      {loadedData.length > 0 && (
        <Box className="table-wrapper">
          <Typography variant="h6" component="h2" sx={{ color: "var(--text-color)", fontWeight: "600", marginBottom: "20px" }}>
            Integration Data
          </Typography>
          <TableContainer
            component={Paper}
            sx={{
              backgroundColor: "var(--card-background)",
              borderRadius: "var(--border-radius)",
              boxShadow: "0 4px 15px var(--shadow-color)",
              border: "1px solid var(--border-color)",
              overflow: "hidden", // Ensures rounded corners apply to table
            }}
          >
            <Table
              sx={{
                borderCollapse: "separate",
                borderSpacing: 0,
                minWidth: "800px", // Ensure table doesn't get too squished
              }}
            >
              <TableHead>
                <TableRow>
                  {getTableHeaders().map((header) => (
                    <TableCell
                      key={header}
                      sx={{
                        backgroundColor: "var(--table-header-bg)",
                        color: "var(--text-light-color)",
                        fontWeight: "600",
                        textTransform: "uppercase",
                        fontSize: "0.85em",
                        padding: "12px 15px",
                        borderBottom: "1px solid var(--border-color)",
                        // Apply rounded corners to first/last header cells
                        "&:first-of-type": { borderTopLeftRadius: "var(--border-radius)" },
                        "&:last-of-type": { borderTopRightRadius: "var(--border-radius)" },
                      }}
                    >
                      {formatHeader(header)}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {pageData.map((item, index) => (
                  <TableRow
                    key={item.id || index}
                    sx={{
                      backgroundColor: index % 2 === 0 ? "var(--table-row-even-bg)" : "var(--table-row-odd-bg)",
                      "&:hover": { backgroundColor: "var(--table-row-hover-bg)", cursor: "pointer" },
                      // Apply rounded corners to last row cells
                      "&:last-child td:first-of-type": { borderBottomLeftRadius: "var(--border-radius)" },
                      "&:last-child td:last-of-type": { borderBottomRightRadius: "var(--border-radius)" },
                    }}
                  >
                    {getTableHeaders().map((header) => (
                      <TableCell
                        key={header}
                        sx={{
                          borderBottom: "1px solid var(--border-color)",
                          color: "var(--text-color)",
                          padding: "12px 15px",
                        }}
                      >
                        {header === "leadStatus" ? (
                          <Box
                            component="span"
                            sx={{
                              padding: "5px 10px",
                              borderRadius: "15px",
                              fontSize: "0.8em",
                              fontWeight: "500",
                              textTransform: "uppercase",
                              display: "inline-block",
                              ...getLeadStatusColor(item[header]), // Apply dynamic color
                            }}
                          >
                            {item[header]}
                          </Box>
                        ) : (
                          item[header] !== null && item[header] !== undefined
                            ? item[header]
                            : "-"
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            mt={2}
            gap={2}
            sx={{
              paddingTop: "15px",
              borderTop: "1px solid var(--border-color)",
            }}
          >
            <Button
              variant="outlined"
              onClick={handlePrevPage}
              disabled={currentPage === 1}
              sx={{
                backgroundColor: "var(--card-background)",
                color: "var(--text-color)",
                border: "1px solid var(--border-color)",
                "&:hover:not(:disabled)": { backgroundColor: "#3b4556", borderColor: "#5a657a" },
                "&:disabled": {
                  opacity: 0.6,
                  cursor: "not-allowed",
                  backgroundColor: "var(--table-row-odd-bg)",
                  color: "var(--text-light-color)",
                },
                borderRadius: "var(--border-radius)",
                padding: "8px 15px",
              }}
            >
              {"<<"}
            </Button>
            <Typography sx={{ fontWeight: "500", color: "var(--text-color)", minWidth: "70px", textAlign: "center" }}>
              {currentPage} / {totalPages}
            </Typography>
            <Button
              variant="outlined"
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
              sx={{
                backgroundColor: "var(--card-background)",
                color: "var(--text-color)",
                border: "1px solid var(--border-color)",
                "&:hover:not(:disabled)": { backgroundColor: "#3b4556", borderColor: "#5a657a" },
                "&:disabled": {
                  opacity: 0.6,
                  cursor: "not-allowed",
                  backgroundColor: "var(--table-row-odd-bg)",
                  color: "var(--text-light-color)",
                },
                borderRadius: "var(--border-radius)",
                padding: "8px 15px",
              }}
            >
              {">>"}
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
}
