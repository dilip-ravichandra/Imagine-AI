package com.imagineai.app.ui

import android.content.Intent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.imagineai.app.model.GenerationDetails
import com.imagineai.app.model.PerformanceMetrics
import com.imagineai.app.model.QualityMode
import com.imagineai.app.model.ResourceDecision

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ImagineAiScreen(viewModel: ImagineAiViewModel) {
    val state by viewModel.uiState.collectAsState()
    val scrollState = rememberScrollState()
    val context = LocalContext.current

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Imagine AI",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold
                        )
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "Hybrid Server-Side Generation",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            val indicatorColor = when (state.serverAvailable) {
                                true -> Color(0xFF2E7D32)
                                false -> Color(0xFFC62828)
                                null -> Color.Gray
                            }
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .clip(RoundedCornerShape(4.dp))
                                    .background(indicatorColor)
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.toggleConfigDialog(true) }) {
                        Icon(
                            imageVector = Icons.Default.Settings,
                            contentDescription = "Server Settings"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(scrollState)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Prompt Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Prompt",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.SemiBold
                        )
                        Text(
                            text = "${state.prompt.length} / 500",
                            style = MaterialTheme.typography.bodySmall,
                            color = if (state.prompt.length >= 480) MaterialTheme.colorScheme.error else Color.Gray
                        )
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = state.prompt,
                        onValueChange = { viewModel.onPromptChange(it) },
                        modifier = Modifier.fillMaxWidth(),
                        placeholder = { Text("Describe the image you want to create...") },
                        maxLines = 4,
                        trailingIcon = {
                            if (state.prompt.isNotEmpty()) {
                                IconButton(onClick = { viewModel.onPromptChange("") }) {
                                    Icon(Icons.Default.Clear, contentDescription = "Clear Prompt")
                                }
                            }
                        }
                    )
                }
            }

            // Quality Mode Selector
            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Quality Mode",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        QualityMode.values().forEach { mode ->
                            val selected = state.qualityMode == mode
                            FilterChip(
                                selected = selected,
                                onClick = { viewModel.onQualityModeChange(mode) },
                                label = {
                                    Column(modifier = Modifier.padding(vertical = 4.dp)) {
                                        Text(text = mode.displayName, fontWeight = FontWeight.Bold)
                                        Text(text = mode.stepsHint, fontSize = 10.sp)
                                    }
                                },
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }

            // Advanced Options: Resolution & Seed
            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Resolution & Seed",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Resolution: ${state.resolution}x${state.resolution}",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf(256, 384, 512, 640, 768).forEach { res ->
                            FilterChip(
                                selected = state.resolution == res,
                                onClick = { viewModel.onResolutionChange(res) },
                                label = { Text("${res}px") },
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = state.seedText,
                        onValueChange = { viewModel.onSeedChange(it) },
                        label = { Text("Seed (optional numeric)") },
                        modifier = Modifier.fillMaxWidth(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )
                }
            }

            // Generate Button
            Button(
                onClick = { viewModel.generateImage() },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                enabled = !state.isLoading && state.prompt.isNotBlank()
            ) {
                if (state.isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = MaterialTheme.colorScheme.onPrimary,
                        strokeWidth = 2.5.dp
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text("Generating on Laptop GPU...")
                } else {
                    Icon(Icons.Default.AutoAwesome, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Generate Image", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
            }

            // Error Message Banner
            state.errorMessage?.let { msg ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                Icons.Default.Warning,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.error
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = msg,
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onErrorContainer
                            )
                        }
                        state.suggestedAction?.let { action ->
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = action,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onErrorContainer
                            )
                        }
                        if (state.canRetry) {
                            Spacer(modifier = Modifier.height(10.dp))
                            Button(
                                onClick = { viewModel.generateImage() },
                                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                            ) {
                                Icon(Icons.Default.Refresh, contentDescription = null)
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Retry Request")
                            }
                        }
                    }
                }
            }

            // Result Image Card & "How this was generated"
            state.lastResponse?.let { resp ->
                resp.imageUrl?.let { imgUrl ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(
                                text = "Generated Image",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                            Spacer(modifier = Modifier.height(12.dp))
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .aspectRatio(1f)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(Color.Black),
                                contentAlignment = Alignment.Center
                            ) {
                                AsyncImage(
                                    model = ImageRequest.Builder(context)
                                        .data(imgUrl)
                                        .crossfade(true)
                                        .build(),
                                    contentDescription = "Generated image for: ${state.prompt}",
                                    contentScale = ContentScale.Fit,
                                    modifier = Modifier.fillMaxSize()
                                )
                            }
                            Spacer(modifier = Modifier.height(12.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.End
                            ) {
                                OutlinedButton(
                                    onClick = {
                                        val shareIntent = Intent(Intent.ACTION_SEND).apply {
                                            type = "text/plain"
                                            putExtra(Intent.EXTRA_TEXT, "Generated with Imagine AI:\n$imgUrl\nPrompt: ${state.prompt}")
                                        }
                                        context.startActivity(Intent.createChooser(shareIntent, "Share Image Link"))
                                    }
                                ) {
                                    Icon(Icons.Default.Share, contentDescription = null)
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("Share")
                                }
                            }

                            // "How this was generated" Panel
                            Spacer(modifier = Modifier.height(16.dp))
                            Divider()
                            Spacer(modifier = Modifier.height(12.dp))
                            GenerationInspectionPanel(
                                details = resp.generation,
                                perf = resp.performance,
                                decision = resp.resourceDecision
                            )
                        }
                    }
                }
            }
        }
    }

    // Server Configuration Dialog
    if (state.showConfigDialog) {
        var tempUrl by remember { mutableStateOf(state.serverBaseUrl) }
        AlertDialog(
            onDismissRequest = { viewModel.toggleConfigDialog(false) },
            title = { Text("Server Configuration") },
            text = {
                Column {
                    Text(
                        "Set backend server URL (must end with /):",
                        style = MaterialTheme.typography.bodySmall
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = tempUrl,
                        onValueChange = { tempUrl = it },
                        label = { Text("Base URL") },
                        singleLine = true
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "• Android Emulator: http://10.0.2.2:8000/\n• Physical Phone: http://<laptop LAN IP>:8000/",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.Gray
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.onBaseUrlChange(tempUrl)
                        viewModel.toggleConfigDialog(false)
                    }
                ) {
                    Text("Save & Connect")
                }
            },
            dismissButton = {
                TextButton(onClick = { viewModel.toggleConfigDialog(false) }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
fun GenerationInspectionPanel(
    details: GenerationDetails?,
    perf: PerformanceMetrics?,
    decision: ResourceDecision?
) {
    var expanded by remember { mutableStateOf(true) }

    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "How this was generated",
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.Bold
            )
            TextButton(onClick = { expanded = !expanded }) {
                Text(if (expanded) "Hide Details" else "Show Details")
            }
        }

        AnimatedVisibility(visible = expanded) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                details?.let {
                    InspectionRow("Model", it.model)
                    InspectionRow("Revision", it.modelRevision)
                    InspectionRow("Precision", it.precision)
                    InspectionRow("Steps", "${it.steps} step(s)")
                    InspectionRow("Resolution", "${it.width} x ${it.height}")
                    InspectionRow("Seed", it.seed.toString())
                }
                perf?.let {
                    it.endToEndMs?.let { ms ->
                        InspectionRow("Latency", "%.1f ms".format(ms))
                    }
                    it.peakGpuMb?.let { gpu ->
                        InspectionRow("Peak GPU VRAM", "%.1f MB".format(gpu))
                    }
                    it.peakProcessRamMb?.let { ram ->
                        InspectionRow("Peak Server RAM", "%.1f MB".format(ram))
                    }
                }
                decision?.let { dec ->
                    InspectionRow("Fallback Used", if (dec.fallbackUsed) "Yes (${dec.reason})" else "No")
                    dec.explanation?.let { exp ->
                        InspectionRow("Decision", exp)
                    }
                }
            }
        }
    }
}

@Composable
private fun InspectionRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodySmall,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Normal
        )
    }
}
