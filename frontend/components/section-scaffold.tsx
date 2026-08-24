export function SectionScaffold({ title, note }: { title: string; note: string }) {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <div className="mt-6 rounded-lg border border-dashed border-neutral-300 dark:border-neutral-700 p-10 text-center">
        <p className="text-sm text-neutral-500">{note}</p>
      </div>
    </main>
  );
}
