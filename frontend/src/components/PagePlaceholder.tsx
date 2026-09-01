interface PagePlaceholderProps {
  title: string
  description: string
  stage?: string
}

export default function PagePlaceholder({
  title,
  description,
  stage = 'Planned for a future stage',
}: PagePlaceholderProps) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 px-6 py-16 text-center">
      <div className="mb-4 text-5xl">🚧</div>
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      <p className="mt-3 max-w-xl text-slate-400">{description}</p>
      <span className="mt-6 inline-flex items-center rounded-full bg-slate-800 px-4 py-1.5 text-xs font-medium text-slate-300">
        {stage}
      </span>
    </div>
  )
}
