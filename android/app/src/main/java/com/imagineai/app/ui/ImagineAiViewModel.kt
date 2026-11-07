package com.imagineai.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.imagineai.app.model.GenerateRequest
import com.imagineai.app.model.GenerateResponse
import com.imagineai.app.model.QualityMode
import com.imagineai.app.network.ApiClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.io.IOException

data class UiState(
    val prompt: String = "A red robot beside a blue submarine underwater",
    val qualityMode: QualityMode = QualityMode.BALANCED,
    val resolution: Int = 512,
    val seedText: String = "42",
    val serverBaseUrl: String = ApiClient.baseUrl,
    val isLoading: Boolean = false,
    val isCheckingServer: Boolean = false,
    val serverAvailable: Boolean? = null,
    val lastResponse: GenerateResponse? = null,
    val errorMessage: String? = null,
    val suggestedAction: String? = null,
    val canRetry: Boolean = false,
    val showConfigDialog: Boolean = false
)

class ImagineAiViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    init {
        checkServerHealth()
    }

    fun onPromptChange(newPrompt: String) {
        if (newPrompt.length <= 500) {
            _uiState.update { it.copy(prompt = newPrompt, errorMessage = null) }
        }
    }

    fun onQualityModeChange(mode: QualityMode) {
        _uiState.update { it.copy(qualityMode = mode) }
    }

    fun onResolutionChange(res: Int) {
        _uiState.update { it.copy(resolution = res) }
    }

    fun onSeedChange(seed: String) {
        if (seed.isEmpty() || seed.all { it.isDigit() }) {
            _uiState.update { it.copy(seedText = seed) }
        }
    }

    fun onBaseUrlChange(url: String) {
        ApiClient.baseUrl = url
        _uiState.update { it.copy(serverBaseUrl = ApiClient.baseUrl) }
        checkServerHealth()
    }

    fun toggleConfigDialog(show: Boolean) {
        _uiState.update { it.copy(showConfigDialog = show) }
    }

    fun checkServerHealth() {
        viewModelScope.launch {
            _uiState.update { it.copy(isCheckingServer = true) }
            try {
                val resp = ApiClient.getApi().health()
                val ok = resp.status.equals("ok", ignoreCase = true)
                _uiState.update { it.copy(serverAvailable = ok, isCheckingServer = false) }
            } catch (_: Exception) {
                _uiState.update { it.copy(serverAvailable = false, isCheckingServer = false) }
            }
        }
    }

    fun generateImage() {
        val prompt = _uiState.value.prompt.trim()
        if (prompt.isEmpty()) {
            _uiState.update {
                it.copy(
                    errorMessage = "Prompt cannot be empty.",
                    suggestedAction = "Enter a descriptive text prompt between 1 and 500 characters.",
                    canRetry = false
                )
            }
            return
        }

        val seedValue = _uiState.value.seedText.toLongOrNull()

        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    isLoading = true,
                    errorMessage = null,
                    suggestedAction = null,
                    canRetry = false
                )
            }

            try {
                val req = GenerateRequest(
                    prompt = prompt,
                    qualityMode = _uiState.value.qualityMode.apiValue,
                    resolution = _uiState.value.resolution,
                    seed = seedValue
                )

                val response = ApiClient.getApi().generate(req)
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            lastResponse = body,
                            errorMessage = null,
                            suggestedAction = null,
                            serverAvailable = true
                        )
                    }
                } else {
                    val errorObj = ApiClient.parseErrorBody(response)?.error
                    val message = errorObj?.message ?: "Server returned error code ${response.code()}."
                    val action = errorObj?.suggestedAction ?: "Check connection and try again."
                    val retryable = errorObj?.retryable ?: (response.code() in listOf(429, 503))

                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = message,
                            suggestedAction = action,
                            canRetry = retryable
                        )
                    }
                }
            } catch (e: IOException) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = "Cannot reach generation server: ${e.localizedMessage ?: "Network error"}",
                        suggestedAction = "Verify your laptop and phone are on the same Wi-Fi, the backend is running at ${ApiClient.baseUrl}, and port 8000 is open.",
                        canRetry = true,
                        serverAvailable = false
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = "Unexpected error: ${e.localizedMessage ?: "Unknown error"}",
                        suggestedAction = "Retry with different parameters.",
                        canRetry = true
                    )
                }
            }
        }
    }
}
