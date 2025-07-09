# Changelog

All notable changes to PRISM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-04

### 🎉 Major Release - Complete Platform Redesign

#### Added
- **🏭 Smart Manufacturing Hub** - New unified interface for program generation
- **📋 Template Manager** - Advanced template creation and management system
- **📊 Multi-format Support** - Full support for SDTM, ADaM datasets and TLF reports
- **🔧 Advanced Template Engine** - Dynamic variable substitution with {{VARIABLE}} syntax
- **📱 Modern UI/UX** - Complete redesign with iOS-style interface
- **💾 Local Template Storage** - Secure local storage for custom templates
- **🔄 Batch Processing** - Support for multiple worksheets and bulk program generation
- **📁 ZIP Package Generation** - Automatic packaging of generated programs
- **🎯 Production & Validation Support** - Separate workflows for different program types

#### Enhanced
- **Excel Processing** - Improved Excel file parsing with better error handling
- **Data Preview** - Enhanced data visualization with sortable tables
- **Code Generation** - More sophisticated SAS code generation with proper formatting
- **Template Variables** - Extended variable system supporting timestamps and metadata
- **Performance** - Optimized file processing and generation speed

#### Technical Improvements
- **Vue 3 Migration** - Complete migration to Vue 3 with Composition API
- **TypeScript Support** - Full TypeScript implementation for better type safety
- **Vite Build System** - Modern build tooling for faster development
- **Pinia State Management** - Replaced Vuex with Pinia for better performance
- **Component Architecture** - Modular component design for maintainability

#### Built-in Templates
- **ADaM Production Template** - Standard template for ADaM dataset programs
- **ADaM Validation Template** - QC template for ADaM validation programs
- **SDTM Production Template** - Standard template for SDTM dataset programs
- **SDTM Validation Template** - QC template for SDTM validation programs
- **TLF Development Template** - Template for Table/Listing/Figure programs
- **TLF Validation Template** - QC template for TLF validation programs

### Breaking Changes
- **Legacy Interface Removed** - Previous version interface is no longer supported
- **New File Format** - Template storage format has been updated
- **API Changes** - Internal APIs have been restructured

### Migration Guide
Users upgrading from version 1.x should:
1. Export existing templates before upgrading
2. Re-import templates using the new Template Manager
3. Update Excel metadata files to use new column naming conventions

### System Requirements
- **Node.js** >= 18.0.0
- **Modern Browser** (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- **Memory** >= 4GB RAM recommended for large Excel files

---

## [1.x] - Legacy Versions

Previous versions are no longer supported. Please upgrade to 2.0.0 for the latest features and security updates.
