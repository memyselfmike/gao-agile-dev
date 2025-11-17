/**
 * TimelineFilters - Filter controls for workflow timeline
 *
 * Story 39.20: Workflow Execution Timeline
 */
import React, { useState, useEffect } from 'react';
import { useWorkflowStore } from '../../stores/workflowStore';
import { Calendar } from '../ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Button } from '../ui/button';
import { Checkbox } from '../ui/checkbox';
import { CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';

export const TimelineFilters: React.FC = () => {
  const { filters, metadata, applyFilters, clearFilters } = useWorkflowStore();

  // Local state for filter UI
  const [workflowType, setWorkflowType] = useState<string | null>(filters.workflowType);
  const [startDate, setStartDate] = useState<Date | null>(filters.startDate);
  const [endDate, setEndDate] = useState<Date | null>(filters.endDate);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>(filters.statuses);

  // Update local state when store filters change
  useEffect(() => {
    setWorkflowType(filters.workflowType);
    setStartDate(filters.startDate);
    setEndDate(filters.endDate);
    setSelectedStatuses(filters.statuses);
  }, [filters]);

  const handleWorkflowTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value || null;
    setWorkflowType(value);
    applyFilters({ workflowType: value });
  };

  const handleStartDateChange = (date: Date | undefined) => {
    const value = date || null;
    setStartDate(value);
    applyFilters({ startDate: value });
  };

  const handleEndDateChange = (date: Date | undefined) => {
    const value = date || null;
    setEndDate(value);
    applyFilters({ endDate: value });
  };

  const handleStatusToggle = (status: string) => {
    const newStatuses = selectedStatuses.includes(status)
      ? selectedStatuses.filter((s) => s !== status)
      : [...selectedStatuses, status];

    setSelectedStatuses(newStatuses);
    applyFilters({ statuses: newStatuses });
  };

  const handleClearFilters = () => {
    setWorkflowType(null);
    setStartDate(null);
    setEndDate(null);
    setSelectedStatuses([]);
    clearFilters();
  };

  const hasFilters =
    workflowType !== null ||
    startDate !== null ||
    endDate !== null ||
    selectedStatuses.length > 0;

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        {hasFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="text-sm text-gray-600"
          >
            Clear All
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {/* Workflow Type Filter */}
        <div>
          <label
            htmlFor="workflow-type"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Workflow Type
          </label>
          <select
            id="workflow-type"
            value={workflowType || ''}
            onChange={handleWorkflowTypeChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Filter by workflow type"
          >
            <option value="">All Workflows</option>
            {metadata?.workflow_types.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        {/* Date Range Filters */}
        <div className="grid grid-cols-2 gap-2">
          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-start text-left font-normal"
                  aria-label="Select start date"
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {startDate ? format(startDate, 'PPP') : 'Pick a date'}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={startDate || undefined}
                  onSelect={handleStartDateChange}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-start text-left font-normal"
                  aria-label="Select end date"
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {endDate ? format(endDate, 'PPP') : 'Pick a date'}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={endDate || undefined}
                  onSelect={handleEndDateChange}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>
        </div>

        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <div className="space-y-2">
            {metadata?.statuses.map((status) => (
              <div key={status} className="flex items-center">
                <Checkbox
                  id={`status-${status}`}
                  checked={selectedStatuses.includes(status)}
                  onCheckedChange={() => handleStatusToggle(status)}
                  aria-label={`Filter by ${status} status`}
                />
                <label
                  htmlFor={`status-${status}`}
                  className="ml-2 text-sm text-gray-700 cursor-pointer"
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
