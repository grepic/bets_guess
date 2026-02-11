export function BetCardSkeleton() {
  return (
    <div className="card p-4 sm:p-5 space-y-3 animate-pulse">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-full bg-gray-200" />
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-100 rounded w-1/2 mt-1.5" />
        </div>
        <div className="h-5 w-16 bg-gray-200 rounded-full" />
      </div>
      <div className="h-14 bg-gray-100 rounded-lg" />
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-12 bg-gray-100 rounded-lg" />
        ))}
      </div>
      <div className="h-2 bg-gray-100 rounded-full" />
    </div>
  );
}

export function BetListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-3 grid-cols-1 md:grid-cols-2">
      {[...Array(count)].map((_, i) => (
        <BetCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function GameDetailSkeleton() {
  return (
    <div className="container-narrow space-y-4 animate-pulse">
      <div className="card p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gray-200" />
          <div className="flex-1">
            <div className="h-6 bg-gray-200 rounded w-2/3" />
            <div className="h-4 bg-gray-100 rounded w-1/2 mt-2" />
          </div>
        </div>
      </div>
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-14 bg-gray-100 rounded-xl" />
      ))}
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="container-narrow space-y-4 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-48" />
      <div className="h-4 bg-gray-100 rounded w-96" />
      <div className="space-y-3 mt-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-4">
            <div className="h-5 bg-gray-200 rounded w-2/3 mb-2" />
            <div className="h-3 bg-gray-100 rounded w-1/2" />
          </div>
        ))}
      </div>
    </div>
  );
}
