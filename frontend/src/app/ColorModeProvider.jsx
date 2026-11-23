import { createContext, useContext, useMemo, useState } from "react";
import { CssBaseline, ThemeProvider } from "@mui/material";
import createAppTheme from "./theme.js";

const ColorModeContext = createContext(null);

export function useColorMode() {
  const context = useContext(ColorModeContext);

  if (!context) {
    throw new Error("useColorMode must be used inside ColorModeProvider");
  }

  return context;
}

function getSavedMode() {
  try {
    const savedMode = window.localStorage.getItem("aerosecure-theme");
    return savedMode === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export default function ColorModeProvider({ children }) {
  const [mode, setMode] = useState(getSavedMode);

  function toggleColorMode() {
    setMode((currentMode) => {
      const nextMode = currentMode === "light" ? "dark" : "light";

      try {
        window.localStorage.setItem("aerosecure-theme", nextMode);
      } catch {
        // The theme still switches if browser storage is unavailable.
      }

      return nextMode;
    });
  }

  const theme = useMemo(() => createAppTheme(mode), [mode]);
  const contextValue = useMemo(
    () => ({ mode, toggleColorMode }),
    [mode],
  );

  return (
    <ColorModeContext.Provider value={contextValue}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}