plugins {
    id("com.android.application")
}

android {
    namespace = "com.onanypostcode.oapworld"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.onanypostcode.oaphome"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1-founder"
    }
    sourceSets {
        getByName("main") {
            java.srcDirs("../oapworld/src/main/java")
            res.srcDirs("../oapworld/src/main/res")
        }
    }
}

dependencies {
    implementation("androidx.activity:activity:1.10.1")
    implementation("androidx.webkit:webkit:1.12.1")
}
