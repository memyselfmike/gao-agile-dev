# Build GAO-Dev Package

Build the GAO-Dev wheel package locally using the build script.

## Instructions

1. Run the build script: `bash scripts/build.sh`
2. Show the user:
   - Build output and status
   - Generated wheel filename and location
   - File size of the built package
   - Whether twine validation passed

## Notes

- The build script performs: clean, build wheel, validate with twine
- Uses setuptools-scm for dynamic versioning from git tags
- Output is in `dist/` directory
