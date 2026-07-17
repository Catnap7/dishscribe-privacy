# DishScribe privacy and support site

Standalone, dependency-free privacy and support page for `DishScribe: Recipe Keeper` (`com.evmodu.dishscribe`). English is the default; Korean and Spanish are available through the in-page language switcher or `?lang=ko` / `?lang=es`.

## Signed-release reconciliation

This page was reconciled on July 17, 2026 with signed package `com.evmodu.dishscribe`, version `1.0.0 (1)`. The release evidence verifies all of the following:

- no `android.permission.INTERNET`;
- no advertising, analytics, account, camera, microphone, location, contacts, notification, or broad storage/media permission;
- Android Photo Picker is the only recipe-photo selection route;
- Storage Access Framework is used only for user-initiated ZIP backup and restore;
- selected photos and recipe data are stored in app-private local storage;
- Android OS backup is disabled, and the final backup/data-extraction rules exclude app files, databases, preferences, and external app storage from cloud backup and device transfer.

Evidence anchors:

- signed APK SHA-256: `9cf45428336d3f789ebfd5db1428becfb1888c8d7cbb5a74773e969a2c80cd9e`;
- signed AAB SHA-256: `48ce05e0f344dbb27c5366c7ffa8a624aeae76750bd81ecd0ea0cf7714ca9b32`;
- APK signature scheme v2 verified with one signer;
- merged-manifest permission and backup audit generated on July 17, 2026.

If a later signed build changes any of these properties, update the public copy before that release.

## Local review

Open `index.html` directly in a browser and review all three language panels at phone and desktop widths. The page has no external assets, analytics, cookies, or build step.
