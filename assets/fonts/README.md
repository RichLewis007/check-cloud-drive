# Fonts Directory

**Author:** Rich Lewis - @RichLewis007

This directory contains bundled font files for the application.

## Font File

- `AtkinsonHyperlegibleMono.zip` - Contains the AtkynsonMono Nerd Font Propo font family used throughout the application.

## How It Works

The application automatically loads fonts from this zip file at startup if the font is not already installed on the system. This ensures the application displays correctly even if users don't have the Nerd Font installed.

The font loading is handled by `src/check_cloud_drives/fonts.py` and is called automatically when the application starts.

## Font Variants Loaded

- AtkynsonMonoNerdFontPropo-Regular.otf (primary)
- AtkynsonMonoNerdFontPropo-Bold.otf
- AtkynsonMonoNerdFontPropo-Italic.otf
- AtkynsonMonoNerdFontPropo-BoldItalic.otf
- AtkynsonMonoNerdFontPropo-Medium.otf

## Note

This font file is included in the package distribution so users don't need to install it separately.

