# Prebuilt OAP World APK from a separately verified Android build.
# Place the verified artifact at vendor/oap/prebuilt/OapWorld.apk.
LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := OapWorld
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_SRC_FILES := prebuilt/OapWorld.apk
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_PRIVILEGED_MODULE := false
include $(BUILD_PREBUILT)
