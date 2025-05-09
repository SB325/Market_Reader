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
    <html lang="en">
      <body>
        {children}
        {data}
        {containers}
      </body>
    </html>
  )
}