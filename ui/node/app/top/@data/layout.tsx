export default function DataLayout({
  children,
  fundamentals,
  news,
  technicals,
}: {
  children: React.ReactNode
  fundamentals: React.ReactNode
  news: React.ReactNode
  technicals: React.ReactNode
}) {
  return (
    <html>
      <body>
        <div className="flex justify-center items-center">
          <div className="relative flex flex-col my-2 bg-white shadow-sm border border-slate-200 rounded-lg w-84">
            <div className="mx-3 mb-0 border-b border-slate-200 pt-3 pb-2 px-1">
              <span className="text-sm text-slate-600 font-medium">
                {children}
              </span>
            </div>
            <div className="w-full grid grid-cols-2 gap-2 mask-clip-border border-1 p-1.5 border-slate-200">
              <div className="w-full flex-initial mask-clip-border">{fundamentals}</div>
              <div className="w-full flex-initial mask-clip-border">{news}</div>
              <div className="w-full flex-initial mask-clip-border">{technicals}</div>
            </div>
          </div>
        </div>
      </body>
    </html>
  )
}