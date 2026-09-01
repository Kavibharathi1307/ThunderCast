import { BookOpen, CloudLightning, Database, Cpu, ShieldAlert, Info, Microscope, ArrowDown, Gauge } from 'lucide-react'
import Panel from '../components/common/Panel'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import { useAsync } from '../hooks/useAsync'
import { getModelAnalytics } from '../services/api'
import EnvironmentModeIndicator from '../components/common/EnvironmentModeIndicator'

const PIPELINE = [
  'REAL WEATHER DATA',
  'FEATURE ENGINEERING',
  'TRAINED MODEL',
  '0–6 HR NOWCAST',
  'RISK ENGINE',
  'EXPLAINABLE AI',
  'IMPACT ASSESSMENT',
  'ALERT',
]

const METRIC_KEYS: { key: string; label: string }[] = [
  { key: 'brier_score', label: 'Brier' },
  { key: 'roc_auc', label: 'ROC-AUC' },
  { key: 'precision', label: 'Precision' },
  { key: 'recall', label: 'Recall' },
  { key: 'f1', label: 'F1' },
]

const STAGES = [
  {
    title: 'Detect',
    icon: <CloudLightning />,
    description:
      'Ingest observational data and identify meteorological indicators of developing convection: temperature, humidity, pressure, atmospheric instability (CAPE, lifted index), wind shear, and existing precipitation.',
  },
  {
    title: 'Predict',
    icon: <Cpu />,
    description:
      'Generate location-specific 0–6 hour probabilistic nowcasts. The rule-based risk engine combines weighted indicators to produce thunderstorm, hail and cloudburst probabilities for each location.',
  },
  {
    title: 'Track',
    icon: <Database />,
    description:
      'Monitor the movement and evolution of detected storm cells. Cells are assigned intensity, severity, radius, movement speed and direction, and projected tracks are computed from observed motion.',
  },
  {
    title: 'Explain',
    icon: <Info />,
    description:
      'Provide human-readable explanations for every prediction and risk assessment. Each hazard probability is decomposed into its contributing meteorological factors so users understand why a risk was assigned.',
  },
  {
    title: 'Warn',
    icon: <ShieldAlert />,
    description:
      'Emit impact-based, severity-levelled alerts for affected communities and authorities. Alerts include expected impacts, affected population estimates, coverage radius, and recommended actions.',
  },
]

const RISK_LEVELS = [
  {
    level: 'LOW',
    description: 'Minimal convective hazard expected. Routine monitoring.',
    color: 'border-emerald-700 text-emerald-300',
  },
  {
    level: 'MODERATE',
    description:
      'Elevated convective potential. Some localized impact possible.',
    color: 'border-amber-700 text-amber-300',
  },
  {
    level: 'HIGH',
    description: 'Significant hazard potential. Precautions recommended.',
    color: 'border-orange-700 text-orange-300',
  },
  {
    level: 'EXTREME',
    description:
      'Severe convective threat. Take protective action and stay informed.',
    color: 'border-rose-700 text-rose-300',
  },
]

const FEATURES = [
  {
    title: 'Interactive Risk Map',
    description:
      'Geographic visualization of convective risk across India with color-coded risk cells and clickable markers. Currently renders demo risk grid data.',
  },
  {
    title: 'Storm Cell Tracking',
    description:
      'Real-time detection and tracking of convective storm cells, including intensity, severity, movement vectors and projected paths.',
  },
  {
    title: 'Explainable AI',
    description:
      'Every risk assessment is decomposed into contributing meteorological factors so the reasoning behind each prediction is transparent and auditable.',
  },
  {
    title: 'Impact-Based Alerts',
    description:
      'Warnings include expected impacts, affected population, coverage radius and recommended actions — not just severity levels.',
  },
  {
    title: '0–6 Hour Nowcast',
    description:
      'Probabilistic forecasts for thunderstorms, hail and cloudbursts across the nowcasting window, with precipitation and wind guidance.',
  },
  {
    title: 'Historical Analysis',
    description:
      'Aggregate analytics from recorded events including type breakdown, risk distribution, monthly trends and the most affected regions.',
  },
]

export default function Methodology() {
  const analytics = useAsync(() => getModelAnalytics(), [])
  const evalInfo = analytics.data?.evaluation
  const envMode = analytics.data?.environment_mode ?? 'DEMO'
  const modelStatus = analytics.data?.model_status ?? 'UNTRAINED'
  const provenance = analytics.data?.data_provenance ?? 'DEMO DATA'
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Methodology &amp; About</h1>
        <p className="mt-1 text-sm text-slate-400">
          How ThunderCast AI approaches convective nowcasting for the Smart
          India Hackathon (SIH26084).
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-xl border border-sky-800/40 bg-sky-950/20 px-4 py-3 text-sm text-sky-200/80">
        <BookOpen className="h-4 w-4 text-sky-400 shrink-0" aria-hidden="true" />
        ThunderCast AI is a conceptual MVP for convective-scale nowcasting. Unless
        a genuine labelled dataset is integrated, thunderstorm / hail / cloudburst
        predictions come from a baseline model, not learned accuracy.
      </div>

      {/* Model pipeline */}
      <Panel
        title="Model Pipeline"
        subtitle={`DATA → ${modelStatus} → NOWCAST → RISK → EXPLAIN → IMPACT → ALERT`}
      >
        <div className="grid gap-2 sm:grid-cols-4">
          {PIPELINE.map((step, i) => (
            <div
              key={step}
              className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/40 px-3 py-2.5"
            >
              <span className="text-xs font-semibold text-sky-500">{i + 1}</span>
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                {step}
              </span>
              {i < PIPELINE.length - 1 && (
                <ArrowDown className="ml-auto h-3.5 w-3.5 text-slate-600" aria-hidden="true" />
              )}
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Live real observations come from Open-Meteo (ERA5) in REAL mode; the
          threat classifier is a dependency-free logistic-regression model trained
          with chronological train/validation/test splits when a labelled dataset
          is available. Model state is always reported below.
        </p>
      </Panel>

      {/* Operational stages */}
      <Panel title="Operational Workflow" subtitle="DETECT → PREDICT → TRACK → EXPLAIN → WARN">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {STAGES.map((stage, i) => {
            const Icon = stage.icon
            return (
              <div
                key={stage.title}
                className="flex flex-col rounded-2xl border border-slate-800 bg-slate-900/40 p-5"
              >
                <span className="mb-2 text-sky-400">{Icon}</span>
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                  Step {i + 1}
                </span>
                <h3 className="mt-1 text-lg font-semibold text-sky-300">
                  {stage.title}
                </h3>
                <p className="mt-2 text-sm text-slate-400">{stage.description}</p>
              </div>
            )
          })}
        </div>
      </Panel>

      {/* Actual implementation */}
      <Panel title="Implemented Features" subtitle="What the MVP currently delivers">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5"
            >
              <h3 className="text-base font-semibold text-sky-300">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-slate-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Risk Levels" subtitle="Severity classification">
        <div className="space-y-3">
          {RISK_LEVELS.map((r) => (
            <div
              key={r.level}
              className={`flex flex-col gap-1 rounded-xl border px-4 py-3 sm:flex-row sm:items-center sm:gap-4 ${r.color}`}
            >
              <span className="text-base font-bold">{r.level}</span>
              <p className="text-sm text-slate-400">{r.description}</p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Technical Architecture" subtitle="Backend · Frontend · Database">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Database className="h-4 w-4 text-emerald-400" aria-hidden="true" />
              Backend
            </h3>
            <ul className="space-y-1 text-sm text-slate-400">
              <li>FastAPI (Python 3.11)</li>
              <li>Rule-based risk engine with explainability</li>
              <li>Resilient PyMongo connection management</li>
              <li>Pydantic-validated API contracts</li>
              <li>Comprehensive pytest suite</li>
            </ul>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Cpu className="h-4 w-4 text-sky-400" aria-hidden="true" />
              Frontend
            </h3>
            <ul className="space-y-1 text-sm text-slate-400">
              <li>React 18 + TypeScript + Vite</li>
              <li>Tailwind CSS, fully responsive</li>
              <li>Recharts data visualization</li>
              <li>Leaflet interactive geospatial maps</li>
              <li>Lazy-loaded routes for performance</li>
            </ul>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <ShieldAlert className="h-4 w-4 text-rose-400" aria-hidden="true" />
              Database
            </h3>
            <ul className="space-y-1 text-sm text-slate-400">
              <li>MongoDB Atlas (optional)</li>
              <li>Backend starts without a database</li>
              <li>Health endpoint reports DB status</li>
              <li>No hardcoded credentials</li>
              <li>Credential-free deployment ready</li>
            </ul>
          </div>
        </div>
      </Panel>

      {/* Live model analytics */}
      <Panel
        title="AI Engine Status"
        subtitle="Live baseline-model report from the backend"
        actions={
          analytics.data?.model_label ? (
            <EnvironmentModeIndicator
              mode={envMode}
              modelStatus={modelStatus}
              provenance={provenance}
            />
          ) : undefined
        }
      >
        {analytics.status === 'loading' && <LoadingState label="Loading model report…" />}
        {analytics.status === 'error' && (
          <ErrorState message={analytics.error ?? 'Model report unavailable'} onRetry={analytics.load} />
        )}
        {analytics.status === 'success' && analytics.data && (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-sky-300">
                <Microscope className="h-4 w-4" aria-hidden="true" />
                Architecture
              </h3>
              <p className="text-sm text-slate-400">{analytics.data.architecture}</p>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-0.5 text-slate-300">
                  {analytics.data.model_label}
                </span>
                <span className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-0.5 text-slate-300">
                  Data: {envMode}
                </span>
              </div>
              <div className="mt-2 space-y-1 text-xs text-slate-400">
                <div>
                  <span className="text-slate-500">Model version: </span>
                  {analytics.data.model_version || 'thundercast-baseline-0.1'}
                </div>
                <div>
                  <span className="text-slate-500">Dataset: </span>
                  {analytics.data.dataset || 'none bundled'}
                </div>
                <div>
                  <span className="text-slate-500">Targets: </span>
                  {analytics.data.targets?.length
                    ? analytics.data.targets.join(', ')
                    : 'none trained'}
                </div>
                <div>
                  <span className="text-slate-500">Unavailable targets: </span>
                  {analytics.data.unavailable_targets?.length
                    ? analytics.data.unavailable_targets.join(', ')
                    : 'none'}
                </div>
                <div>
                  <span className="text-slate-500">Features: </span>
                  {analytics.data.feature_count ?? 0}
                </div>
                <div>
                  <span className="text-slate-500">Samples (trn/val/tst): </span>
                  {analytics.data.training_samples ?? 0} /{' '}
                  {analytics.data.validation_samples ?? 0} /{' '}
                  {analytics.data.test_samples ?? 0}
                </div>
              </div>
            </div>

            {/* Genuine metrics (only present when a labelled dataset was used) */}
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-sky-300">
                <Gauge className="h-4 w-4" aria-hidden="true" />
                Genuine Validation Metrics
              </h3>
              {analytics.data.metrics && Object.keys(analytics.data.metrics).length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {Object.entries(analytics.data.metrics).map(([target, m]) => (
                    <div
                      key={target}
                      className="rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-2"
                    >
                      <div className="text-xs font-semibold uppercase text-slate-400">{target}</div>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {METRIC_KEYS.map(({ key, label }) =>
                          m[key] !== undefined && m[key] !== null ? (
                            <span
                              key={key}
                              className="rounded-full border border-slate-700 bg-slate-900 px-2 py-0.5 text-xs text-slate-300"
                            >
                              {label}: {Number(m[key]).toFixed(3)}
                            </span>
                          ) : null,
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">
                  No genuine validation metrics — no labelled dataset is bundled.
                  Figures are reported only from held-out test splits once a
                  labelled dataset is trained.
                </p>
              )}
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-sky-300">
                <ShieldAlert className="h-4 w-4" aria-hidden="true" />
                Evaluation Readiness
              </h3>
              {evalInfo && (
                <>
                  <p className="text-sm text-slate-400">{evalInfo.message}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="rounded-full border border-amber-700 bg-amber-900/30 px-2.5 py-0.5 text-xs font-semibold text-amber-300">
                      {evalInfo.status}
                    </span>
                    {evalInfo.available_metrics?.map((m) => (
                      <span
                        key={m}
                        className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-0.5 text-xs text-slate-300"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </Panel>

      <Panel
        title="Data &amp; Validation Status"
        subtitle="Honest assessment">
        <div className="rounded-xl border border-amber-800/40 bg-amber-950/20 p-4">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-amber-400">
            <Info className="h-4 w-4" aria-hidden="true" />
            Important Disclosure
          </h3>
          <p className="mt-2 text-sm text-slate-400">
            ThunderCast AI is a demonstration MVP. All data served by the API is
            synthetic, deterministic demo data explicitly labelled as such. The
            risk engine applies domain-inspired heuristics and has{' '}
            <strong>not</strong> been evaluated against real meteorological data
            or ML benchmarks. It should not be used for operational forecasting,
            emergency response, or any safety-critical decision. Production use
            would require real data ingestion, a trained and cross-validated ML
            model, and independent scientific evaluation.
          </p>
        </div>
      </Panel>

      <Panel title="Deployment" subtitle="Target architecture">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <h3 className="text-sm font-semibold text-sky-300">Frontend</h3>
            <p className="mt-1 text-sm text-slate-400">
              React build deployed to <strong>Vercel</strong>. SPA routing and
              asset caching configured via vercel.json.
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <h3 className="text-sm font-semibold text-sky-300">Backend</h3>
            <p className="mt-1 text-sm text-slate-400">
              FastAPI deployed to <strong>Render</strong> as a web service.
              Uvicorn via render.yaml. Runs even without MongoDB configured.
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
            <h3 className="text-sm font-semibold text-sky-300">Database</h3>
            <p className="mt-1 text-sm text-slate-400">
              <strong>MongoDB Atlas</strong> via MONGO_URI environment variable.
              Connection is lazy and resilient, never blocking startup.
            </p>
          </div>
        </div>
      </Panel>
    </div>
  )
}
