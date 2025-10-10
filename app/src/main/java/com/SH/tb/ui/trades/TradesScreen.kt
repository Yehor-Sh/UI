package com.SH.tb.ui.trades

import android.content.res.Configuration
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.weight
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Article
import androidx.compose.material.icons.outlined.Cancel
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.History
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Menu
import androidx.compose.material.icons.outlined.MoreVert
import androidx.compose.material.icons.outlined.NotificationsNone
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.NavigationDrawerItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SheetDefaults
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.TopAppBarScrollBehavior
import androidx.compose.material3.rememberDrawerState
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.SH.tb.ui.theme.NegativeRed
import com.SH.tb.ui.theme.NeutralGray
import com.SH.tb.ui.theme.PositiveGreen
import com.SH.tb.ui.theme.TBTheme
import com.SH.tb.ui.theme.WarningOrange
import kotlinx.coroutines.launch
import java.time.LocalDateTime
import java.time.Month
import java.time.format.DateTimeFormatter
import java.util.Locale

private val dateFormatter: DateTimeFormatter =
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm", Locale("ru", "RU"))

enum class DrawerDestination(val title: String, val icon: ImageVector) {
    Home("Главная", Icons.Outlined.Home),
    History("История", Icons.Outlined.History),
    Settings("Настройки", Icons.Outlined.Settings),
    Notifications("Уведомления", Icons.Outlined.NotificationsNone)
}

enum class TradeAction(val title: String, val icon: ImageVector, val feedback: String) {
    Refresh("Обновить", Icons.Outlined.Refresh, "Обновление запущено"),
    CloseAll("Закрыть все", Icons.Outlined.Cancel, "Команда на закрытие отправлена"),
    Settings("Настройки", Icons.Outlined.Settings, "Открываем настройки"),
    Logs("Логи", Icons.Outlined.Article, "Открываем журнал событий")
}

enum class DealState(val label: String, val accent: Color) {
    Active("Активна", PositiveGreen),
    Watch("Под наблюдением", WarningOrange),
    Flat("В ожидании", NeutralGray)
}

data class PortfolioStatus(
    val title: String,
    val description: String? = null,
    val isActive: Boolean = true
)

data class Trade(
    val id: Int,
    val symbol: String,
    val quote: String,
    val entryPrice: Double,
    val currentPrice: Double,
    val changePercent: Double,
    val entryTime: LocalDateTime,
    val strategy: String,
    val stopLoss: Double,
    val takeProfit: Double,
    val status: DealState
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TradesApp(modifier: Modifier = Modifier) {
    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val coroutineScope = rememberCoroutineScope()
    var currentDestination by remember { mutableStateOf(DrawerDestination.Home) }
    val snackbarHostState = remember { SnackbarHostState() }
    val trades = remember { sampleTrades() }
    var selectedTrade by remember { mutableStateOf<Trade?>(null) }
    val bottomSheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    val hideSheet: () -> Unit = {
        coroutineScope.launch {
            bottomSheetState.hide()
        }.invokeOnCompletion {
            if (!bottomSheetState.isVisible) {
                selectedTrade = null
            }
        }
    }

    LaunchedEffect(selectedTrade) {
        if (selectedTrade != null && !bottomSheetState.isVisible) {
            bottomSheetState.show()
        }
    }

    ModalNavigationDrawer(
        drawerState = drawerState,
        scrimColor = MaterialTheme.colorScheme.scrim,
        drawerContent = {
            TradesDrawer(
                current = currentDestination,
                onDestinationSelected = { destination ->
                    currentDestination = destination
                    coroutineScope.launch { drawerState.close() }
                }
            )
        }
    ) {
        TradesScreen(
            trades = trades,
            status = PortfolioStatus(
                title = "Работает",
                description = "Автоматическая стратегия активна",
                isActive = true
            ),
            onTradeClick = { trade -> selectedTrade = trade },
            onMenuClick = { coroutineScope.launch { drawerState.open() } },
            onAction = { action ->
                coroutineScope.launch {
                    snackbarHostState.showSnackbar(action.feedback)
                }
            },
            snackbarHostState = snackbarHostState,
            modifier = modifier
        )
    }

    selectedTrade?.let { trade ->
        ModalBottomSheet(
            sheetState = bottomSheetState,
            onDismissRequest = hideSheet,
            dragHandle = {
                SheetDefaults.DragHandle(color = MaterialTheme.colorScheme.outlineVariant)
            },
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
            tonalElevation = 8.dp
        ) {
            TradeDetailsSheet(
                trade = trade,
                onClose = hideSheet,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TradesScreen(
    trades: List<Trade>,
    status: PortfolioStatus,
    onTradeClick: (Trade) -> Unit,
    onMenuClick: () -> Unit,
    onAction: (TradeAction) -> Unit,
    snackbarHostState: SnackbarHostState,
    modifier: Modifier = Modifier
) {
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior()

    Scaffold(
        modifier = modifier
            .fillMaxSize()
            .nestedScroll(scrollBehavior.nestedScrollConnection),
        containerColor = MaterialTheme.colorScheme.background,
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) },
        topBar = {
            TradesTopBar(
                onMenuClick = onMenuClick,
                onMoreClick = { onAction(TradeAction.Logs) },
                scrollBehavior = scrollBehavior
            )
        },
        bottomBar = {
            TradesBottomBar(onAction = onAction)
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 20.dp)
        ) {
            StatusBanner(status = status)
            Spacer(modifier = Modifier.height(20.dp))
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                contentPadding = PaddingValues(bottom = 120.dp)
            ) {
                items(trades, key = { it.id }) { trade ->
                    TradeCard(
                        trade = trade,
                        onClick = { onTradeClick(trade) }
                    )
                }
            }
        }
    }
}

@Composable
private fun TradesTopBar(
    onMenuClick: () -> Unit,
    onMoreClick: () -> Unit,
    scrollBehavior: TopAppBarScrollBehavior
) {
    androidx.compose.material3.CenterAlignedTopAppBar(
        title = {
            Text(
                text = "Сделки",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onSurface
            )
        },
        navigationIcon = {
            IconButton(onClick = onMenuClick) {
                Icon(imageVector = Icons.Outlined.Menu, contentDescription = "Открыть меню")
            }
        },
        actions = {
            IconButton(onClick = onMoreClick) {
                Icon(imageVector = Icons.Outlined.MoreVert, contentDescription = "Дополнительно")
            }
        },
        colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
            containerColor = MaterialTheme.colorScheme.background,
            navigationIconContentColor = MaterialTheme.colorScheme.onSurface,
            titleContentColor = MaterialTheme.colorScheme.onSurface,
            actionIconContentColor = MaterialTheme.colorScheme.onSurface
        ),
        scrollBehavior = scrollBehavior
    )
}

@Composable
private fun TradesBottomBar(onAction: (TradeAction) -> Unit) {
    Surface(
        tonalElevation = 6.dp,
        shadowElevation = 6.dp,
        color = MaterialTheme.colorScheme.surface
    ) {
        Column {
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.4f))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TradeAction.entries.forEach { action ->
                    val isPrimary = action == TradeAction.Refresh
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .clickable { onAction(action) }
                            .padding(vertical = 6.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(
                            imageVector = action.icon,
                            contentDescription = action.title,
                            tint = if (isPrimary) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = action.title,
                            style = MaterialTheme.typography.labelMedium,
                            color = if (isPrimary) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusBanner(status: PortfolioStatus, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        tonalElevation = 4.dp,
        color = MaterialTheme.colorScheme.surfaceVariant
    ) {
        Column(modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .background(
                            color = if (status.isActive) PositiveGreen else WarningOrange,
                            shape = CircleShape
                        )
                )
                Spacer(modifier = Modifier.width(12.dp))
                Text(
                    text = status.title,
                    style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.Medium),
                    color = MaterialTheme.colorScheme.onSurface
                )
            }
            status.description?.takeIf { it.isNotBlank() }?.let { description ->
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TradeCard(trade: Trade, onClick: () -> Unit, modifier: Modifier = Modifier) {
    val changeColor = when {
        trade.changePercent > 0 -> PositiveGreen
        trade.changePercent < 0 -> NegativeRed
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }

    Card(
        modifier = modifier.fillMaxWidth(),
        onClick = onClick,
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Row(modifier = Modifier.padding(horizontal = 18.dp, vertical = 20.dp)) {
            Box(
                modifier = Modifier
                    .width(6.dp)
                    .height(72.dp)
                    .background(color = changeColor, shape = RoundedCornerShape(12.dp))
            )
            Spacer(modifier = Modifier.width(18.dp))
            Column(modifier = Modifier.weight(1f)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "${trade.symbol}/${trade.quote}",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold),
                        color = MaterialTheme.colorScheme.onSurface,
                        modifier = Modifier.weight(1f)
                    )
                    Text(
                        text = formatPercent(trade.changePercent),
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold),
                        color = changeColor
                    )
                }
                Spacer(modifier = Modifier.height(14.dp))
                Row(modifier = Modifier.fillMaxWidth()) {
                    PriceColumn(title = "Вход:", value = trade.entryPrice)
                    Spacer(modifier = Modifier.weight(1f))
                    PriceColumn(title = "Текущая:", value = trade.currentPrice, alignEnd = true)
                }
            }
        }
    }
}

@Composable
private fun PriceColumn(title: String, value: Double, alignEnd: Boolean = false) {
    Column(
        horizontalAlignment = if (alignEnd) Alignment.End else Alignment.Start
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = formatPrice(value),
            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Medium),
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
private fun TradesDrawer(
    current: DrawerDestination,
    onDestinationSelected: (DrawerDestination) -> Unit,
    modifier: Modifier = Modifier
) {
    ModalDrawerSheet(
        modifier = modifier,
        drawerShape = RoundedCornerShape(topEnd = 28.dp, bottomEnd = 28.dp),
        drawerContainerColor = MaterialTheme.colorScheme.surface
    ) {
        Spacer(modifier = Modifier.height(32.dp))
        Text(
            text = "Навигация",
            modifier = Modifier.padding(horizontal = 24.dp),
            style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Medium),
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(16.dp))
        DrawerDestination.entries.forEach { destination ->
            NavigationDrawerItem(
                icon = {
                    Icon(
                        imageVector = destination.icon,
                        contentDescription = destination.title
                    )
                },
                label = {
                    Text(text = destination.title)
                },
                selected = destination == current,
                onClick = { onDestinationSelected(destination) },
                modifier = Modifier.padding(horizontal = 12.dp),
                shape = RoundedCornerShape(18.dp),
                colors = NavigationDrawerItemDefaults.colors(
                    selectedContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                    selectedTextColor = MaterialTheme.colorScheme.onSurface,
                    selectedIconColor = MaterialTheme.colorScheme.onSurface,
                    unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                    unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant
                )
            )
        }
        Spacer(modifier = Modifier.height(24.dp))
    }
}

@Composable
private fun TradeDetailsSheet(
    trade: Trade,
    onClose: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.padding(horizontal = 24.dp, vertical = 16.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onClose) {
                Icon(imageVector = Icons.Outlined.Close, contentDescription = "Закрыть детали")
            }
            Text(
                text = "Сделка #${trade.id}",
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold),
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier
                    .weight(1f)
                    .padding(horizontal = 8.dp),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.width(48.dp))
        }
        Spacer(modifier = Modifier.height(12.dp))
        Text(
            text = "${trade.symbol}/${trade.quote}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.align(Alignment.CenterHorizontally)
        )
        Spacer(modifier = Modifier.height(20.dp))
        Text(
            text = "Детали сделки",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(12.dp))
        TradeDetailRow(label = "Время входа", value = trade.entryTime.format(dateFormatter))
        TradeDetailRow(label = "Стратегия", value = trade.strategy)
        TradeDetailRow(label = "Стоп-лосс", value = formatPrice(trade.stopLoss))
        TradeDetailRow(label = "Тейк-профит", value = formatPrice(trade.takeProfit))
        Spacer(modifier = Modifier.height(20.dp))
        Text(
            text = "Текущий статус",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(12.dp))
        StatusChip(status = trade.status)
        Spacer(modifier = Modifier.height(12.dp))
    }
}

@Composable
private fun StatusChip(status: DealState, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(24.dp),
        color = status.accent.copy(alpha = 0.15f),
        tonalElevation = 0.dp,
        shadowElevation = 0.dp
    ) {
        Text(
            text = status.label,
            modifier = Modifier.padding(horizontal = 18.dp, vertical = 10.dp),
            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Medium),
            color = status.accent
        )
    }
}

@Composable
private fun TradeDetailRow(label: String, value: String) {
    Column(modifier = Modifier.padding(vertical = 6.dp)) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = value,
            style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.Medium),
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

private fun formatPrice(value: Double): String {
    return String.format(Locale("ru", "RU"), "%1$,.2f", value)
}

private fun formatPercent(change: Double): String {
    return String.format(Locale("ru", "RU"), "%+.2f%%", change)
}

private fun sampleTrades(): List<Trade> {
    return listOf(
        Trade(
            id = 12345,
            symbol = "BTC",
            quote = "USDT",
            entryPrice = 45_000.0,
            currentPrice = 46_102.5,
            changePercent = 2.45,
            entryTime = LocalDateTime.of(2024, Month.JULY, 26, 14, 30),
            strategy = "Пробой уровня",
            stopLoss = 44_000.0,
            takeProfit = 47_000.0,
            status = DealState.Active
        ),
        Trade(
            id = 12346,
            symbol = "ETH",
            quote = "USDT",
            entryPrice = 3_200.0,
            currentPrice = 3_163.2,
            changePercent = -1.15,
            entryTime = LocalDateTime.of(2024, Month.JULY, 25, 10, 45),
            strategy = "Отбой от уровня",
            stopLoss = 3_120.0,
            takeProfit = 3_360.0,
            status = DealState.Watch
        ),
        Trade(
            id = 12347,
            symbol = "ADA",
            quote = "USDT",
            entryPrice = 1.25,
            currentPrice = 1.25,
            changePercent = 0.0,
            entryTime = LocalDateTime.of(2024, Month.JULY, 24, 18, 5),
            strategy = "Диапазон",
            stopLoss = 1.18,
            takeProfit = 1.34,
            status = DealState.Flat
        )
    )
}

@Preview(name = "Trades", showSystemUi = true, uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun TradesScreenPreview() {
    TBTheme {
        val snackbarHostState = remember { SnackbarHostState() }
        TradesScreen(
            trades = sampleTrades(),
            status = PortfolioStatus(
                title = "Работает",
                description = "Автоматическая стратегия активна",
                isActive = true
            ),
            onTradeClick = {},
            onMenuClick = {},
            onAction = {},
            snackbarHostState = snackbarHostState
        )
    }
}
