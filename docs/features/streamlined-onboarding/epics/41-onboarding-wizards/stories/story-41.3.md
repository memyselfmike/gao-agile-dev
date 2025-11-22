# Story 41.3: Web Wizard Frontend Components

## User Story

As a first-time GAO-Dev user with a desktop browser,
I want a visual step-by-step wizard that guides me through configuration,
So that I can understand each option and complete setup with confidence.

## Acceptance Criteria

- [ ] AC1: Wizard displays progress indicator showing current step (e.g., "Step 2 of 4")
- [ ] AC2: Project step shows name input (defaulted to folder name), type indicator, optional description
- [ ] AC3: Git step shows name/email inputs with pre-filled values from global config
- [ ] AC4: Provider step displays card-based selection with icons, names, descriptions, and API key indicators
- [ ] AC5: Credentials step shows password input with show/hide toggle and environment variable option
- [ ] AC6: Completion step shows configuration summary with "Start Building" button
- [ ] AC7: All steps have "Back" button (except first) and "Continue" button
- [ ] AC8: Form validation shows inline errors with red styling
- [ ] AC9: API key validation shows loading spinner and success/error feedback
- [ ] AC10: All form fields have proper labels and are keyboard accessible
- [ ] AC11: Focus management moves to first field of each step
- [ ] AC12: Wizard meets WCAG 2.1 AA accessibility standards

## Technical Notes

### Implementation Details

Create React components in `gao_dev/web/frontend/src/components/onboarding/`:

```typescript
// OnboardingWizard.tsx
import { useState, useEffect } from 'react';

interface WizardState {
  currentStep: number;
  steps: string[];
  data: OnboardingData;
}

export function OnboardingWizard() {
  const [state, setState] = useState<WizardState>({
    currentStep: 0,
    steps: ['project', 'git', 'provider', 'credentials'],
    data: {}
  });

  // Component implementation
}

// ProjectStep.tsx
export function ProjectStep({ data, onNext, onBack }) {
  // Project configuration form
}

// GitStep.tsx
export function GitStep({ data, onNext, onBack }) {
  // Git configuration form
}

// ProviderStep.tsx
export function ProviderStep({ data, onNext, onBack }) {
  // Provider selection cards
}

// CredentialsStep.tsx
export function CredentialsStep({ data, onNext, onBack }) {
  // API key input with validation
}

// CompletionStep.tsx
export function CompletionStep({ data, onComplete }) {
  // Summary and start button
}
```

### Component Structure

```
components/onboarding/
  OnboardingWizard.tsx     # Main wizard container
  StepIndicator.tsx        # Progress indicator
  ProjectStep.tsx          # Step 1
  GitStep.tsx              # Step 2
  ProviderStep.tsx         # Step 3
  CredentialsStep.tsx      # Step 4
  CompletionStep.tsx       # Final summary
  ProviderCard.tsx         # Reusable provider card
  FormField.tsx            # Reusable form field with validation
```

### Design Specifications

#### Layout
- Centered wizard container (max-width: 600px)
- Step indicator at top
- Form content in middle
- Navigation buttons at bottom (primary right-aligned)

#### Provider Cards
- Card grid (2x2 on desktop, 1x4 on mobile)
- Provider icon (32x32)
- Provider name (bold)
- Short description
- Badge for "Requires API Key"
- Selected state with border highlight

#### Color Scheme
- Primary: Use existing GAO-Dev design system
- Error: Red (#dc3545) for validation errors
- Success: Green (#28a745) for validation success
- Warning: Yellow (#ffc107) for notes

### Accessibility Requirements

- All inputs have associated `<label>` elements
- Error messages use `aria-describedby`
- Focus trap within wizard
- Escape key closes wizard with confirmation
- Color is not sole indicator (use icons + text)
- Minimum touch target size (44x44px)

## Test Scenarios

1. **Initial render**: Given wizard mounts, When rendered, Then shows step 1 with progress indicator "Step 1 of 4"

2. **Project defaults**: Given folder name is "my-app", When project step renders, Then name input has "my-app" as default

3. **Provider selection**: Given provider step shown, When user clicks "Claude Code" card, Then card shows selected state

4. **Credential masking**: Given credentials step shown, When password typed, Then characters are masked

5. **Show/hide toggle**: Given masked password, When show toggle clicked, Then password becomes visible

6. **Validation error**: Given empty required field, When continue clicked, Then inline error shown below field

7. **API validation loading**: Given valid-looking API key, When continue clicked, Then loading spinner shown

8. **Back navigation**: Given on step 3, When back clicked, Then returns to step 2 with data preserved

9. **Keyboard navigation**: Given any step, When Tab key pressed, Then focus moves through all interactive elements

10. **Completion summary**: Given all steps complete, When completion step shown, Then displays all configured values

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests for each component (>80% coverage)
- [ ] Integration tests for wizard flow
- [ ] Accessibility audit passes (WCAG 2.1 AA)
- [ ] Responsive design tested (desktop, tablet)
- [ ] Code reviewed
- [ ] Storybook stories created for components
- [ ] Type hints complete (TypeScript strict mode)

## Story Points: 8

## Dependencies

- Story 41.2: Web Wizard Backend API (endpoints to call)
- Existing GAO-Dev design system/component library

## Notes

- Reuse existing form components where possible
- Consider using React Hook Form for form state management
- Test with screen readers (NVDA, VoiceOver)
- Provider icons should be SVGs for crisp rendering
- Consider animation between steps for polish
- Mobile responsiveness is tablet-focused (not phone)
