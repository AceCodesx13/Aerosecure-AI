import { useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  AppBar,
  Box,
  Drawer,
  FormControl,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import ListAltOutlinedIcon from "@mui/icons-material/ListAltOutlined";
import TimelineOutlinedIcon from "@mui/icons-material/TimelineOutlined";
import BuildOutlinedIcon from "@mui/icons-material/BuildOutlined";
import Brightness4OutlinedIcon from "@mui/icons-material/Brightness4Outlined";
import Brightness7OutlinedIcon from "@mui/icons-material/Brightness7Outlined";
import { useColorMode } from "./ColorModeProvider.jsx";

const drawerWidth = 248;
const sidebarBackground = "#102438";

const pages = [
  { label: "Orders", path: "/orders", icon: <ListAltOutlinedIcon /> },
  { label: "Prediction", path: "/prediction", icon: <TimelineOutlinedIcon /> },
  {
    label: "Supplier Recommendation",
    path: "/supplier-recommendation",
    icon: <BuildOutlinedIcon />,
  },
];

export default function AppLayout() {
  const [role, setRole] = useState("student");
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const { mode, toggleColorMode } = useColorMode();

  const currentPage =
    pages.find((page) => page.path === location.pathname) ?? pages[0];

  function goToPage(path) {
    navigate(path);
    setMobileOpen(false);
  }

  const navigation = (
    <Box
      component="nav"
      aria-label="Main navigation"
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        color: "#ffffff",
        background: `radial-gradient(
          circle at bottom right,
          rgba(22, 140, 140, 0.32),
          transparent 52%
        ), ${sidebarBackground}`,
      }}
    >
    <Toolbar sx={{ minHeight: 76, px: 2.5 }}>
      <Typography
        component="div"
        sx={{
          color: "#ffffff",
          fontSize: 20,
          fontWeight: 800,
          letterSpacing: "-0.035em",
          lineHeight: 1,
        }}
      >
        AeroSecure
        <Box
          component="span"
          sx={{
            ml: 0.75,
            color: "#8ce0d1",
            fontWeight: 700,
            letterSpacing: "0.01em",
          }}
        >
          AI
        </Box>
      </Typography>
    </Toolbar>

      <Typography
        variant="overline"
        sx={{ px: 2.5, pt: 2, color: "rgba(255,255,255,0.52)" }}
      >
        Workspace
      </Typography>

      <List sx={{ px: 1.5, pt: 1 }}>
        {pages.map((page) => {
          const selected = location.pathname === page.path;

          return (
            <ListItemButton
              key={page.path}
              selected={selected}
              onClick={() => goToPage(page.path)}
              sx={{
                mb: 0.5,
                minHeight: 46,
                borderRadius: 2,
                color: selected ? "#ffffff" : "rgba(255,255,255,0.76)",
                "& .MuiListItemIcon-root": {
                  minWidth: 38,
                  color: selected ? "#8ce0d1" : "rgba(255,255,255,0.62)",
                },
                "&.Mui-selected": {
                  backgroundColor: "rgba(140,224,209,0.14)",
                },
                "&.Mui-selected:hover": {
                  backgroundColor: "rgba(140,224,209,0.2)",
                },
                "&:hover": {
                  backgroundColor: "rgba(255,255,255,0.08)",
                },
              }}
            >
              <ListItemIcon>{page.icon}</ListItemIcon>
              <ListItemText
                primary={page.label}
                primaryTypographyProps={{ fontSize: 14, fontWeight: 600 }}
              />
            </ListItemButton>
          );
        })}
      </List>

      <Box
        sx={{
          mt: "auto",
          p: 1.5,
          borderTop: "1px solid rgba(255,255,255,0.12)",
        }}
      >
        <IconButton
          onClick={toggleColorMode}
          aria-label={mode === "light" ? "Switch to dark theme" : "Switch to light theme"}
          title={mode === "light" ? "Switch to dark theme" : "Switch to light theme"}
          sx={{
            width: 46,
            height: 46,
            borderRadius: 2,
            color: "#8ce0d1",
            "&:hover": {
              backgroundColor: "rgba(255,255,255,0.08)",
            },
          }}
        >
          {mode === "light" ? (
            <Brightness4OutlinedIcon />
          ) : (
            <Brightness7OutlinedIcon />
          )}
        </IconButton>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ minHeight: "100vh", display: "flex" }}>
      <Drawer
        variant={isDesktop ? "permanent" : "temporary"}
        open={isDesktop || mobileOpen}
        onClose={() => setMobileOpen(false)}
        sx={{
          width: isDesktop ? drawerWidth : undefined,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            border: 0,
            backgroundColor: sidebarBackground,
            color: "#ffffff",
          },
        }}
      >
        {navigation}
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          ml: isDesktop ? `${drawerWidth}px` : 0,
        }}
      >
        <AppBar
          position="sticky"
          color="inherit"
          elevation={0}
          sx={{
            borderBottom: 1,
            borderColor: "divider",
            backgroundColor:
              mode === "dark"
                ? "rgba(24,36,49,0.92)"
                : "rgba(255,255,255,0.92)",
            backdropFilter: "blur(10px)",
          }}
        >
          <Toolbar sx={{ minHeight: 72, gap: 2 }}>
            {!isDesktop && (
              <IconButton
                edge="start"
                aria-label="Open navigation"
                onClick={() => setMobileOpen(true)}
              >
                <MenuIcon />
              </IconButton>
            )}

            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="body2" color="text.secondary">
                AeroSecure AI / Workspace
              </Typography>
              <Typography variant="subtitle1" fontWeight={700}>
                {currentPage.label}
              </Typography>
            </Box>

            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ display: { xs: "none", sm: "block" } }}
            >
              View as
            </Typography>

            <FormControl size="small" sx={{ minWidth: 130 }}>
              <Select
                value={role}
                onChange={(event) => setRole(event.target.value)}
                inputProps={{ "aria-label": "Select user role" }}
                sx={{ bgcolor: "background.paper" }}
              >
                <MenuItem value="student">Student</MenuItem>
                <MenuItem value="mentor">Mentor</MenuItem>
                <MenuItem value="administrator">Admin</MenuItem>
              </Select>
            </FormControl>
          </Toolbar>
        </AppBar>

        <Box sx={{ px: { xs: 2, sm: 3, lg: 4 }, py: { xs: 3, md: 4 } }}>
          <Outlet context={{ role }} />
        </Box>
      </Box>
    </Box>
  );
}