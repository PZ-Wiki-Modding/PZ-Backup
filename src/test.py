import sv_ttk

print("Current theme:", sv_ttk.get_theme())
print("\nTrying use_dark_theme():")
sv_ttk.use_dark_theme()
print("Theme after use_dark_theme():", sv_ttk.get_theme())