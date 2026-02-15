# Archived: WASM Portal Experiment

This directory contains the abandoned DuckDB-WASM portal implementation.

## Why it was archived

1. **Browser compatibility issues**: DuckDB-WASM had initialization problems in Safari
2. **Complexity**: TypeScript/Vite/WASM stack was too heavy for the project scope
3. **Better alternatives**: A simpler Python-based web service (Flask/NiceGUI) would be more appropriate

## Files

- `app.ts` - TypeScript application code
- `index.html` - HTML entry point
- `style.css` - Academic-style CSS
- `package.json`, `tsconfig.json`, `vite.config.ts` - Build configuration

## Future direction

For the prism-portal project, consider:
1. **Flask + Jinja2**: Simple server-side rendering
2. **NiceGUI/Streamlit**: Python-native UI frameworks
3. **Pre-generated JSON + vanilla JS**: No build step needed

## Reference

- DuckDB-WASM docs: https://shell.duckdb.org/docs/
