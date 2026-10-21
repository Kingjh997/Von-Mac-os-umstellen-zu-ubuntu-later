TARGET := iphone:clang:16.5:15.0
ARCHS = arm64

include $(THEOS)/makefiles/common.mk

APPLICATION_NAME = TapSprint
TapSprint_FILES = main.m
TapSprint_FRAMEWORKS = UIKit
TapSprint_CFLAGS = -fobjc-arc
TapSprint_BUNDLE_ID = com.kingjh.tapsprint
TapSprint_INFO_PLIST = Info.plist

include $(THEOS_MAKE_PATH)/application.mk
