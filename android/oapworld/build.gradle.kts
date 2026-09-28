plugins {
    id("com.android.application")
}

android {
    namespace = "com.onanypostcode.oapworld"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.onanypostcode.oapworld"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
        }
    }
}

dependencies {
    implementation("androidx.activity:activity:1.10.1")
    implementation("androidx.webkit:webkit:1.12.1")
}
