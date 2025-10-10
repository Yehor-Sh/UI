package com.SH.tb.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColorScheme = darkColorScheme(
    primary = AccentBlue,
    onPrimary = Color.White,
    secondary = NeutralGray,
    onSecondary = Color.White,
    tertiary = PositiveGreen,
    background = DarkBackground,
    onBackground = TextPrimary,
    surface = DarkSurface,
    onSurface = TextPrimary,
    surfaceVariant = DarkSurfaceVariant,
    onSurfaceVariant = TextSecondary,
    outline = OutlineDark,
    outlineVariant = OutlineVariantDark,
    error = NegativeRed,
    scrim = Color(0x990F1116)
)

private val LightColorScheme = lightColorScheme(
    primary = AccentBlue,
    onPrimary = Color.White,
    secondary = NeutralGray,
    onSecondary = Color.White,
    tertiary = PositiveGreen,
    background = LightBackground,
    onBackground = Color(0xFF10131A),
    surface = LightSurface,
    onSurface = Color(0xFF10131A),
    surfaceVariant = LightSurfaceVariant,
    onSurfaceVariant = Color(0xFF4C5367),
    outline = LightOutline,
    outlineVariant = LightOutlineVariant,
    error = NegativeRed,
    scrim = Color(0x550F1116)
)

@Composable
fun TBTheme(
    darkTheme: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
