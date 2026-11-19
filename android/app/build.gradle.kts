plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

val configuredApiBaseUrl = providers.gradleProperty("API_BASE_URL")
    .orElse(providers.environmentVariable("API_BASE_URL"))
    .orNull
val debugApiBaseUrl = configuredApiBaseUrl ?: "http://10.0.2.2:8000/api/"
val releaseApiBaseUrl = configuredApiBaseUrl
    ?: "https://configure-api-before-release.invalid/api/"

val verifyReleaseApiUrl = tasks.register("verifyReleaseApiUrl") {
    inputs.property("apiBaseUrl", configuredApiBaseUrl ?: "")
    doLast {
        val apiUrl = inputs.properties["apiBaseUrl"] as String
        if (apiUrl.isBlank()) {
            throw GradleException(
                "Define API_BASE_URL con la URL HTTPS de producción antes de compilar release."
            )
        }
        val apiHost = apiUrl
            .removePrefix("https://")
            .substringBefore('/')
        if (
            !apiUrl.startsWith("https://") ||
            apiHost.isBlank() ||
            !apiUrl.endsWith("/api/")
        ) {
            throw GradleException(
                "API_BASE_URL debe ser una URL HTTPS válida y terminar en /api/."
            )
        }
    }
}

tasks.configureEach {
    if (name.contains("Release") && name != "verifyReleaseApiUrl") {
        dependsOn(verifyReleaseApiUrl)
    }
}

android {
    namespace = "com.example.canaldedenunciasgsi"
    compileSdk {
        version = release(37)
    }

    defaultConfig {
        applicationId = "com.example.canaldedenunciasgsi"
        minSdk = 24
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "API_BASE_URL", "\"$debugApiBaseUrl\"")
    }

    buildTypes {
        debug {
            manifestPlaceholders["allowCleartextTraffic"] = "true"
        }
        release {
            buildConfigField("String", "API_BASE_URL", "\"$releaseApiBaseUrl\"")
            manifestPlaceholders["allowCleartextTraffic"] = "false"
            optimization {
                enable = false
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons.core)
    implementation(libs.androidx.compose.material.icons.extended)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.print)
    implementation(libs.zxing.core)
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.gson)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging.interceptor)
    implementation(libs.gson)
    testImplementation(libs.junit)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.tooling)
}
