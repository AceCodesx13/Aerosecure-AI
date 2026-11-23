import { createTheme } from "@mui/material/styles";

export default function createAppTheme(mode) {
  const isDark = mode === "dark";

  return createTheme({
    palette: {
      mode,
      primary: isDark
        ? { main: "#8dbbdb", dark: "#51809d", contrastText: "#10202e" }
        : { main: "#17324d", dark: "#102438", contrastText: "#ffffff" },
      secondary: {
        main: isDark ? "#65c9bc" : "#168c8c",
        light: isDark ? "#1c3b3d" : "#e7f5f3",
      },
      background: {
        default: isDark ? "#101820" : "#f4f7fb",
        paper: isDark ? "#182431" : "#ffffff",
      },
      text: {
        primary: isDark ? "#e7edf3" : "#172b3f",
        secondary: isDark ? "#aab7c4" : "#647487",
      },
      divider: isDark ? "#344554" : "#e3e9f0",
      success: { main: isDark ? "#69c69a" : "#23835b" },
      warning: { main: isDark ? "#f0b65c" : "#a96608" },
      error: { main: isDark ? "#ed8585" : "#b54747" },
    },
    shape: {
      borderRadius: 12,
    },
    typography: {
      fontFamily: "Inter, system-ui, sans-serif",
      h4: { fontWeight: 700, letterSpacing: "-0.03em" },
      h5: { fontWeight: 700, letterSpacing: "-0.02em" },
      h6: { fontWeight: 700 },
      button: { fontWeight: 600, textTransform: "none" },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: isDark ? "#101820" : "#f4f7fb",
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: { borderRadius: 9, boxShadow: "none" },
        },
      },
      MuiPaper: {
        styleOverrides: {
          outlined: {
            borderColor: isDark ? "#344554" : "#e3e9f0",
          },
        },
      },
      MuiDataGrid: {
        styleOverrides: {
          root: {
            border: 0,
            "& .MuiDataGrid-columnHeaders": {
              backgroundColor: isDark ? "#1d2b38" : "#f7f9fc",
              borderBottom: `1px solid ${isDark ? "#344554" : "#e3e9f0"}`,
            },
            "& .MuiDataGrid-row:hover": {
              backgroundColor: isDark ? "#20313f" : "#f6fafb",
            },
          },
        },
      },
      MuiInputBase: {
        styleOverrides: {
            input: {
            "&[type='number']": {
                colorScheme: mode,
            },
            },
        },
        },
    },
  });
}