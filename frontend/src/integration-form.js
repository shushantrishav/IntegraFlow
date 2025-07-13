import { useState } from "react";
import { Box, Autocomplete, TextField, Typography, Button } from "@mui/material"; // Added Button
import { AirtableIntegration } from "./integrations/airtable";
import { NotionIntegration } from "./integrations/notion";
import { HubspotIntegration } from "./integrations/hubspot.js";
import DataForm from "./data-form";

const integrationMapping = {
  Notion: NotionIntegration,
  Airtable: AirtableIntegration,
  Hubspot: HubspotIntegration,
};

export const IntegrationForm = () => {
  const [integrationParams, setIntegrationParams] = useState({});
  const [user, setUser] = useState("TestUser");
  const [org, setOrg] = useState("TestOrg");
  const [currType, setCurrType] = useState(null);
  const CurrIntegration = integrationMapping[currType];

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        width: "98%", // Set to 98% width
        margin: "20px auto", // Center horizontally with auto margins and add top/bottom margin
        padding: "20px",
        backgroundColor: "var(--background-color)", // Use CSS variable
        color: "var(--text-color)", // Use CSS variable
        boxSizing: "border-box", // Ensure padding is included in the width calculation for the main container
        borderRadius: "var(--border-radius)", // Apply border-radius for consistency
        boxShadow: "0 8px 20px var(--shadow-color)", // Apply shadow for dashboard feel
      }}
    >
      {/* Header Section */}
      <Box sx={{ textAlign: "center", marginBottom: "30px", width: "100%" }}>
        <Typography
          variant="h4"
          component="h1"
          sx={{
            fontSize: "2.5em",
            color: "var(--primary-color)",
            fontWeight: "700",
            textShadow: "0 2px 5px rgba(0, 0, 0, 0.3)",
          }}
        >
          Dashboard
        </Typography>
      </Box>

      {/* User Information Section (Card) */}
      <Box
        sx={{
          backgroundColor: "var(--card-background)",
          padding: "25px 30px",
          borderRadius: "var(--border-radius)",
          boxShadow: "0 4px 15px var(--shadow-color)",
          marginBottom: "25px", // Consistent spacing below this card
          border: "1px solid var(--border-color)",
          display: "flex",
          flexDirection: "column",
          gap: "20px", // Spacing between form groups
          width: "100%", // Set to 100% of its parent (which is now 90% wide)
          boxSizing: "border-box", // Ensure padding is included in the width calculation
        }}
      >
        <Typography variant="h6" component="h2" sx={{ color: "var(--text-color)", fontWeight: "600" }}>
          User Information
        </Typography>
        <TextField
          label="User"
          value={user}
          onChange={(e) => setUser(e.target.value)}
          InputLabelProps={{ sx: { color: "var(--text-light-color)" } }}
          InputProps={{
            readOnly: true, // Make it readonly as in the HTML example
            sx: {
              color: "var(--text-color)",
              backgroundColor: "#3b4556",
              "& fieldset": { borderColor: "var(--border-color) !important" },
              "&:hover fieldset": { borderColor: "var(--primary-color) !important" },
              "&.Mui-focused fieldset": { borderColor: "var(--primary-color) !important", boxShadow: "0 0 0 3px rgba(99, 179, 237, 0.3)" },
              borderRadius: "var(--border-radius)",
            },
          }}
          sx={{ '& .MuiInputBase-root': { borderRadius: 'var(--border-radius)' } }}
        />
        <TextField
          label="Organization"
          value={org}
          onChange={(e) => setOrg(e.target.value)}
          InputLabelProps={{ sx: { color: "var(--text-light-color)" } }}
          InputProps={{
            readOnly: true, // Make it readonly
            sx: {
              color: "var(--text-color)",
              backgroundColor: "#3b4556",
              "& fieldset": { borderColor: "var(--border-color) !important" },
              "&:hover fieldset": { borderColor: "var(--primary-color) !important" },
              "&.Mui-focused fieldset": { borderColor: "var(--primary-color) !important", boxShadow: "0 0 0 3px rgba(99, 179, 237, 0.3)" },
              borderRadius: "var(--border-radius)",
            },
          }}
          sx={{ '& .MuiInputBase-root': { borderRadius: 'var(--border-radius)' } }}
        />
        <Autocomplete
          id="integration-type"
          options={Object.keys(integrationMapping)}
          disabled={integrationParams.connected} // Disable if an integration is connected
          sx={{
            width: "100%",
            "& .MuiInputBase-root": {
              color: "var(--text-color)",
              backgroundColor: "#3b4556",
              borderRadius: "var(--border-radius)",
              "& fieldset": { borderColor: "var(--border-color) !important" },
              "&:hover fieldset": { borderColor: "var(--primary-color) !important" },
              "&.Mui-focused fieldset": { borderColor: "var(--primary-color) !important", boxShadow: "0 0 0 3px rgba(99, 179, 237, 0.3)" },
            },
            "& .MuiInputLabel-root": { color: "var(--text-light-color)" },
            "& .MuiSvgIcon-root": { color: "var(--text-light-color)" },
            "&.Mui-disabled": { // Styling for disabled Autocomplete
              "& .MuiInputBase-root": {
                backgroundColor: "var(--table-row-odd-bg)",
                color: "var(--text-light-color)",
                "& fieldset": { borderColor: "var(--table-row-odd-bg) !important" },
              },
              "& .MuiInputLabel-root": { color: "var(--text-light-color)" },
              "& .MuiSvgIcon-root": { color: "var(--text-light-color)" },
            }
          }}
          renderInput={(params) => (
            <TextField {...params} label="Integration Type" />
          )}
          onChange={(e, value) => {
            setCurrType(value);
            // Reset integrationParams when changing type to ensure a fresh connection
            setIntegrationParams({});
          }}
        />
      </Box>

      {/* Parameter Section (Card) */}
      <Box
        sx={{
          backgroundColor: "var(--card-background)",
          padding: "25px 30px",
          borderRadius: "var(--border-radius)",
          boxShadow: "0 4px 15px var(--shadow-color)",
          marginBottom: "25px", // Consistent spacing below this card
          border: "1px solid var(--border-color)",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        <Typography variant="h6" component="h2" sx={{ color: "var(--text-color)", fontWeight: "600", marginBottom: "20px" }}>
          Parameters
        </Typography>
        {currType ? (
          <CurrIntegration
            user={user}
            org={org}
            integrationParams={integrationParams}
            setIntegrationParams={setIntegrationParams}
          />
        ) : (
          <Button
            disabled
            variant="contained"
            sx={{
              backgroundColor: "var(--primary-color)",
              color: "#1a202c",
              boxShadow: "0 2px 5px rgba(99, 179, 237, 0.2)",
              borderRadius: "var(--border-radius)",
              padding: "12px 25px",
              fontWeight: "600",
              width: "100%",
              "&:disabled": {
                backgroundColor: "var(--primary-color)",
                color: "rgba(26, 32, 44, 0.6)",
                opacity: 0.7,
                boxShadow: "none",
              }
            }}
          >
            Select Integration Type
          </Button>
        )}
      </Box>

      {/* DataForm section - only render if currType is selected */}
      {currType && (
        <Box
          sx={{
            width: "100%",
            boxSizing: "border-box",
          }}
        >
          <DataForm
            integration={integrationParams}
            setIntegrationParams={setIntegrationParams}
          />
        </Box>
      )}
    </Box>
  );
};
