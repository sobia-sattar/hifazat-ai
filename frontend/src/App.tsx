import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import LivePage from "./pages/Live";
import SettingsPage from "./pages/Settings";
import TextAnalyzerPage from "./pages/TextAnalyzer";
import YoutubePage from "./pages/Youtube";
import ResultsPage from "./pages/Results";
import Moderation from "./pages/Moderation";
import ChannelScan from "./pages/ChannelScan";
import DashboardPage from "./pages/Dashboard";
import PasswordChecker from "./pages/PasswordChecker";
import ScamChecker from "./pages/ScamChecker";
import IncidentCenter from "./pages/IncidentCenter";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<DashboardPage />} />
        <Route path="/moderation" element={<Moderation />} />
        <Route path="/incidents" element={<IncidentCenter />} />
        <Route path="/analyzer" element={<TextAnalyzerPage />} />
        <Route path="/assistant" element={<Navigate to="/overview" replace />} />
        <Route path="/scam-check" element={<ScamChecker />} />
        <Route path="/password-check" element={<PasswordChecker />} />
        <Route path="/youtube" element={<ChannelScan />} />
        <Route path="/youtube/video" element={<YoutubePage />} />
        <Route path="/live" element={<LivePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/research" element={<ResultsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
