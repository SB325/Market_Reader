export default function RootLayout({
  children,
  data,
  containers,
}: {
  children: React.ReactNode
  data: React.ReactNode
  containers: React.ReactNode
}) {
  return (
    <html>
      <body>
        <div className="flex justify-center items-center">
          <div className="relative flex flex-col my-6 bg-white shadow-sm border border-slate-200 rounded-lg w-92">
            <div className="mx-3 mb-0 border-b border-slate-200 pt-3 pb-2 px-1">
              <span className="text-sm text-slate-600 font-medium">
                {children}
              </span>
            </div>
            <div className="w-full flex-initial mask-clip-border">{data}</div>
            <div className="w-full flex-initial mask-clip-border">{containers}</div>
          </div>
        </div>
      </body>
    </html>
  )
}