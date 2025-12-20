# Grid Trading Bot - Android Mobile App

## 📱 Overview

This folder contains the specification and starter code for building an Android companion app for the Grid Trading Bot.

## 📁 Files

| File | Description |
|------|-------------|
| `API_QUICK_REFERENCE.md` | API endpoints cheat sheet |
| `android/DataModels.kt` | Kotlin data classes for API responses |
| `android/GridBotApiService.kt` | Retrofit API interface |
| `android/BotRepository.kt` | Repository pattern with polling |
| `android/DashboardViewModel.kt` | MVVM ViewModel |
| `android/DashboardScreen.kt` | Jetpack Compose UI |
| `android/NetworkModule.kt` | Hilt dependency injection |

## 🚀 Quick Start

### 1. Create New Android Project
- Open Android Studio
- New Project → Empty Compose Activity
- Name: `GridTradingBot`
- Package: `com.gridbot`
- Min SDK: 26 (Android 8.0)

### 2. Add Dependencies
Add to `app/build.gradle.kts`:

```kotlin
dependencies {
    // Compose (already included)
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    
    // Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // Hilt DI
    implementation("com.google.dagger:hilt-android:2.48")
    kapt("com.google.dagger:hilt-compiler:2.48")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")
    
    // Lifecycle
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")
}
```

### 3. Copy Kotlin Files
Copy all `.kt` files from `android/` folder to your project:
- `DataModels.kt` → `app/src/main/java/com/gridbot/data/models/`
- `GridBotApiService.kt` → `app/src/main/java/com/gridbot/data/api/`
- `BotRepository.kt` → `app/src/main/java/com/gridbot/data/repository/`
- `NetworkModule.kt` → `app/src/main/java/com/gridbot/di/`
- `DashboardViewModel.kt` → `app/src/main/java/com/gridbot/ui/dashboard/`
- `DashboardScreen.kt` → `app/src/main/java/com/gridbot/ui/dashboard/`

### 4. Configure Hilt
Add to `Application` class:
```kotlin
@HiltAndroidApp
class GridBotApp : Application()
```

Add to `MainActivity`:
```kotlin
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            GridBotTheme {
                DashboardScreen()
            }
        }
    }
}
```

### 5. Add Permissions
In `AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### 6. Run
1. Make sure bot is running on your computer
2. Get your computer's IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
3. Update the IP in `NetworkModule.kt`
4. Run the app on your phone (same WiFi network)

## 🔗 Connection

The app connects to the bot's REST API:
- **Default URL**: `http://192.168.1.100:8080/api/`
- **Protocol**: HTTP (no HTTPS for local network)
- **Port**: 8080 (configurable in bot's config.json)

### Finding Your Bot's IP
On the computer running the bot:
```powershell
# Windows
ipconfig | Select-String IPv4

# Output example:
# IPv4 Address. . . . . . . . . . : 192.168.1.100
```

## 📋 Features

### MVP (Minimum Viable Product)
- ✅ Connect to bot via IP address
- ✅ View bot status (running/stopped/paused)
- ✅ View P&L (profit/loss)
- ✅ Start/Stop/Pause/Resume controls
- ✅ View active orders
- ✅ MTF signal indicator

### Coming Soon
- 📊 Market Scanner
- 📈 Price charts
- 🔔 Push notifications
- ⚙️ Configuration editor

## 🎨 UI Design

The app uses Material 3 (Material You) with:
- Dark/Light theme support
- Dynamic color theming
- Card-based layout
- Status badges with color coding:
  - 🟢 Green: Running, Ideal, Profit
  - 🟡 Orange: Paused, Caution
  - 🔴 Red: Stopped, Avoid, Loss

## 🔒 Security Notes

1. **No API keys stored in app** - Exchange credentials stay on the bot server
2. **Local network only** - App works on same WiFi as bot
3. **No sensitive data transmitted** - Only trading status and controls

## 📖 Full Documentation

See `../MOBILE_APP_SPEC.md` for complete API documentation and architecture details.
