-- ==============================================================================
-- Hyprland Window Rules for Qutebrowser (Omarchy Linux)
-- Adds terminal-matching 0.90 window opacity
-- ==============================================================================

o.window("([oO]rg\\.[qQ]utebrowser\\.[qQ]utebrowser|[qQ]utebrowser)", {
  tag = "-default-opacity",
  opacity = "0.90 0.85",
})
