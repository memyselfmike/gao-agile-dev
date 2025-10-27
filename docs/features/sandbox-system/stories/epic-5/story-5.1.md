# Story 5.1: Report Templates (Jinja2)

**Epic**: Epic 5 - Reporting & Visualization
**Status**: Ready
**Priority**: P2 (Medium)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27

---

## User Story

**As a** developer reviewing benchmark results
**I want** well-designed Jinja2 templates for HTML reports
**So that** I can generate professional, readable reports with consistent formatting

---

## Acceptance Criteria

### AC1: Base Report Template
- [ ] `base_report.html.j2` template created
- [ ] Includes common HTML structure (head, body, navigation)
- [ ] Responsive CSS included (mobile-friendly)
- [ ] Color scheme and typography defined
- [ ] Navigation structure for multi-section reports
- [ ] Footer with generation timestamp

### AC2: Run Report Template
- [ ] `run_report.html.j2` template created
- [ ] Extends base template
- [ ] Sections: Summary, Metrics, Timeline, Quality, Artifacts
- [ ] Data tables for metrics display
- [ ] Placeholders for charts
- [ ] Status indicators (success/failure/partial)
- [ ] Collapsible sections for detailed data

### AC3: Comparison Report Template
- [ ] `comparison_report.html.j2` template created
- [ ] Extends base template
- [ ] Side-by-side run comparisons
- [ ] Difference highlighting (improvements/regressions)
- [ ] Metric delta calculations displayed
- [ ] Visual indicators for changes (arrows, colors)

### AC4: Trend Analysis Template
- [ ] `trend_report.html.j2` template created
- [ ] Extends base template
- [ ] Time-series chart placeholders
- [ ] Statistical summaries (mean, median, std dev)
- [ ] Trend indicators (improving, stable, degrading)
- [ ] Date range selector display

### AC5: Template Assets
- [ ] CSS stylesheet created (`report_styles.css`)
- [ ] Clean, professional design
- [ ] Print-friendly styles included
- [ ] Dark mode support (optional)
- [ ] JavaScript utilities for interactivity (`report.js`)
- [ ] Chart rendering helpers
- [ ] Collapsible section toggles

### AC6: Template Directory Structure
- [ ] Templates organized in `gao_dev/sandbox/reporting/templates/`
- [ ] Assets in `gao_dev/sandbox/reporting/assets/`
- [ ] README explaining template structure
- [ ] Example data files for preview

---

## Technical Details

### Implementation Approach

**Directory Structure:**
```
gao_dev/sandbox/reporting/
├── __init__.py
├── templates/
│   ├── base_report.html.j2
│   ├── run_report.html.j2
│   ├── comparison_report.html.j2
│   ├── trend_report.html.j2
│   └── partials/
│       ├── metrics_table.html.j2
│       ├── chart_container.html.j2
│       ├── status_badge.html.j2
│       └── timeline.html.j2
└── assets/
    ├── report_styles.css
    └── report.js
```

**Base Template Structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - GAO-Dev Benchmark Report</title>
    <style>
        {% include 'assets/report_styles.css' %}
    </style>
</head>
<body>
    <header>
        <h1>GAO-Dev Benchmark Report</h1>
        <nav>
            {% block navigation %}{% endblock %}
        </nav>
    </header>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>Generated: {{ generation_time }}</p>
        <p>GAO-Dev v{{ version }}</p>
    </footer>

    <script>
        {% include 'assets/report.js' %}
    </script>
</body>
</html>
```

**Run Report Sections:**
```jinja2
{% extends "base_report.html.j2" %}

{% block content %}
<section id="summary">
    <h2>Benchmark Summary</h2>
    <div class="metric-grid">
        <div class="metric">
            <span class="label">Status</span>
            <span class="value {{ run.status }}">{{ run.status }}</span>
        </div>
        <div class="metric">
            <span class="label">Duration</span>
            <span class="value">{{ run.duration_seconds }}s</span>
        </div>
        <div class="metric">
            <span class="label">Test Coverage</span>
            <span class="value">{{ run.metrics.test_coverage }}%</span>
        </div>
    </div>
</section>

<section id="metrics">
    <h2>Detailed Metrics</h2>
    {% include "partials/metrics_table.html.j2" %}
</section>

<section id="timeline">
    <h2>Execution Timeline</h2>
    {% include "partials/timeline.html.j2" %}
</section>
{% endblock %}
```

**CSS Design Principles:**
- Clean, minimal design
- Good contrast for readability
- Consistent spacing and typography
- Responsive grid layouts
- Print styles (hide navigation, optimize layout)

**JavaScript Features:**
- Collapsible section toggles
- Table sorting
- Copy-to-clipboard for metrics
- Chart interaction helpers

---

## Testing Strategy

### Unit Tests
- Template rendering with sample data
- All templates compile without errors
- All template variables resolved
- CSS validates
- JavaScript has no syntax errors

### Integration Tests
- Templates work with ReportGenerator
- Assets load correctly
- All sections render properly
- Responsive behavior verified

### Visual Tests
- Review generated HTML in browser
- Test on mobile viewport
- Verify print layout
- Check all interactive elements

### Test Coverage Goal
- 90%+ for template rendering logic
- Manual review for visual design

---

## Dependencies

### Before This Story
- None (foundational story)

### Blocks Other Stories
- Story 5.2: HTML Report Generator (needs templates)
- Story 5.3: Chart Generation (needs placeholders)

### External Dependencies
- Jinja2 library (already in dependencies)
- Modern web browser for preview

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All templates created and organized
- [ ] CSS and JavaScript assets created
- [ ] Templates render with sample data
- [ ] Code reviewed for quality
- [ ] Unit tests written and passing
- [ ] Visual review completed
- [ ] Documentation updated
- [ ] Committed to feature branch

---

## Notes

**Design Considerations:**
- Keep templates simple and maintainable
- Use semantic HTML5 elements
- Follow accessibility guidelines (WCAG)
- Minimize external dependencies (no CDN links)
- Self-contained HTML files (inline CSS/JS)

**Future Enhancements:**
- Interactive charts (Story 5.3)
- Export to PDF functionality
- Custom branding/theming support
- Real-time updates (WebSocket)

---

## References

- PRD Section: 4.4 - Reporting & Visualization
- Architecture: ReportGenerator component
- Similar Tools: pytest-html, coverage.py reports
