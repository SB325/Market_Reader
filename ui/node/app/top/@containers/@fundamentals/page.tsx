export default function Page() {
  return (
    <div
      className="rounded-lg bg-green-400 text-left text-surface shadow-secondary-1 light:bg-surface-dark dark:text-black border border-slate-200">
      <div className="p-2">
        <h5 className="mb-1 text-xl font-medium leading-tight">
          Fundamentals
        </h5>
        <h6
          className="mb-2 text-base font-medium leading-tight text-surface/75 dark:text-neutral-300">
          Healthy
        </h6>
        <p className="mb-4 text-base leading-normal">
          Running for N Hours
        </p>
        <a
          type="button"
          href="#"
          className="pointer-events-auto me-5 inline-block cursor-pointer rounded text-base font-normal leading-normal text-primary transition duration-150 ease-in-out hover:text-primary-600 focus:text-primary-600 focus:outline-none focus:ring-0 active:text-primary-700 dark:text-primary-400">
          View Logs
        </a>
      </div>
    </div>
  )
}