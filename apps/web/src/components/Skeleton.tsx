export function BetCardSkeleton() {
  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center gap-2">
        <div className="skeleton w-6 h-6 rounded-full" />
        <div className="skeleton h-4 w-48" />
      </div>
      <div className="skeleton h-12 w-full rounded-md" />
      <div className="grid grid-cols-4 gap-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="skeleton h-10 rounded" />
        ))}
      </div>
      <div className="skeleton h-2 w-full rounded-full" />
    </div>
  );
}

export function BetListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {[...Array(count)].map((_, i) => (
        <BetCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function GameDetailSkeleton() {
  return (
    <div className="space-y-4">
      <div className="skeleton h-8 w-64" />
      <div className="skeleton h-16 w-full rounded-lg" />
      {[...Array(5)].map((_, i) => (
        <div key={i} className="skeleton h-12 w-full rounded-lg" />
      ))}
    </div>
  );
}
