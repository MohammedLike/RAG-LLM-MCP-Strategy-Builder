import { Sun, Moon } from 'lucide-react';
import { useThemeStore } from '../../stores/themeStore';

export const ThemeToggle = () => {
  const { theme, setTheme } = useThemeStore();

  return (
    <div className="theme-switch" role="group" aria-label="Color theme">
      <button
        type="button"
        className={`theme-switch-btn ${theme === 'light' ? 'active' : ''}`}
        onClick={() => setTheme('light')}
        title="Light mode"
      >
        <Sun size={13} />
        <span>Light</span>
      </button>
      <button
        type="button"
        className={`theme-switch-btn ${theme === 'dark' ? 'active' : ''}`}
        onClick={() => setTheme('dark')}
        title="Dark mode"
      >
        <Moon size={13} />
        <span>Dark</span>
      </button>
    </div>
  );
};
