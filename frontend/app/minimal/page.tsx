import { SettingsProvider } from '../../contexts/SettingsContext';
import { LanguageProvider } from '../../contexts/LanguageContext';
import MinimalHomePage from '../minimal-page';

export default function MinimalPage() {
  return (
    <SettingsProvider>
      <LanguageProvider>
        <MinimalHomePage />
      </LanguageProvider>
    </SettingsProvider>
  );
}