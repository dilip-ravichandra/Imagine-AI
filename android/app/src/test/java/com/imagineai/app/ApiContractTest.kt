package com.imagineai.app

import com.google.gson.Gson
import com.imagineai.app.model.ErrorResponse
import com.imagineai.app.model.GenerateResponse
import org.junit.Assert.*
import org.junit.Test

class ApiContractTest {

    private val gson = Gson()

    @Test
    fun testParseRealSuccessResponse() {
        val json = """
        {
          "status": "success",
          "request_id": "d40d7d32d94e48fcb84ab0cfcf19aff1",
          "image_url": "http://10.0.2.2:8000/images/d40d7d32d94e48fcb84ab0cfcf19aff1.png",
          "generation": {
            "model": "stabilityai/sd-turbo",
            "model_revision": "b261bac6fd2cf515557d5d0707481eafa0485ec2",
            "precision": "fp16",
            "scheduler": "EulerDiscreteScheduler(timestep_spacing=trailing)",
            "steps": 2,
            "width": 512,
            "height": 512,
            "seed": 42
          },
          "performance": {
            "model_load_ms": 306163.88,
            "prompt_encode_ms": null,
            "denoise_ms": null,
            "decode_ms": null,
            "cv_ms": null,
            "end_to_end_ms": 323.82,
            "peak_gpu_mb": 3097.61,
            "peak_process_ram_mb": 2547.38
          },
          "quality": null,
          "resource_decision": {
            "fallback_used": false,
            "reason": null,
            "explanation": "balanced mode -> 2 step(s) at 512x512."
          }
        }
        """.trimIndent()

        val resp = gson.fromJson(json, GenerateResponse::class.java)
        assertEquals("success", resp.status)
        assertEquals("d40d7d32d94e48fcb84ab0cfcf19aff1", resp.requestId)
        assertEquals("http://10.0.2.2:8000/images/d40d7d32d94e48fcb84ab0cfcf19aff1.png", resp.imageUrl)

        assertNotNull(resp.generation)
        assertEquals("stabilityai/sd-turbo", resp.generation!!.model)
        assertEquals("fp16", resp.generation!!.precision)
        assertEquals(2, resp.generation!!.steps)
        assertEquals(512, resp.generation!!.width)
        assertEquals(42L, resp.generation!!.seed)

        assertNotNull(resp.performance)
        assertEquals(323.82, resp.performance!!.endToEndMs!!, 0.01)
        assertEquals(3097.61, resp.performance!!.peakGpuMb!!, 0.01)
        assertNull(resp.performance!!.promptEncodeMs)

        assertNotNull(resp.resourceDecision)
        assertFalse(resp.resourceDecision!!.fallbackUsed)
        assertEquals("balanced mode -> 2 step(s) at 512x512.", resp.resourceDecision!!.explanation)
    }

    @Test
    fun testParseErrorResponse_InvalidRequest() {
        val json = """
        {
          "status": "error",
          "request_id": null,
          "error": {
            "code": "INVALID_REQUEST",
            "message": "Request failed validation.",
            "retryable": false,
            "suggested_action": "Check prompt (1-500 chars), quality_mode (quick|balanced|best), resolution (256-1024), seed."
          }
        }
        """.trimIndent()

        val resp = gson.fromJson(json, ErrorResponse::class.java)
        assertEquals("error", resp.status)
        assertEquals("INVALID_REQUEST", resp.error.code)
        assertFalse(resp.error.retryable)
        assertTrue(resp.error.suggestedAction!!.contains("Check prompt"))
    }

    @Test
    fun testParseErrorResponse_ResourceExhausted() {
        val json = """
        {
          "status": "error",
          "request_id": "abc123def456",
          "error": {
            "code": "RESOURCE_EXHAUSTED",
            "message": "Out of GPU memory.",
            "retryable": true,
            "suggested_action": "Try a lower resolution or quick mode."
          }
        }
        """.trimIndent()

        val resp = gson.fromJson(json, ErrorResponse::class.java)
        assertEquals("error", resp.status)
        assertEquals("abc123def456", resp.requestId)
        assertEquals("RESOURCE_EXHAUSTED", resp.error.code)
        assertTrue(resp.error.retryable)
    }

    @Test
    fun testParseErrorResponse_Unauthorized() {
        val json = """
        {
          "status": "error",
          "error": {
            "code": "UNAUTHORIZED",
            "message": "A valid API key is required.",
            "retryable": false,
            "suggested_action": "Send the server's API key in the X-API-Key header."
          }
        }
        """.trimIndent()

        val resp = gson.fromJson(json, ErrorResponse::class.java)
        assertEquals("error", resp.status)
        assertEquals("UNAUTHORIZED", resp.error.code)
        assertFalse(resp.error.retryable)
    }
}
