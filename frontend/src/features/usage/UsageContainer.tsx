import { useEffect, useState, useCallback } from 'react';
import { UsageState } from './types';
import { fetchUsageDashboard } from './api/usageApi';
import { LoadingSpinner } from './components/LoadingSpinner';
import { UsageMetrics } from './components/UsageMetrics';

export function UsageContainer() {
  const initialState: UsageState = {
    data: null,
    loading: true,
    error: null,
  };

  const [state, setState] = useState<UsageState>(initialState);

  const fetchUsageData = useCallback(async () => {
    try {
      const data = await fetchUsageDashboard();
      setState(prev => ({
        ...prev,
        data,
        error: null,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'An error occurred while fetching usage data.',
        data: null,
      }));
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, []);

  useEffect(() => {
    setState(prev => ({ ...prev, loading: true }));
    fetchUsageData();
  }, [fetchUsageData]);

  if (state.loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 p-6">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Usage Dashboard</h2>
        {state.error && <p className="text-red-500 mt-2">{state.error}</p>}
      </div>
      <div className="flex-1 overflow-y-auto">
        {state.data ? (
          <UsageMetrics data={state.data.current_month} />
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No usage data available</p>
          </div>
        )}
      </div>
    </div>
  );
}