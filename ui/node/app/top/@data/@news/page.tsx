export default function Page() {
  return (
    <div className="flex flex-col rounded-lg bg-white shadow-sm max-w-96 p-6 my-2 border border-slate-200">
      <div className="pb-2 m-0 mb-4 text-center text-slate-800 border-b border-slate-200">
        <p className="text-sm uppercase font-semibold text-slate-500">
          News
        </p>
        <h1 className="flex justify-center gap-1 mt-4 font-bold text-slate-800 text-6xl">
          <span className="self-end text-4xl">20</span>
          <span className="self-end text-sm">M</span>
        </h1>
      </div>
      <div className="p-0">
        <button className="min-w-16 w-full rounded-md bg-slate-800 py-2 px-4 border border-transparent text-center text-sm text-white transition-all shadow-md hover:shadow-lg focus:bg-slate-700 focus:shadow-none active:bg-slate-700 hover:bg-slate-700 active:shadow-none disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none" type="button">
          Refresh
        </button>
      </div>
    </div> 
  )
}