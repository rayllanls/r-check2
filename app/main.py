"""r-check — Entry point."""
from app.gui.app import RCheckApp
from app.gui.screens.main_screen import HomeScreen
from app.gui.screens.settings_screen import SettingsScreen
from app.gui.screens.progress_screen import ProgressScreen
from app.gui.screens.results_screen import ResultsScreen


def main() -> None:
    app = RCheckApp()

    # Navigation callback — screens call this to switch
    def navigate(screen_name: str, **kwargs) -> None:
        app.show_screen(screen_name, **kwargs)

    # Create and register screens
    home = HomeScreen(app.content_frame, app=app, nav_callback=navigate)
    app.register_screen("home", home)

    settings = SettingsScreen(app.content_frame, app=app, nav_callback=navigate)
    app.register_screen("settings", settings)

    progress = ProgressScreen(app.content_frame, app=app, nav_callback=navigate)
    app.register_screen("progress", progress)

    results = ResultsScreen(app.content_frame, app=app, nav_callback=navigate)
    app.register_screen("results", results)

    app.run()


if __name__ == "__main__":
    main()
