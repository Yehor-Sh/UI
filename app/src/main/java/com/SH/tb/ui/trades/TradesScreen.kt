package com.SH.tb.ui.trades

import android.content.res.Configuration
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Assessment
import androidx.compose.material.icons.outlined.BarChart
import androidx.compose.material.icons.outlined.Cancel
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.History
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Menu
import androidx.compose.material.icons.outlined.MoreVert
import androidx.compose.material.icons.outlined.NotificationsNone
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.ElevatedSuggestionChip
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
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
import java.time.format.FormatStyle
import java.util.Locale
import kotlin.math.abs

private val dateFormatter =
    DateTimeFormatter.ofLocalizedDateTime(FormatStyle.MEDIUM).withLocale(Locale("ru", "RU"))

private enum class DrawerDestination(val title: String, val icon: ImageVector) {
    Home("Рабочий стол", Icons.Outlined.Home),
    History("История", Icons.Outlined.History),
    Analytics("Аналитика", Icons.Outlined.BarChart),
    Notifications("Уведомления", Icons.Outlined.NotificationsNone),
    Settings("Настройки", Icons.Outlined.Settings)
}

enum class TradeAction(val label: String, val icon: ImageVector, val feedback: String) {
    Resume("Продолжить", Icons.Outlined.PlayArrow, "Алгоритм запущен"),
    PauseAll("Пауза", Icons.Outlined.Cancel, "Все сделки поставлены на паузу"),
    Journal("Журнал", Icons.Outlined.Assessment, "Открыт журнал операций")
}

enum class TradeFilter(val label: String) {
    Active("Активные"),
    Watch("Наблюдение"),
    Flat("В ожидании")
}

enum class TradeDirection(val label: String, val accent: Color) {
    Long("Лонг", PositiveGreen),
    Short("Шорт", NegativeRed)
}

enum class TradeStatus(val label: String, val accent: Color, val subtitle: String) {
    Running("Исполняется", PositiveGreen, "Сделка под управлением робота"),
    Watching("Наблюдение", WarningOrange, "Ожидаем сигнал к входу"),
    Flat("Без позиции", NeutralGray, "Актив добавлен в лист ожидания")
}

data class DealSummary(
    val balance: String,
    val todayPnL: String,
    val activeStrategies: Int
)

data class Trade(
    val id: Int,
    val symbol: String,
    val quote: String,
    val direction: TradeDirection,
    val volume: Double,
    val entryPrice: Double,
    val currentPrice: Double,
    val takeProfit: Double,
    val stopLoss: Double,
    val pnlPercent: Double,
    val pnlAmount: Double,
    val openedAt: LocalDateTime,
    val status: TradeStatus,
    val progress: Float,
    val strategy: String,
    val exchange: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TradesApp(modifier: Modifier = Modifier) {
    val drawerState = rememberDrawerState(DrawerValue.Closed)
    val coroutineScope = rememberCoroutineScope()
    var currentDestination by remember { mutableStateOf(DrawerDestination.Home) }
    val snackbarHostState = remember { SnackbarHostState() }
    var selectedTrade by remember { mutableStateOf<Trade?>(null) }
    val trades = remember { sampleTrades() }
    val summary = remember { sampleSummary() }
    var selectedFilter by remember { mutableStateOf(TradeFilter.Active) }
    val bottomSheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    val filteredTrades = remember(trades, selectedFilter) {
        when (selectedFilter) {
            TradeFilter.Active -> trades.filter { it.status == TradeStatus.Running }
            TradeFilter.Watch -> trades.filter { it.status == TradeStatus.Watching }
            TradeFilter.Flat -> trades.filter { it.status == TradeStatus.Flat }
        }
    }

    val hideSheet: () -> Unit = {
        coroutineScope.launch { bottomSheetState.hide() }.invokeOnCompletion {
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
            summary = summary,
            trades = filteredTrades,
            filter = selectedFilter,
            onFilterSelected = { selectedFilter = it },
            onTradeClick = { selectedTrade = it },
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
            tonalElevation = 12.dp
        ) {
            TradeDetailsSheet(
                trade = trade,
                onClose = hideSheet,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 24.dp)
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TradesScreen(
    summary: DealSummary,
    trades: List<Trade>,
    filter: TradeFilter,
    onFilterSelected: (TradeFilter) -> Unit,
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
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TradesTopBar(
                onMenuClick = onMenuClick,
                onMoreClick = { onAction(TradeAction.Journal) },
                scrollBehavior = scrollBehavior
            )
        },
        bottomBar = { TradesBottomBar(onAction = onAction) }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            item {
                PortfolioSummaryCard(summary = summary)
            }
            item {
                FilterSection(current = filter, onSelect = onFilterSelected)
            }
            if (trades.isEmpty()) {
                item {
                    EmptyState(filter = filter)
                }
            } else {
                item {
                    SectionHeader(title = "Активные сделки")
                }
                items(trades, key = { it.id }) { trade ->
                    TradeCard(trade = trade, onClick = { onTradeClick(trade) })
                }
                item { Spacer(modifier = Modifier.height(76.dp)) }
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
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "Отслеживание сделок",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Text(
                    text = "Автоматические стратегии",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
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
private fun PortfolioSummaryCard(summary: DealSummary, modifier: Modifier = Modifier) {
    val gradient = Brush.linearGradient(
        colors = listOf(
            MaterialTheme.colorScheme.primary.copy(alpha = 0.9f),
            MaterialTheme.colorScheme.primary.copy(alpha = 0.6f)
        )
    )

    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(28.dp),
        tonalElevation = 8.dp,
        color = MaterialTheme.colorScheme.surface
    ) {
        Column(
            modifier = Modifier
                .background(gradient, shape = RoundedCornerShape(28.dp))
                .padding(horizontal = 24.dp, vertical = 22.dp)
        ) {
            Text(
                text = "Баланс",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.8f)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = summary.balance,
                style = MaterialTheme.typography.headlineSmall.copy(fontWeight = FontWeight.SemiBold),
                color = MaterialTheme.colorScheme.onPrimary
            )
            Spacer(modifier = Modifier.height(16.dp))
            Row(
                horizontalArrangement = Arrangement.spacedBy(18.dp)
            ) {
                SummaryStat(
                    title = "P&L за день",
                    value = summary.todayPnL,
                    accent = PositiveGreen
                )
                SummaryStat(
                    title = "Стратегий активно",
                    value = summary.activeStrategies.toString(),
                    accent = MaterialTheme.colorScheme.onPrimary
                )
            }
        }
    }
}

@Composable
private fun SummaryStat(title: String, value: String, accent: Color, modifier: Modifier = Modifier) {
    Column(modifier = modifier) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.75f)
        )
        Spacer(modifier = Modifier.height(6.dp))
        Text(
            text = value,
            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Medium),
            color = accent
        )
    }
}

@Composable
private fun FilterSection(
    current: TradeFilter,
    onSelect: (TradeFilter) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier.fillMaxWidth()) {
        SectionHeader(title = "Фильтр по статусу")
        Spacer(modifier = Modifier.height(12.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            TradeFilter.entries.forEach { filter ->
                val selected = filter == current
                FilterChip(
                    selected = selected,
                    onClick = { onSelect(filter) },
                    label = {
                        Text(
                            text = filter.label,
                            style = MaterialTheme.typography.labelLarge
                        )
                    },
                    shape = RoundedCornerShape(24.dp),
                    colors = androidx.compose.material3.FilterChipDefaults.filterChipColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                        selectedContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                        labelColor = MaterialTheme.colorScheme.onSurface,
                        selectedLabelColor = MaterialTheme.colorScheme.onSurface,
                        leadingIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                        selectedLeadingIconColor = MaterialTheme.colorScheme.onSurface
                    ),
                    leadingIcon = {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .clip(CircleShape)
                                .background(filter.toStatus().accent)
                        )
                    }
                )
            }
        }
    }
}

private fun TradeFilter.toStatus(): TradeStatus = when (this) {
    TradeFilter.Active -> TradeStatus.Running
    TradeFilter.Watch -> TradeStatus.Watching
    TradeFilter.Flat -> TradeStatus.Flat
}

@Composable
private fun SectionHeader(title: String) {
    Text(
        text = title,
        style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Medium),
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
}

@Composable
private fun TradeCard(trade: Trade, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .wrapContentHeight(),
        onClick = onClick,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        shape = RoundedCornerShape(26.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(modifier = Modifier.padding(horizontal = 22.dp, vertical = 20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape)
                        .background(trade.direction.accent.copy(alpha = 0.18f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = trade.direction.label.first().toString(),
                        style = MaterialTheme.typography.titleMedium,
                        color = trade.direction.accent,
                        fontWeight = FontWeight.SemiBold
                    )
                }
                Spacer(modifier = Modifier.width(16.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "${trade.symbol}/${trade.quote}",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold),
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = "${trade.exchange} · ${trade.strategy}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
                StatusTag(status = trade.status)
            }
            Spacer(modifier = Modifier.height(18.dp))
            Row(
                horizontalArrangement = Arrangement.spacedBy(18.dp)
            ) {
                PriceColumn(title = "Вход", value = trade.entryPrice)
                PriceColumn(title = "Текущая", value = trade.currentPrice)
                PriceColumn(title = "Объём", value = trade.volume, isPrice = false)
            }
            Spacer(modifier = Modifier.height(18.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                PnlBadge(amount = trade.pnlAmount, percent = trade.pnlPercent)
                Spacer(modifier = Modifier.width(16.dp))
                ProgressIndicator(progress = trade.progress, modifier = Modifier.weight(1f))
            }
            Spacer(modifier = Modifier.height(14.dp))
            Text(
                text = "Открыта ${trade.openedAt.format(dateFormatter)}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun StatusTag(status: TradeStatus) {
    Surface(
        shape = CutCornerShape(topStart = 12.dp, bottomEnd = 12.dp),
        color = status.accent.copy(alpha = 0.16f),
        tonalElevation = 0.dp,
        shadowElevation = 0.dp
    ) {
        Text(
            text = status.label,
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
            style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Medium),
            color = status.accent
        )
    }
}

@Composable
private fun PriceColumn(title: String, value: Double, isPrice: Boolean = true) {
    Column(modifier = Modifier.weight(1f)) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = if (isPrice) formatPrice(value) else formatVolume(value),
            style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.Medium),
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
private fun PnlBadge(amount: Double, percent: Double) {
    val positive = amount >= 0
    val tint = if (positive) PositiveGreen else NegativeRed
    Surface(
        shape = RoundedCornerShape(18.dp),
        color = tint.copy(alpha = 0.16f)
    ) {
        Text(
            text = "${formatSigned(amount)} (${formatPercent(percent)})",
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
            style = MaterialTheme.typography.labelLarge,
            color = tint,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
private fun ProgressIndicator(progress: Float, modifier: Modifier = Modifier) {
    androidx.compose.material3.LinearProgressIndicator(
        progress = { progress.coerceIn(0f, 1f) },
        modifier = modifier
            .height(8.dp)
            .clip(RoundedCornerShape(8.dp)),
        color = MaterialTheme.colorScheme.primary,
        trackColor = MaterialTheme.colorScheme.surfaceVariant
    )
}

@Composable
private fun EmptyState(filter: TradeFilter) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 32.dp),
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 26.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(52.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.surfaceVariant),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.NotificationsNone,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Нет сделок",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "В категории \"${filter.label}\" пока пусто. Попробуйте выбрать другой фильтр или запустить новую стратегию.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TradesBottomBar(onAction: (TradeAction) -> Unit) {
    Surface(
        tonalElevation = 8.dp,
        shadowElevation = 8.dp,
        color = MaterialTheme.colorScheme.surface
    ) {
        Column {
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.35f))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 14.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                ElevatedSuggestionChip(
                    onClick = { onAction(TradeAction.Resume) },
                    label = {
                        Text(
                            text = TradeAction.Resume.label,
                            style = MaterialTheme.typography.labelLarge
                        )
                    },
                    icon = {
                        Icon(
                            imageVector = TradeAction.Resume.icon,
                            contentDescription = null
                        )
                    }
                )
                androidx.compose.material3.FilledTonalButton(
                    onClick = { onAction(TradeAction.PauseAll) },
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.filledTonalButtonColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant
                    )
                ) {
                    Icon(
                        imageVector = TradeAction.PauseAll.icon,
                        contentDescription = null
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(text = TradeAction.PauseAll.label)
                }
                androidx.compose.material3.OutlinedButton(onClick = { onAction(TradeAction.Journal) }) {
                    Icon(
                        imageVector = TradeAction.Journal.icon,
                        contentDescription = null
                    )
                }
            }
        }
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
                label = { Text(text = destination.title) },
                selected = destination == current,
                onClick = { onDestinationSelected(destination) },
                modifier = Modifier.padding(horizontal = 12.dp),
                shape = RoundedCornerShape(18.dp),
                colors = NavigationDrawerItemDefaults.colors(
                    selectedContainerColor = MaterialTheme.colorScheme.surfaceVariant,
                    selectedIconColor = MaterialTheme.colorScheme.onSurface,
                    selectedTextColor = MaterialTheme.colorScheme.onSurface,
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
        modifier = modifier.padding(horizontal = 24.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onClose) {
                Icon(imageVector = Icons.Outlined.Close, contentDescription = "Закрыть")
            }
            Text(
                text = "${trade.symbol}/${trade.quote}",
                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.SemiBold),
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.weight(1f),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.width(48.dp))
        }
        Spacer(modifier = Modifier.height(18.dp))
        StatusInfo(status = trade.status)
        Spacer(modifier = Modifier.height(18.dp))
        DetailGrid(trade = trade)
        Spacer(modifier = Modifier.height(22.dp))
        Text(
            text = "Комментарий стратегии",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "${trade.strategy} · ${trade.exchange}",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Открыта ${trade.openedAt.format(dateFormatter)}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(12.dp))
    }
}

@Composable
private fun StatusInfo(status: TradeStatus) {
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = status.accent.copy(alpha = 0.12f),
        tonalElevation = 0.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(12.dp)
                    .clip(CircleShape)
                    .background(status.accent)
            )
            Spacer(modifier = Modifier.width(14.dp))
            Column {
                Text(
                    text = status.label,
                    style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Medium),
                    color = status.accent
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = status.subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun DetailGrid(trade: Trade) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            DetailCard(title = "P&L", value = formatSigned(trade.pnlAmount))
            DetailCard(title = "P&L %", value = formatPercent(trade.pnlPercent))
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            DetailCard(title = "Стоп-лосс", value = formatPrice(trade.stopLoss))
            DetailCard(title = "Тейк-профит", value = formatPrice(trade.takeProfit))
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            DetailCard(title = "Объём", value = formatVolume(trade.volume))
            DetailCard(title = "Прогресс", value = "${(trade.progress * 100).toInt()}%")
        }
    }
}

@Composable
private fun DetailCard(title: String, value: String) {
    Surface(
        modifier = Modifier
            .weight(1f)
            .aspectRatio(1.7f),
        shape = RoundedCornerShape(20.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 18.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = value,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.Medium
            )
        }
    }
}

private fun formatPrice(value: Double): String {
    return String.format(Locale("ru", "RU"), "%1$,.2f", value)
}

private fun formatVolume(value: Double): String {
    return String.format(Locale("ru", "RU"), "%1$,.3f", value)
}

private fun formatPercent(value: Double): String {
    return String.format(Locale("ru", "RU"), "%+.2f%%", value)
}

private fun formatSigned(value: Double): String {
    val sign = if (value >= 0) "+" else "-"
    return "$sign${String.format(Locale("ru", "RU"), "%1$,.2f", abs(value))}"
}

private fun sampleSummary(): DealSummary {
    return DealSummary(balance = "₽ 4 820 000", todayPnL = "+₽ 42 150", activeStrategies = 5)
}

private fun sampleTrades(): List<Trade> {
    return listOf(
        Trade(
            id = 1,
            symbol = "BTC",
            quote = "USDT",
            direction = TradeDirection.Long,
            volume = 0.85,
            entryPrice = 62_450.0,
            currentPrice = 63_915.4,
            takeProfit = 65_200.0,
            stopLoss = 60_800.0,
            pnlPercent = 2.34,
            pnlAmount = 3_875.0,
            openedAt = LocalDateTime.of(2024, Month.JULY, 26, 9, 15),
            status = TradeStatus.Running,
            progress = 0.62f,
            strategy = "Пробой уровня",
            exchange = "Binance"
        ),
        Trade(
            id = 2,
            symbol = "ETH",
            quote = "USDT",
            direction = TradeDirection.Long,
            volume = 5.4,
            entryPrice = 3_210.0,
            currentPrice = 3_156.2,
            takeProfit = 3_420.0,
            stopLoss = 3_080.0,
            pnlPercent = -1.68,
            pnlAmount = -291.5,
            openedAt = LocalDateTime.of(2024, Month.JULY, 25, 14, 40),
            status = TradeStatus.Watching,
            progress = 0.38f,
            strategy = "Диапазон",
            exchange = "Bybit"
        ),
        Trade(
            id = 3,
            symbol = "SOL",
            quote = "USDT",
            direction = TradeDirection.Short,
            volume = 120.0,
            entryPrice = 148.5,
            currentPrice = 147.9,
            takeProfit = 140.0,
            stopLoss = 152.0,
            pnlPercent = 0.42,
            pnlAmount = 72.8,
            openedAt = LocalDateTime.of(2024, Month.JULY, 24, 22, 5),
            status = TradeStatus.Running,
            progress = 0.47f,
            strategy = "Импульс",
            exchange = "OKX"
        ),
        Trade(
            id = 4,
            symbol = "ADA",
            quote = "USDT",
            direction = TradeDirection.Long,
            volume = 2_400.0,
            entryPrice = 0.58,
            currentPrice = 0.58,
            takeProfit = 0.66,
            stopLoss = 0.54,
            pnlPercent = 0.0,
            pnlAmount = 0.0,
            openedAt = LocalDateTime.of(2024, Month.JULY, 23, 19, 25),
            status = TradeStatus.Flat,
            progress = 0.21f,
            strategy = "Среднее по рынку",
            exchange = "Binance"
        )
    )
}

@Preview(name = "TradesScreen", showSystemUi = true, uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun TradesScreenPreview() {
    TBTheme {
        val snackbarHostState = remember { SnackbarHostState() }
        TradesScreen(
            summary = sampleSummary(),
            trades = sampleTrades(),
            filter = TradeFilter.Active,
            onFilterSelected = {},
            onTradeClick = {},
            onMenuClick = {},
            onAction = {},
            snackbarHostState = snackbarHostState
        )
    }
}
