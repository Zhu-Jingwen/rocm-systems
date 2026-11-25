# gfx1201 counter validation

The unit contract checks each raw selector and derived expression against the
pinned SDK definition. Dependency checks prevent restoring an expression
without its inputs. These checks establish configuration consistency, not
every selector's physical hardware semantics.

## Automated checks

The Python contract is registered as `test_sdk_config` in CMake and the
existing test categories. It has 121 historical/additional selector,
uniqueness and dependency cases.

```sh
PYTHONPATH=projects/rocprofiler-compute/src python -m pytest -q \
  projects/rocprofiler-compute/tests/unit/rocprof_compute_soc/profile_configs/test_sdk_config.py
```

## Prior GEMM controls

Local BF16 GEMM controls collected all configured metrics on two gfx1201 cards.
The controls used shapes 24576x16x4096 and 32768x4096x256, 100 cold and
200 measured dispatches per metric and case, with cache flush disabled.
Raw/sum and derived-expression identities verify the collection path.
Nonzero observations alone do not identify a selector's physical event.

## References

- [Code PR #16491](https://github.com/ROCm/rocm-systems/pull/16491).
- [Historical SDK contract](https://github.com/ROCm/rocm-systems/blob/e92aa6ee8c01f991c9da08ea386330a6374e0f4a/projects/rocprofiler-sdk/source/share/rocprofiler-sdk/config.yaml).
