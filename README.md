# WordCraft Android Enhanced

Workspace for improving the Android port of WordCraft while keeping the original projects untouched.

## Sources

- Android port: https://github.com/kanaaka/wordcraft-android
- Upstream WordCraft: https://github.com/storytold/wordcraft
- Android port package: `ai.storyteller.wordcraft`
- Target ABI: `arm64-v8a`

## Build workflow

The GitHub Actions workflow checks out the Android port and its pinned upstream WordCraft source, assembles the Android workspace, builds the APK, verifies the package/ABI/signature, and publishes the APK as a workflow artifact.

Run it from **Actions → Build Android APK → Run workflow**.

The APK produced by CI is a test/sideload build. Until a persistent signing key is configured, separate CI runs may use different signing identities; installing a later build over an earlier one may require uninstalling the previous build first. Do not uninstall the existing app until its documents/data are backed up.

## Planned enhancement work

1. Preserve Kanaaka's Android modifier-key handling and existing Android-specific behavior.
2. Improve Android document open/save integration, prioritizing Google Drive and Storage Access Framework.
3. Verify Word-style formatting shortcuts on an actual Android keyboard.
4. Run source and APK verification before sharing any build.

No changes are made to either source repository by this workspace.
