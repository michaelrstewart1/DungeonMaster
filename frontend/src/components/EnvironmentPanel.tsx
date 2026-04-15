import { useState, useEffect } from 'react';
import type { EnvironmentData } from '../types';
import { getEnvironment } from '../api/client';
import './EnvironmentPanel.css';

interface EnvironmentPanelProps {
  sessionId: string;
}

export function EnvironmentPanel({ sessionId }: EnvironmentPanelProps) {
  const [environment, setEnvironment] = useState<EnvironmentData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEnvironment = async () => {
      try {
        setIsLoading(true);
        const env = await getEnvironment(sessionId);
        setEnvironment(env);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch environment:', err);
        setError(err instanceof Error ? err.message : 'Failed to load environment');
      } finally {
        setIsLoading(false);
      }
    };

    fetchEnvironment();
    // Refresh environment every 30 seconds
    const interval = setInterval(fetchEnvironment, 30000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (error) {
    return (
      <div className="environment-panel environment-error">
        <span title={error}>⚠</span>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="environment-panel environment-loading">
        <span>Loading environment...</span>
      </div>
    );
  }

  if (!environment) {
    // Fallback: render a minimal default instead of stuck loading
    return (
      <div className="environment-panel">
        <div className="env-item time-of-day">
          <span className="env-icon">☀️</span>
          <span className="env-label">morning</span>
        </div>
        <div className="env-item weather">
          <span className="env-icon">☀️</span>
          <span className="env-label">clear</span>
        </div>
      </div>
    );
  }

  // Get icons for time of day
  const getTimeIcon = (time: string): string => {
    const icons: Record<string, string> = {
      dawn: '🌅',
      morning: '🌄',
      noon: '☀️',
      afternoon: '🌞',
      dusk: '🌆',
      evening: '🌇',
      night: '🌙',
      midnight: '🌑',
    };
    return icons[time] || '☀️';
  };

  // Get icons for weather
  const getWeatherIcon = (weather: string): string => {
    const icons: Record<string, string> = {
      clear: '☀️',
      cloudy: '☁️',
      rain: '🌧️',
      storm: '⛈️',
      snow: '❄️',
      fog: '🌫️',
      wind: '💨',
    };
    return icons[weather] || '☀️';
  };

  // Get temperature indicator
  const getTemperatureDisplay = (temp: string): string => {
    const display: Record<string, string> = {
      freezing: '❄️ Freezing',
      cold: '🥶 Cold',
      cool: '🌬️ Cool',
      mild: '🌤️ Mild',
      warm: '🔥 Warm',
      hot: '🔥🔥 Hot',
    };
    return display[temp] || 'Mild';
  };

  // Get season color
  const getSeasonClass = (season: string): string => {
    const classMap: Record<string, string> = {
      spring: 'season-spring',
      summer: 'season-summer',
      autumn: 'season-autumn',
      winter: 'season-winter',
    };
    return classMap[season] || 'season-spring';
  };

  return (
    <div className={`environment-panel ${getSeasonClass(environment.season)} weather-${environment.weather}`}>
      {/* Time of Day with icon */}
      <div className="env-item time-of-day">
        <span className="env-icon">{getTimeIcon(environment.time_of_day)}</span>
        <span className="env-label">{environment.time_of_day}</span>
      </div>

      {/* Weather with icon and animation */}
      <div className={`env-item weather weather-type-${environment.weather}`}>
        <span className="env-icon">{getWeatherIcon(environment.weather)}</span>
        <span className="env-label">{environment.weather}</span>
      </div>

      {/* Temperature */}
      <div className="env-item temperature">
        <span className="env-label">{getTemperatureDisplay(environment.temperature)}</span>
      </div>

      {/* Season indicator (discrete) */}
      <div className="env-item season" title={environment.season}>
        <span className="env-label season-abbr">
          {environment.season.substring(0, 3).toUpperCase()}
        </span>
      </div>

      {/* Weather-specific animated effects */}
      {environment.weather === 'rain' && <div className="weather-effect rain-effect" />}
      {environment.weather === 'snow' && <div className="weather-effect snow-effect" />}
      {environment.weather === 'storm' && <div className="weather-effect storm-effect" />}
    </div>
  );
}
