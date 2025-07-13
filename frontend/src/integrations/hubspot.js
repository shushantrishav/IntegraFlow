import { useState, useEffect } from "react";
import { Box, Button, CircularProgress } from "@mui/material";
import axios from "axios";

export const HubspotIntegration = ({
  user,
  org,
  integrationParams,
  setIntegrationParams,
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // Trigger OAuth and open auth popup
  const handleConnectClick = async () => {
    try {
      setIsConnecting(true);
      const formData = new FormData();
      formData.append("user_id", user);
      formData.append("org_id", org);

      const response = await axios.post(
        `http://localhost:8000/integrations/hubspot/authorize`,
        formData
      );
      const authURL = response?.data;

      const newWindow = window.open(
        authURL,
        "HubSpot Authorization",
        "width=600,height=600"
      );

      // Wait for popup to close
      const pollTimer = window.setInterval(() => {
        if (newWindow?.closed !== false) return;
        window.clearInterval(pollTimer);
        setTimeout(handleWindowClosed, 800); // Wait briefly for Redis to be ready
      }, 200);
    } catch (e) {
      setIsConnecting(false);
      alert(e?.response?.data?.detail || "HubSpot connection failed");
    }
  };

  // After OAuth popup closes, fetch credentials
  const handleWindowClosed = async () => {
    try {
      const formData = new FormData();
      formData.append("user_id", user);
      formData.append("org_id", org);

      const response = await axios.post(
        `http://localhost:8000/integrations/hubspot/credentials`,
        formData
      );
      const credentials = response.data;

      if (credentials) {
        setIsConnected(true);
        setIntegrationParams((prev) => ({
          ...prev,
          credentials,
          type: "Hubspot",
          connected: true,
          connect: handleConnectClick,
          load: async () => {
            const res = await axios.post(
              "http://localhost:8000/integrations/hubspot/load",
              { credentials }
            );
            return res.data;
          },
        }));
      }

      setIsConnecting(false);
    } catch (e) {
      setIsConnecting(false);
      alert(
        e?.response?.data?.detail || "Failed to retrieve HubSpot credentials"
      );
    }
  };

  useEffect(() => {
    setIsConnected(
      integrationParams?.type === "Hubspot" && integrationParams?.credentials
        ? true
        : false
    );
  }, [integrationParams]);

  return (
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* The Connect/Connected Button */}
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        sx={{ mt: 2 }}
      >
        <Button
          variant="contained"
          onClick={isConnected ? () => {} : handleConnectClick} // Disable click if connected
          disabled={isConnecting || isConnected} // Disable if connecting or already connected
          sx={{
            // Apply primary button styles
            backgroundColor: isConnected ? "var(--success-color)" : "var(--primary-color)",
            color: isConnected ? "white" : "#1a202c", // White text for connected, dark for primary
            boxShadow: isConnected ? "0 2px 5px rgba(72, 187, 120, 0.2)" : "0 2px 5px rgba(99, 179, 237, 0.2)",
            borderRadius: "var(--border-radius)",
            padding: "12px 25px",
            fontWeight: "600",
            width: "100%", // Make it full width
            transition: "background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease, opacity 0.3s ease",
            "&:hover": {
              backgroundColor: isConnected ? "var(--success-color)" : "var(--primary-dark)",
              transform: isConnected ? "none" : "translateY(-1px)", // No lift if connected
              boxShadow: isConnected ? "0 2px 5px rgba(72, 187, 120, 0.3)" : "0 4px 8px rgba(99, 179, 237, 0.3)",
              cursor: isConnected ? "default" : "pointer", // Change cursor if connected
            },
            "&:disabled": {
              backgroundColor: isConnected ? "var(--success-color)" : "var(--table-row-odd-bg)", // Keep success color if connected and disabled, else disabled grey
              color: isConnected ? "white" : "var(--text-light-color)", // Keep white for connected, faded for disabled
              opacity: isConnected ? 1 : 0.7, // Keep full opacity if connected, fade if disabled
              boxShadow: "none",
              cursor: "not-allowed",
              pointerEvents: isConnected ? "none" : "auto", // Explicitly set pointer-events for disabled state
            }
          }}
        >
          {isConnected ? (
            "HubSpot Connected"
          ) : isConnecting ? (
            <CircularProgress size={20} sx={{ color: isConnected ? "white" : "#1a202c" }} /> // Adjust progress color
          ) : (
            "Connect to HubSpot"
          )}
        </Button>
      </Box>
    </Box>
  );
};
