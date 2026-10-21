# TapSprint

A small original UIKit game: tap the moving target as many times as possible in 30 seconds.

This source is used to test whether the Ubuntu Theos cross-toolchain can compile an iOS app and package the result as an IPA. It uses the pinned public iPhoneOS 16.5 Theos SDK and targets ARM64/iOS 15+.

The resulting IPA is an unsigned build artifact. It is not ready to install on a stock iPhone until it is signed with a valid certificate and provisioning profile. No Xcode/macOS runner or copied Apple SDK is used.

The same source is checked by separate GitHub Actions workflows on Ubuntu 22.04 and Ubuntu 26.04. Both workflows package an unsigned IPA artifact.
