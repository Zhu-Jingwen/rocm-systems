# gfx1201 selector catalog validation

Standalone C11 and C++17 compilation checks the new gfx1201 declarations.
C++ assertions also preserve the existing generic soc24 values. These are
declaration and compatibility checks; they do not certify physical event
semantics or replace IP/RDL review.

```sh
cmake -S projects/aqlprofile/test/selector_catalog -B build-selector-catalog
cmake --build build-selector-catalog
ctest --test-dir build-selector-catalog --output-on-failure
```

Both standalone cases pass. Their source includes the gfx1201 companion
header, and the C++ case also includes the generic soc24 header.

References:
- [Code PR #16491](https://github.com/ROCm/rocm-systems/pull/16491).
- [Generic soc24 baseline](https://github.com/ROCm/rocm-systems/blob/6f441646398273bb16a065a3b3798d95f7a95563/projects/aqlprofile/linux/soc24_enum.h).
