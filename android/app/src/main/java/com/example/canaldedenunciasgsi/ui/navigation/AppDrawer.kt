package com.example.canaldedenunciasgsi.ui.navigation

import androidx.annotation.StringRes
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.HelpOutline
import androidx.compose.material.icons.automirrored.filled.LibraryBooks
import androidx.compose.material.icons.automirrored.filled.MenuBook
import androidx.compose.material.icons.automirrored.outlined.HelpOutline
import androidx.compose.material.icons.automirrored.outlined.LibraryBooks
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.filled.Campaign
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.outlined.Campaign
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.NavigationDrawerItemDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.ui.components.AppLogo
import com.example.canaldedenunciasgsi.ui.components.FloatingCircles
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul285
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiAzulClaro
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisBorde
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisTexto

/**
 * Elemento del menú lateral.
 *
 * Cada sección usa dos variantes del mismo icono: relleno cuando está
 * seleccionada y de contorno cuando no, lo que facilita identificar la sección
 * activa y da un acabado más cuidado.
 */
data class DrawerItem(
    @param:StringRes val labelRes: Int,
    val route: String,
    val icon: ImageVector,
    val iconSelected: ImageVector
)

/** Secciones disponibles en la app. Cada icono representa la acción de su sección. */
val drawerItems = listOf(
    DrawerItem(
        R.string.nav_home,
        Destinations.HOME,
        Icons.Outlined.Home,
        Icons.Filled.Home
    ),
    DrawerItem(
        R.string.nav_report,
        Destinations.REPORT,
        Icons.Outlined.Campaign,
        Icons.Filled.Campaign
    ),
    DrawerItem(
        R.string.nav_track,
        Destinations.TRACK,
        Icons.Outlined.Search,
        Icons.Filled.Search
    ),
    DrawerItem(
        R.string.nav_guide,
        Destinations.GUIDE,
        Icons.AutoMirrored.Outlined.MenuBook,
        Icons.AutoMirrored.Filled.MenuBook
    ),
    DrawerItem(
        R.string.nav_faq,
        Destinations.FAQ,
        Icons.AutoMirrored.Outlined.HelpOutline,
        Icons.AutoMirrored.Filled.HelpOutline
    ),
    DrawerItem(
        R.string.nav_library,
        Destinations.LIBRARY,
        Icons.AutoMirrored.Outlined.LibraryBooks,
        Icons.AutoMirrored.Filled.LibraryBooks
    )
)

/**
 * Contenido de la barra desplegable con las secciones de la app.
 *
 * @param revealed indica si el menú está abierto. Se usa para reproducir la
 * entrada escalonada de las secciones y para animar los adornos del encabezado
 * únicamente mientras el menú está visible (así no consume recursos en reposo).
 */
@Composable
fun AppDrawerContent(
    currentRoute: String?,
    onItemClick: (String) -> Unit,
    modifier: Modifier = Modifier,
    revealed: Boolean = true
) {
    var versionClicks by remember { mutableIntStateOf(0) }
    var showCredits by remember { mutableStateOf(false) }

    ModalDrawerSheet(
        modifier = modifier,
        drawerContainerColor = Color.White
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(Brush.linearGradient(listOf(GsiAzul654, GsiAzul285)))
                .clipToBounds()
        ) {
            // Adornos de profundidad en movimiento, igual que en el encabezado principal.
            // Solo se componen con el menú abierto para no animar en segundo plano.
            if (revealed) FloatingCircles()

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 24.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(2.dp)
                ) {
                    Text(
                        text = stringResource(R.string.app_name),
                        color = Color.White,
                        fontSize = 28.sp,
                        fontWeight = FontWeight.Bold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = stringResource(R.string.drawer_subtitle),
                        color = Color.White.copy(alpha = 0.88f),
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Medium,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
                // Logotipo de la empresa, al costado derecho del título.
                Box(
                    modifier = Modifier
                        .background(Color.White, RoundedCornerShape(12.dp))
                        .padding(horizontal = 10.dp, vertical = 8.dp)
                ) {
                    AppLogo(height = 28.dp)
                }
            }
        }
        Spacer(modifier = Modifier.height(12.dp))

        drawerItems.forEachIndexed { index, item ->
            val selected = currentRoute == item.route
            val delayMillis = index * 45

            AnimatedVisibility(
                visible = revealed,
                enter = fadeIn(
                    animationSpec = tween(durationMillis = 240, delayMillis = delayMillis)
                ) + slideInHorizontally(
                    animationSpec = tween(durationMillis = 300, delayMillis = delayMillis)
                ) { full -> -full / 3 },
                exit = fadeOut(animationSpec = tween(durationMillis = 120))
            ) {
                DrawerSectionItem(
                    item = item,
                    selected = selected,
                    onClick = { onItemClick(item.route) }
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))
        HorizontalDivider(color = GsiGrisBorde)
        Text(
            text = stringResource(R.string.drawer_footer),
            color = GsiGrisTexto,
            fontSize = 12.sp,
            modifier = Modifier
                .fillMaxWidth()
                .clickable(
                    interactionSource = remember { MutableInteractionSource() },
                    indication = null,
                    onClick = {
                        versionClicks++
                        if (versionClicks >= CREDITS_TAPS) {
                            versionClicks = 0
                            showCredits = true
                        }
                    }
                )
                .padding(horizontal = 24.dp, vertical = 14.dp)
        )
    }

    if (showCredits) {
        CreditsDialog(onDismiss = { showCredits = false })
    }
}

/** Sección del menú, con su icono relleno o de contorno según el estado. */
@Composable
private fun DrawerSectionItem(
    item: DrawerItem,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val iconScale by animateFloatAsState(
        targetValue = if (selected) 1.08f else 1f,
        animationSpec = tween(durationMillis = 240),
        label = "drawerIconScale"
    )

    NavigationDrawerItem(
        label = {
            Text(
                text = stringResource(item.labelRes),
                fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium
            )
        },
        icon = {
            Icon(
                imageVector = if (selected) item.iconSelected else item.icon,
                contentDescription = null,
                modifier = Modifier.graphicsLayer {
                    scaleX = iconScale
                    scaleY = iconScale
                }
            )
        },
        selected = selected,
        onClick = onClick,
        shape = RoundedCornerShape(10.dp),
        colors = NavigationDrawerItemDefaults.colors(
            selectedContainerColor = GsiAzulClaro,
            selectedIconColor = GsiAzul654,
            selectedTextColor = GsiAzul654,
            unselectedIconColor = GsiGrisTexto,
            unselectedTextColor = GsiGrisTexto
        ),
        modifier = modifier.padding(horizontal = 12.dp, vertical = 2.dp)
    )
}

/** Número de toques sobre la versión para descubrir los créditos. */
private const val CREDITS_TAPS = 8

@Composable
private fun CreditsDialog(onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        icon = {
            Icon(
                imageVector = Icons.Filled.Star,
                contentDescription = null,
                tint = GsiAzul285
            )
        },
        title = {
            Text(
                text = stringResource(R.string.easter_egg_title),
                fontWeight = FontWeight.Bold,
                color = GsiAzul654
            )
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    text = stringResource(R.string.easter_egg_credits),
                    fontSize = 15.sp,
                    color = Color.Black
                )
                Text(
                    text = stringResource(R.string.easter_egg_studio),
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = GsiAzul285
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text(
                    text = stringResource(R.string.easter_egg_close),
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    )
}
