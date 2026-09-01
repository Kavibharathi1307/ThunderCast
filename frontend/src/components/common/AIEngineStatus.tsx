import { Cpu, Gauge, Database, FlaskConical, Info, Layers } from 'lucide-react'
import { getModelAnalytics } from '../../services/api'
import { useAsync } from '../../hooks/useAsync'
import LoadingState from '../common/LoadingState'
import type { ModelAnalyticsResponse } from '../../types/api'

/**
 * Truthful AI engine report.
 *
 * The backend reports model_status=UNTRAINED, environment_mode=DEMO and
 * evaluation=dataset_required during normal Stage-1 operation. Even when the
 * model analytics endpoint is unreachable, the UI still shows that honest
 * prototype state (rather than a scary 401/raw error) and explains it.
 */

const DEFAULT_STATE: Pick<
  ModelAnalyticsResponse,
  'model_label' | 'model_version' | 'model_status' | 'environment_mode' | 'evaluation' | 'targets' | 'feature_count'
> = {
  model_label: 'BASELINE MODEL',
  model_version: 'thundercast-baseline-0.1',
  model_status: 'UNTRAINED',
  environment_mode: 'DEMO',
  evaluation: {
    status: 'dataset_required',
    message:
      'Model evaluation requires labelled meteorological observations. No real dataset is bundled, so no evaluation scores are reported.',
    n_samples: 0,
    available_metrics: [
      'brier_score',
      'accuracy',
      'precision',
      'recall',
      'f1',
      'roc_auc',
    ],
  },
  targets: [],
  feature_count: 12,
}

export default function AIEngineStatus() {
  const state = useAsync(() => getModelAnalytics(), [])
  const model = state.data ?? null

  const status = model?.model_status ?? DEFAULT_STATE.model_status
  const envMode = model?.environment_mode ?? DEFAULT_STATE.environment_mode
  const evalStatus = model?.evaluation?.status ?? DEFAULT_STATE.evaluation.status
  const reached = state.status === 'success'

  if (state.status === 'loading') {
    return (
      <div className="flex items-center justify-center py-6">
        <LoadingState label="Checking AI engine status…" />
      </div>
    )
  }

  const modelLabel = model?.model_label ?? DEFAULT_STATE.model_label
  const modelVersion = model?.model_version ?? DEFAULT_STATE.model_version
  const targets = model?.targets ?? DEFAULT_STATE.targets
  const unavailableTargets = model?.unavailable_targets ?? []
  const featureCount = model?.feature_count ?? DEFAULT_STATE.feature_count

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-sky-500/10">
          <Cpu className="h-4 w-4 text-sky-400" aria-hidden="true" />
        </div>
        <span className="text-sm font-semibold text-slate-100">{modelLabel}</span>
        <span
          className={`ml-auto inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
            status === 'TRAINED'
              ? 'border-emerald-700 bg-emerald-950/50 text-emerald-300'
              : 'border-amber-700 bg-amber-950/50 text-amber-300'
          }`}
        >
          {status}
        </span>
      </div>

      <dl className="grid grid-cols-3 gap-2">
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <dt className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            <Gauge className="h-3 w-3" aria-hidden="true" /> Status
          </dt>
          <dd
            className={`mt-1 font-mono text-sm font-bold ${
              status === 'TRAINED' ? 'text-emerald-300' : 'text-amber-300'
            }`}
          >
            {status}
          </dd>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <dt className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            <Database className="h-3 w-3" aria-hidden="true" /> Mode
          </dt>
          <dd className="mt-1 font-mono text-sm font-bold text-slate-200">
            {envMode}
          </dd>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <dt className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            <FlaskConical className="h-3 w-3" aria-hidden="true" /> Evaluation
          </dt>
          <dd className="mt-1 font-mono text-sm font-bold capitalize text-slate-200">
            {evalStatus.replace(/_/g, ' ')}
          </dd>
        </div>
      </dl>

      {status !== 'TRAINED' && (
        <div className="rounded-lg border border-sky-800/40 bg-sky-950/20 p-3 text-xs">
          <p className="font-semibold uppercase tracking-wide text-sky-300">
            AI model not trained
          </p>
          <p className="mt-1 leading-relaxed text-slate-400">
            The ML model has not been trained yet. Demo intelligence is
            currently being used for all risk calculations.
          </p>
          <p className="mt-1 leading-relaxed text-slate-500">
            {model?.evaluation?.message ?? DEFAULT_STATE.evaluation.message}
          </p>
        </div>
      )}

      {status === 'TRAINED' && (
        <div className="rounded-lg border border-emerald-800/40 bg-emerald-950/20 p-3 text-xs">
          <p className="font-semibold uppercase tracking-wide text-emerald-300">
            AI model trained
          </p>
          <p className="mt-1 text-slate-400">
            {model?.evaluation?.message ??
              'Trained model active with documented evaluation metrics.'}
          </p>
        </div>
      )}

      <div className="flex flex-wrap items-start gap-x-4 gap-y-1.5 text-[11px] text-slate-500">
        <span className="flex items-center gap-1.5">
          <Info className="h-3 w-3" aria-hidden="true" />
          Version {modelVersion}
        </span>
        <span className="flex items-center gap-1.5">
          <Layers className="h-3 w-3" aria-hidden="true" />
          {featureCount} features
        </span>
        {targets.length > 0 ? (
          <span>Targets trained: {targets.join(', ')}</span>
        ) : unavailableTargets.length > 0 ? (
          <span>Untrained targets: {unavailableTargets.join(', ')}</span>
        ) : null}
      </div>

      {!reached && (
        <p className="rounded-lg border border-amber-800/40 bg-amber-950/20 p-3 text-[11px] text-amber-200/90">
          The model analytics service could not be reached — ThunderCast is
          reporting its standard prototype state (UNTRAINED · DEMO ·
          dataset_required).
        </p>
      )}
    </div>
  )
}