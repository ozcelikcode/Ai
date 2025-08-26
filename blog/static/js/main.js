/* Main JavaScript - AI Blog Platform */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    lucide.createIcons();
    
    // Enhanced Search functionality
    const searchToggleBtn = document.getElementById('search-toggle-btn');
    const searchBar = document.getElementById('search-bar');
    const navbarSearchInput = document.getElementById('navbar-search-input');
    const closeSearchBtn = document.getElementById('close-search');
    const navbarSuggestions = document.getElementById('navbar-search-suggestions');
    
    let searchTimeout;
    let isSearchOpen = false;
    
    function toggleSearch(focus = true) {
        isSearchOpen = !isSearchOpen;
        
        if (isSearchOpen) {
            searchBar.classList.remove('hidden');
            if (focus) {
                setTimeout(() => navbarSearchInput.focus(), 100);
            }
            // Add smooth slide animation
            searchBar.style.opacity = '0';
            searchBar.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                searchBar.style.transition = 'all 0.3s ease-out';
                searchBar.style.opacity = '1';
                searchBar.style.transform = 'translateY(0)';
            }, 10);
        } else {
            searchBar.style.opacity = '0';
            searchBar.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                searchBar.classList.add('hidden');
                navbarSuggestions.classList.add('hidden');
            }, 300);
        }
    }
    
    // Toggle search on button click
    if (searchToggleBtn) {
        searchToggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleSearch();
        });
    }
    
    // Close search button
    if (closeSearchBtn) {
        closeSearchBtn.addEventListener('click', function() {
            toggleSearch(false);
        });
    }
    
    // Close search when clicking outside
    document.addEventListener('click', function(e) {
        if (isSearchOpen && searchBar && !searchBar.contains(e.target) && !searchToggleBtn.contains(e.target)) {
            toggleSearch(false);
        }
    });
    
    // Prevent search bar from closing when clicking inside it
    if (searchBar) {
        searchBar.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to toggle search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            toggleSearch();
        }
        
        // Escape to close search
        if (e.key === 'Escape' && isSearchOpen) {
            toggleSearch(false);
        }
    });
    
    // Search suggestions for navbar
    if (navbarSearchInput) {
        navbarSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                if (navbarSuggestions) {
                    navbarSuggestions.classList.add('hidden');
                }
                return;
            }
            
            searchTimeout = setTimeout(async function() {
                try {
                    const response = await fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    if (data.suggestions && data.suggestions.length > 0) {
                        navbarSuggestions.innerHTML = data.suggestions.map(suggestion => `
                            <div class="p-3 hover:bg-cream-50 cursor-pointer border-b border-cream-100 last:border-b-0 transition-smooth" 
                                 onclick="selectNavbarSuggestion('${suggestion.text}')">
                                <div class="flex items-center gap-3">
                                    <i data-lucide="${suggestion.type === 'post' ? 'file-text' : 'folder'}" class="w-4 h-4 text-brown-500"></i>
                                    <span class="text-brown-900">${suggestion.text}</span>
                                    <span class="text-xs text-brown-500 ml-auto">${suggestion.type === 'post' ? 'Yazı' : 'Kategori'}</span>
                                </div>
                            </div>
                        `).join('');
                        
                        navbarSuggestions.classList.remove('hidden');
                        lucide.createIcons();
                    } else {
                        navbarSuggestions.classList.add('hidden');
                    }
                } catch (error) {
                    console.error('Suggestions error:', error);
                    if (navbarSuggestions) {
                        navbarSuggestions.classList.add('hidden');
                    }
                }
            }, 200);
        });
        
        // Hide suggestions when input loses focus (with delay for click handling)
        navbarSearchInput.addEventListener('blur', function() {
            setTimeout(() => {
                if (navbarSuggestions) {
                    navbarSuggestions.classList.add('hidden');
                }
            }, 200);
        });
    }
});

// Global functions that need to be accessible from HTML
window.selectNavbarSuggestion = function(text) {
    const navbarSearchInput = document.getElementById('navbar-search-input');
    const navbarSuggestions = document.getElementById('navbar-search-suggestions');
    
    if (navbarSearchInput) {
        navbarSearchInput.value = text;
        navbarSearchInput.form.submit();
    }
    
    if (navbarSuggestions) {
        navbarSuggestions.classList.add('hidden');
    }
};