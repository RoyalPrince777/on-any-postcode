package com.onanypostcode.oapworld;

/**
 * Founder-private camera data boundary.
 *
 * This policy describes what OAP itself may retain; it cannot control metadata
 * or processing performed by a separate Android camera application.
 * No camera capture, face identification, or cloud upload is enabled here.
 */
public final class OapCameraPrivacyPolicy {
    private OapCameraPrivacyPolicy() {}

    public enum DataClass {
        OWNER_APPROVED_PHOTO,
        OWNER_APPROVED_METADATA,
        OWNER_APPROVED_ANALYSIS,
        THIRD_PARTY_BIOMETRIC,
        THIRD_PARTY_IDENTITY_PROFILE,
        BACKGROUND_LOCATION,
        UNCONSENTED_CLOUD_COPY
    }

    /** Explicit owner approval is required even for owner-specific data. */
    public static boolean mayPersist(DataClass type, boolean ownerApproved) {
        if (!ownerApproved || type == null) return false;
        switch (type) {
            case OWNER_APPROVED_PHOTO:
            case OWNER_APPROVED_METADATA:
            case OWNER_APPROVED_ANALYSIS:
                return true;
            default:
                return false;
        }
    }

    /** No automatic transmission of camera data from the OAP camera pipeline. */
    public static boolean mayAutomaticallyUpload(DataClass type) {
        return false;
    }

    /** Third-party identity/biometric profiles are never part of owner memory. */
    public static boolean mayAddToOwnerMemory(DataClass type, boolean ownerApproved) {
        return ownerApproved && type == DataClass.OWNER_APPROVED_ANALYSIS;
    }
}
