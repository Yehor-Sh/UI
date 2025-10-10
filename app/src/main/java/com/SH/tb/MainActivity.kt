package com.SH.tb

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.SH.tb.ui.theme.TBTheme
import com.SH.tb.ui.trades.TradesApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            TBTheme {
                TradesApp()
            }
        }
    }
}
