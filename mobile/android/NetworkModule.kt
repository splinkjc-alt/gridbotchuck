// Grid Trading Bot - Hilt Dependency Injection Module
// Copy to: app/src/main/java/com/gridbot/di/NetworkModule.kt

package com.gridbot.di

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.gridbot.data.api.GridBotApiService
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    private const val PREFS_NAME = "grid_bot_prefs"
    private const val KEY_BOT_URL = "bot_url"
    private const val DEFAULT_URL = "http://192.168.1.100:8080/api/"

    @Provides
    @Singleton
    fun provideSharedPreferences(
        @ApplicationContext context: Context
    ): SharedPreferences {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    @Provides
    @Singleton
    fun provideGson(): Gson {
        return GsonBuilder()
            .setLenient()
            .create()
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        gson: Gson,
        sharedPreferences: SharedPreferences
    ): Retrofit {
        val baseUrl = sharedPreferences.getString(KEY_BOT_URL, DEFAULT_URL) ?: DEFAULT_URL

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
    }

    @Provides
    @Singleton
    fun provideGridBotApiService(retrofit: Retrofit): GridBotApiService {
        return retrofit.create(GridBotApiService::class.java)
    }
}

// ============== URL Manager ==============
// Use this to update the bot URL at runtime

class BotConnectionManager(
    private val sharedPreferences: SharedPreferences
) {
    companion object {
        private const val KEY_BOT_URL = "bot_url"
        private const val KEY_BOT_HOST = "bot_host"
        private const val KEY_BOT_PORT = "bot_port"
    }

    fun saveConnection(host: String, port: Int = 8080) {
        val url = "http://$host:$port/api/"
        sharedPreferences.edit()
            .putString(KEY_BOT_URL, url)
            .putString(KEY_BOT_HOST, host)
            .putInt(KEY_BOT_PORT, port)
            .apply()
    }

    fun getHost(): String {
        return sharedPreferences.getString(KEY_BOT_HOST, "192.168.1.100") ?: "192.168.1.100"
    }

    fun getPort(): Int {
        return sharedPreferences.getInt(KEY_BOT_PORT, 8080)
    }

    fun getBaseUrl(): String {
        return sharedPreferences.getString(KEY_BOT_URL, "http://192.168.1.100:8080/api/")
            ?: "http://192.168.1.100:8080/api/"
    }
}
