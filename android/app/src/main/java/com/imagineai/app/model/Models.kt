package com.imagineai.app.model

import com.google.gson.annotations.SerializedName

enum class QualityMode(val apiValue: String, val displayName: String, val stepsHint: String) {
    QUICK("quick", "Quick", "1 step · Fast draft"),
    BALANCED("balanced", "Balanced", "2 steps · Recommended"),
    BEST("best", "Best", "4 steps · Maximum detail")
}

data class GenerateRequest(
    @SerializedName("prompt") val prompt: String,
    @SerializedName("quality_mode") val qualityMode: String = "balanced",
    @SerializedName("resolution") val resolution: Int = 512,
    @SerializedName("seed") val seed: Long? = null
)

data class GenerateResponse(
    @SerializedName("status") val status: String,
    @SerializedName("request_id") val requestId: String? = null,
    @SerializedName("image_url") val imageUrl: String? = null,
    @SerializedName("generation") val generation: GenerationDetails? = null,
    @SerializedName("performance") val performance: PerformanceMetrics? = null,
    @SerializedName("quality") val quality: QualityMetrics? = null,
    @SerializedName("resource_decision") val resourceDecision: ResourceDecision? = null,
    @SerializedName("error") val error: ApiError? = null
)

data class GenerationDetails(
    @SerializedName("model") val model: String,
    @SerializedName("model_revision") val modelRevision: String,
    @SerializedName("precision") val precision: String,
    @SerializedName("scheduler") val scheduler: String,
    @SerializedName("steps") val steps: Int,
    @SerializedName("width") val width: Int,
    @SerializedName("height") val height: Int,
    @SerializedName("seed") val seed: Long
)

data class PerformanceMetrics(
    @SerializedName("model_load_ms") val modelLoadMs: Double? = null,
    @SerializedName("prompt_encode_ms") val promptEncodeMs: Double? = null,
    @SerializedName("denoise_ms") val denoiseMs: Double? = null,
    @SerializedName("decode_ms") val decodeMs: Double? = null,
    @SerializedName("cv_ms") val cvMs: Double? = null,
    @SerializedName("end_to_end_ms") val endToEndMs: Double? = null,
    @SerializedName("peak_gpu_mb") val peakGpuMb: Double? = null,
    @SerializedName("peak_process_ram_mb") val peakProcessRamMb: Double? = null
)

data class QualityMetrics(
    @SerializedName("clip_score") val clipScore: Double? = null,
    @SerializedName("sharpness") val sharpness: Double? = null,
    @SerializedName("brightness") val brightness: Double? = null,
    @SerializedName("contrast") val contrast: Double? = null,
    @SerializedName("artifact_flags") val artifactFlags: List<String>? = null
)

data class ResourceDecision(
    @SerializedName("fallback_used") val fallbackUsed: Boolean = false,
    @SerializedName("reason") val reason: String? = null,
    @SerializedName("explanation") val explanation: String? = null
)

data class ApiError(
    @SerializedName("code") val code: String,
    @SerializedName("message") val message: String,
    @SerializedName("retryable") val retryable: Boolean = false,
    @SerializedName("suggested_action") val suggestedAction: String? = null
)

data class ErrorResponse(
    @SerializedName("status") val status: String,
    @SerializedName("request_id") val requestId: String? = null,
    @SerializedName("error") val error: ApiError
)

data class CapabilitiesResponse(
    @SerializedName("api_version") val apiVersion: String,
    @SerializedName("quality_modes") val qualityModes: List<String>,
    @SerializedName("min_resolution") val minResolution: Int,
    @SerializedName("max_resolution") val maxResolution: Int,
    @SerializedName("generation_available") val generationAvailable: Boolean,
    @SerializedName("deployment_mode") val deploymentMode: String
)

data class HealthResponse(
    @SerializedName("status") val status: String,
    @SerializedName("api_version") val apiVersion: String
)
