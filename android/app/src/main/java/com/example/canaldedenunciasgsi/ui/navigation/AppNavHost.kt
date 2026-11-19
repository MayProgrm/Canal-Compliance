package com.example.canaldedenunciasgsi.ui.navigation

import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.canaldedenunciasgsi.R
import com.example.canaldedenunciasgsi.ui.components.AppLogo
import com.example.canaldedenunciasgsi.ui.screens.faq.FaqScreen
import com.example.canaldedenunciasgsi.ui.screens.guide.GuideScreen
import com.example.canaldedenunciasgsi.ui.screens.home.HomeScreen
import com.example.canaldedenunciasgsi.ui.screens.library.LibraryScreen
import com.example.canaldedenunciasgsi.ui.screens.report.ReportScreen
import com.example.canaldedenunciasgsi.ui.screens.report.ReportSuccessScreen
import com.example.canaldedenunciasgsi.ui.screens.track.TrackScreen
import com.example.canaldedenunciasgsi.ui.theme.GsiAzul654
import com.example.canaldedenunciasgsi.ui.theme.GsiGrisBorde
import kotlinx.coroutines.launch

/**
 * Punto único de navegación de la app.
 * Incluye la barra desplegable con las secciones y el contenedor de pantallas.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppNavHost(
    modifier: Modifier = Modifier,
    navController: NavHostController = rememberNavController()
) {
    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route ?: Destinations.HOME

    // Sección activa. Se normaliza la ruta para ignorar parámetros como el folio
    // que llega en la consulta desde el comprobante.
    val currentSection = when {
        currentRoute.startsWith(Destinations.REPORT_SUCCESS) -> Destinations.REPORT_SUCCESS
        else -> drawerItems.firstOrNull { currentRoute.startsWith(it.route) }?.route ?: currentRoute
    }

    val currentTitleRes = when (currentSection) {
        Destinations.REPORT_SUCCESS -> R.string.report_success_bar_title
        else -> drawerItems
            .firstOrNull { it.route == currentSection }
            ?.labelRes
            ?: R.string.app_name
    }

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            AppDrawerContent(
                currentRoute = currentSection,
                // Se lee el estado destino para reproducir la entrada de las
                // secciones mientras el menú se desliza, y para no animar los
                // adornos del encabezado mientras el menú está cerrado.
                revealed = drawerState.targetValue == DrawerValue.Open,
                onItemClick = { route ->
                    scope.launch { drawerState.close() }
                    if (route != currentSection) {
                        navController.navigate(route) {
                            popUpTo(Destinations.HOME) { saveState = true }
                            launchSingleTop = true
                            // La consulta siempre abre limpia desde el menú: el folio
                            // solo se precarga si se llega desde el comprobante.
                            restoreState = route != Destinations.TRACK
                        }
                    }
                }
            )
        }
    ) {
        Scaffold(
            modifier = modifier.fillMaxSize(),
            containerColor = Color.White,
            topBar = {
                Column {
                    TopAppBar(
                        title = {
                            Text(
                                text = stringResource(currentTitleRes),
                                fontWeight = FontWeight.SemiBold,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        },
                        navigationIcon = {
                            IconButton(onClick = { scope.launch { drawerState.open() } }) {
                                Icon(
                                    imageVector = Icons.Filled.Menu,
                                    contentDescription = stringResource(R.string.menu_open)
                                )
                            }
                        },
                        actions = {
                            // Logotipo de la empresa, ubicado al costado derecho.
                            AppLogo(
                                modifier = Modifier.padding(end = 12.dp),
                                height = 40.dp
                            )
                        },
                        colors = TopAppBarDefaults.topAppBarColors(
                            containerColor = Color.White,
                            titleContentColor = GsiAzul654,
                            navigationIconContentColor = GsiAzul654
                        )
                    )
                    HorizontalDivider(thickness = 1.dp, color = GsiGrisBorde)
                }
            }
        ) { innerPadding ->
            NavHost(
                navController = navController,
                startDestination = Destinations.HOME,
                modifier = Modifier.padding(innerPadding),
                enterTransition = {
                    fadeIn(animationSpec = tween(durationMillis = 220)) +
                        slideInHorizontally(animationSpec = tween(durationMillis = 260)) { full ->
                            full / 14
                        }
                },
                exitTransition = { fadeOut(animationSpec = tween(durationMillis = 150)) },
                popEnterTransition = {
                    fadeIn(animationSpec = tween(durationMillis = 220))
                },
                popExitTransition = {
                    fadeOut(animationSpec = tween(durationMillis = 150)) +
                        slideOutHorizontally(animationSpec = tween(durationMillis = 260)) { full ->
                            full / 14
                        }
                }
            ) {
                composable(Destinations.HOME) {
                    HomeScreen(
                        onReportClick = { navController.navigate(Destinations.REPORT) },
                        onTrackClick = { navController.navigate(Destinations.TRACK) }
                    )
                }
                composable(Destinations.REPORT) {
                    ReportScreen(
                        onExit = {
                            navController.navigate(Destinations.HOME) {
                                popUpTo(Destinations.HOME) { inclusive = true }
                                launchSingleTop = true
                            }
                        },
                        onSubmitted = { folio ->
                            navController.navigate(Destinations.reportSuccess(folio)) {
                                popUpTo(Destinations.REPORT) { inclusive = true }
                                launchSingleTop = true
                            }
                        }
                    )
                }
                composable(
                    route = Destinations.REPORT_SUCCESS_ROUTE,
                    arguments = listOf(
                        navArgument(Destinations.ARG_FOLIO) { type = NavType.StringType }
                    )
                ) { entry ->
                    val folio = entry.arguments?.getString(Destinations.ARG_FOLIO).orEmpty()
                    ReportSuccessScreen(
                        folio = folio,
                        onGoHome = {
                            navController.navigate(Destinations.HOME) {
                                popUpTo(Destinations.HOME) { inclusive = true }
                                launchSingleTop = true
                            }
                        },
                        onTrack = {
                            // Se envía el folio para que la consulta se autorrellene.
                            navController.navigate(Destinations.track(folio)) {
                                popUpTo(Destinations.HOME) { saveState = true }
                                launchSingleTop = true
                            }
                        }
                    )
                }
                composable(
                    route = Destinations.TRACK_ROUTE,
                    arguments = listOf(
                        navArgument(Destinations.ARG_FOLIO) {
                            type = NavType.StringType
                            nullable = true
                            defaultValue = null
                        }
                    )
                ) { entry ->
                    TrackScreen(
                        initialFolio = entry.arguments?.getString(Destinations.ARG_FOLIO).orEmpty()
                    )
                }
                composable(Destinations.GUIDE) { GuideScreen() }
                composable(Destinations.FAQ) { FaqScreen() }
                composable(Destinations.LIBRARY) { LibraryScreen() }
            }
        }
    }
}
