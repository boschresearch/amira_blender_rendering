# Running Tests

ABR relies on the standard unittest python framework. 
Multiple tests are already implemented in order to ensure a minimal code coverage.

However, since some tests need to load Blender's python API (bpy), it is not possible
to use the standard *discover* option for unittests.

To overcome this we provide a dedicated script. For ABR root directory, you just need to run

```bash
./scripts/run_tests --abr-path ~/amira_blender_rendering
```

## Implementing your own tests

In case you directly contribute to ABR, it is of course possible (and recommended) 
to implement additional tests. To do that you need to:

1. Locate (or create a new one) the most suitable directory in $ABR/tests where to put your test files
2. Implement your tests according the standard unittest framework. You can take inspiration from existing tests
3. Similar to existing tests, add your own to `tests.__main__::import_and_run_implemented_tests`

Afterwards you can run tests as above expalined.

