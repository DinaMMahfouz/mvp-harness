import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { ApplicationRegistry } from "./pages/ApplicationRegistry";
import { ApplicationForm } from "./pages/ApplicationForm";
import { ApplicationDetail } from "./pages/ApplicationDetail";
import { TestPlan } from "./pages/TestPlan";
import { RunDetail } from "./pages/RunDetail";
import { FindingsBoard } from "./pages/FindingsBoard";
import { FindingDetail } from "./pages/FindingDetail";
import { RetestComparisonPage } from "./pages/RetestComparisonPage";
import { ReleaseDecisionPage } from "./pages/ReleaseDecisionPage";
import { ReportsPage } from "./pages/ReportsPage";
import { NotFound } from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/applications" element={<ApplicationRegistry />} />
        <Route path="/applications/new" element={<ApplicationForm mode="create" />} />
        <Route path="/applications/:id/edit" element={<ApplicationForm mode="edit" />} />
        <Route path="/applications/:id" element={<ApplicationDetail />} />
        <Route path="/applications/:id/test-plan" element={<TestPlan />} />
        <Route path="/applications/:id/findings" element={<FindingsBoard />} />
        <Route path="/applications/:id/retest" element={<RetestComparisonPage />} />
        <Route path="/applications/:id/release-decision" element={<ReleaseDecisionPage />} />
        <Route path="/applications/:id/reports" element={<ReportsPage />} />
        <Route path="/runs/:id" element={<RunDetail />} />
        <Route path="/findings/:id" element={<FindingDetail />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
