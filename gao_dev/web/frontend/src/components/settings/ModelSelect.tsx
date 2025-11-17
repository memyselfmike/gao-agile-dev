/**
 * Model Select - Dropdown for selecting model within provider
 *
 * Story 39.28: Provider Selection Settings Panel
 */
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import type { Model } from '@/types/settings';

interface ModelSelectProps {
  models: Model[];
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function ModelSelect({
  models,
  value,
  onChange,
  disabled = false,
}: ModelSelectProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="model" className="text-sm font-medium">
        Model
      </Label>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger id="model" className="w-full">
          <SelectValue placeholder="Select model" />
        </SelectTrigger>
        <SelectContent>
          {models.length === 0 ? (
            <div className="p-2 text-sm text-muted-foreground">
              No models available
            </div>
          ) : (
            models.map((model) => (
              <SelectItem key={model.id} value={model.id}>
                <div className="flex flex-col">
                  <span className="font-medium">{model.name}</span>
                  {model.description && (
                    <span className="text-xs text-muted-foreground">
                      {model.description}
                    </span>
                  )}
                </div>
              </SelectItem>
            ))
          )}
        </SelectContent>
      </Select>
    </div>
  );
}
