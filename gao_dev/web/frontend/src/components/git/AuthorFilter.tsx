/**
 * AuthorFilter - Dropdown for filtering commits by author
 *
 * Options:
 * - All (no filter)
 * - Agents only (all GAO-Dev agents)
 * - User only (non-agent commits)
 * - Individual agents (Brian, John, Winston, Sally, Bob, Amelia, Murat, Mary)
 */
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { User } from 'lucide-react';

interface AuthorFilterProps {
  value: string;
  onChange: (value: string) => void;
}

export function AuthorFilter({ value, onChange }: AuthorFilterProps) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[200px]">
        <User className="h-4 w-4 mr-2" />
        <SelectValue placeholder="Filter by author" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Filter Options</SelectLabel>
          <SelectItem value="all">All Authors</SelectItem>
          <SelectItem value="agents">Agents Only</SelectItem>
          <SelectItem value="user">User Only</SelectItem>
        </SelectGroup>

        <SelectSeparator />

        <SelectGroup>
          <SelectLabel>Individual Agents</SelectLabel>
          <SelectItem value="brian">Brian (Workflow Coordinator)</SelectItem>
          <SelectItem value="john">John (Product Manager)</SelectItem>
          <SelectItem value="winston">Winston (Architect)</SelectItem>
          <SelectItem value="sally">Sally (UX Designer)</SelectItem>
          <SelectItem value="bob">Bob (Scrum Master)</SelectItem>
          <SelectItem value="amelia">Amelia (Developer)</SelectItem>
          <SelectItem value="murat">Murat (Test Architect)</SelectItem>
          <SelectItem value="mary">Mary (Business Analyst)</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
