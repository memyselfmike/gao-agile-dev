// GAO-Dev Benchmark Report JavaScript

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    initializeCollapsibleSections();
    initializeTableSorting();
    initializeCopyButtons();
    initializeNavigation();
});

/**
 * Initialize collapsible sections
 */
function initializeCollapsibleSections() {
    const collapsibles = document.querySelectorAll('.collapsible');

    collapsibles.forEach(function(element) {
        element.addEventListener('click', function() {
            this.classList.toggle('collapsed');

            const content = this.nextElementSibling;
            if (content && content.classList.contains('collapsible-content')) {
                content.classList.toggle('collapsed');
            }
        });
    });
}

/**
 * Initialize table sorting
 */
function initializeTableSorting() {
    const tables = document.querySelectorAll('table.sortable');

    tables.forEach(function(table) {
        const headers = table.querySelectorAll('th');

        headers.forEach(function(header, index) {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // Determine sort direction
    const currentSort = table.dataset.sortColumn;
    const currentDir = table.dataset.sortDir || 'asc';
    const newDir = (currentSort == columnIndex && currentDir === 'asc') ? 'desc' : 'asc';

    // Sort rows
    rows.sort(function(a, b) {
        const aCell = a.cells[columnIndex].textContent.trim();
        const bCell = b.cells[columnIndex].textContent.trim();

        // Try to parse as number
        const aNum = parseFloat(aCell);
        const bNum = parseFloat(bCell);

        let comparison = 0;
        if (!isNaN(aNum) && !isNaN(bNum)) {
            comparison = aNum - bNum;
        } else {
            comparison = aCell.localeCompare(bCell);
        }

        return newDir === 'asc' ? comparison : -comparison;
    });

    // Re-append rows in sorted order
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });

    // Update sort state
    table.dataset.sortColumn = columnIndex;
    table.dataset.sortDir = newDir;

    // Update header indicators
    const headers = table.querySelectorAll('th');
    headers.forEach(function(header, index) {
        header.classList.remove('sort-asc', 'sort-desc');
        if (index === columnIndex) {
            header.classList.add('sort-' + newDir);
        }
    });
}

/**
 * Initialize copy-to-clipboard buttons
 */
function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-button');

    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const target = document.getElementById(targetId);

            if (target) {
                const text = target.textContent || target.value;
                copyToClipboard(text);

                // Visual feedback
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                setTimeout(function() {
                    button.textContent = originalText;
                }, 2000);
            }
        });
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
}

/**
 * Initialize smooth scrolling navigation
 */
function initializeNavigation() {
    const navLinks = document.querySelectorAll('nav a[href^="#"]');

    navLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);

            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Update active nav item
                navLinks.forEach(function(navLink) {
                    navLink.classList.remove('active');
                });
                this.classList.add('active');
            }
        });
    });

    // Highlight active section on scroll
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section[id]');
        let currentSection = '';

        sections.forEach(function(section) {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;

            if (pageYOffset >= sectionTop - 100) {
                currentSection = section.getAttribute('id');
            }
        });

        navLinks.forEach(function(link) {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + currentSection) {
                link.classList.add('active');
            }
        });
    });
}

/**
 * Format duration for display
 */
function formatDuration(seconds) {
    if (seconds < 60) {
        return seconds.toFixed(1) + 's';
    } else if (seconds < 3600) {
        const minutes = seconds / 60;
        return minutes.toFixed(1) + 'm';
    } else {
        const hours = seconds / 3600;
        return hours.toFixed(1) + 'h';
    }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

/**
 * Expand all collapsible sections
 */
function expandAll() {
    const collapsibles = document.querySelectorAll('.collapsible');
    const contents = document.querySelectorAll('.collapsible-content');

    collapsibles.forEach(function(element) {
        element.classList.remove('collapsed');
    });

    contents.forEach(function(element) {
        element.classList.remove('collapsed');
    });
}

/**
 * Collapse all collapsible sections
 */
function collapseAll() {
    const collapsibles = document.querySelectorAll('.collapsible');
    const contents = document.querySelectorAll('.collapsible-content');

    collapsibles.forEach(function(element) {
        element.classList.add('collapsed');
    });

    contents.forEach(function(element) {
        element.classList.add('collapsed');
    });
}

// Export functions for use in templates
window.gaoReport = {
    expandAll: expandAll,
    collapseAll: collapseAll,
    formatDuration: formatDuration,
    formatTimestamp: formatTimestamp
};
