// Admin Menü Dinamikliği - Gelişmiş Script
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin menu script loaded');
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('nav a[data-menu], nav button[data-menu]');
    
    // Menü durumları
    const menuStates = {
        default: {
            classes: ['text-cream-200', 'hover:bg-brown-700', 'hover:text-white'],
            remove: ['text-cream-100', 'bg-brown-700']
        },
        active: {
            classes: ['text-cream-100', 'bg-brown-700'],
            remove: ['text-cream-200', 'hover:bg-brown-700', 'hover:text-white']
        }
    };
    
    // Menü eşleştirme kuralları
    const menuMatching = {
        '/admin': 'dashboard',
        '/admin/posts': 'posts',
        '/admin/posts/new': 'posts-new',
        '/admin/posts/': 'posts', // posts alt sayfaları için
        '/admin/pages': 'pages',
        '/admin/categories': 'categories',
        '/admin/tags': 'tags',
        '/admin/media': 'media',
        '/admin/comments': 'comments',
        '/admin/settings': 'settings'
    };
    
    // Aktif menüyü belirle
    function getActiveMenu(path) {
        // Tam eşleşme kontrolü
        if (menuMatching[path]) {
            return menuMatching[path];
        }
        
        // Kısmi eşleşme kontrolü (alt sayfalar için)
        for (const [route, menuId] of Object.entries(menuMatching)) {
            if (route !== '/admin' && path.startsWith(route + '/')) {
                return menuId;
            }
        }
        
        return 'dashboard'; // Varsayılan
    }
    
    // Menü durumlarını güncelle
    function updateMenuStates() {
        const activeMenuId = getActiveMenu(currentPath);
        
        menuItems.forEach(item => {
            const menuId = item.getAttribute('data-menu');
            const isActive = menuId === activeMenuId;
            
            // Sınıfları temizle
            const state = isActive ? menuStates.active : menuStates.default;
            item.classList.remove(...state.remove);
            item.classList.add(...state.classes);
            
            // Parent menü aktivasyonu (alt menüler için)
            if (isActive && menuId.includes('-')) {
                const parentMenuId = menuId.split('-')[0];
                const parentItem = document.querySelector(`nav a[data-menu="${parentMenuId}"]`);
                if (parentItem && parentItem !== item) {
                    parentItem.classList.remove(...menuStates.default.remove);
                    parentItem.classList.add('text-cream-100', 'bg-brown-600'); // Farklı renk ton
                }
            }
        });
    }
    
    // İlk yüklemede menüyü güncelle
    updateMenuStates();
    
    // Dinamik menü güncellemesi için event listener (SPA uygulamaları için)
    window.addEventListener('popstate', updateMenuStates);
    
    // Hover efektleri için additional listeners
    menuItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            if (!this.classList.contains('bg-brown-700')) {
                this.classList.add('bg-brown-600');
            }
        });
        
        item.addEventListener('mouseleave', function() {
            if (!this.classList.contains('bg-brown-700')) {
                this.classList.remove('bg-brown-600');
            }
        });
    });
});

// Dropdown menü işlevselliği - Basit ve debug'lanabilir
window.toggleDropdown = function(event, dropdownId) {
    console.log('toggleDropdown called with:', dropdownId);
    
    event.preventDefault();
    event.stopPropagation();
    
    const dropdown = document.getElementById(dropdownId);
    const toggle = event.currentTarget;
    
    console.log('Dropdown element:', dropdown);
    console.log('Toggle element:', toggle);
    
    if (!dropdown) {
        console.error('Dropdown not found:', dropdownId);
        return;
    }
    
    // Diğer tüm dropdown'ları kapat
    const allDropdowns = document.querySelectorAll('.dropdown-menu');
    const allToggles = document.querySelectorAll('.dropdown-toggle');
    
    console.log('Found dropdowns:', allDropdowns.length);
    console.log('Found toggles:', allToggles.length);
    
    allDropdowns.forEach(dd => {
        if (dd !== dropdown) {
            dd.classList.remove('open');
            console.log('Closed dropdown:', dd.id);
        }
    });
    
    allToggles.forEach(dt => {
        if (dt !== toggle) {
            dt.classList.remove('open');
        }
    });
    
    // Mevcut dropdown'ı aç/kapat
    const isOpen = dropdown.classList.contains('open');
    if (isOpen) {
        dropdown.classList.remove('open');
        toggle.classList.remove('open');
        console.log('Dropdown closed:', dropdownId);
    } else {
        dropdown.classList.add('open');
        toggle.classList.add('open');
        console.log('Dropdown opened:', dropdownId);
    }
};

// Sayfa dışında tıklandığında dropdown'ları kapat
document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown-toggle') && !event.target.closest('.dropdown-menu')) {
        const allDropdowns = document.querySelectorAll('.dropdown-menu');
        const allToggles = document.querySelectorAll('.dropdown-toggle');
        
        allDropdowns.forEach(dd => dd.classList.remove('open'));
        allToggles.forEach(dt => dt.classList.remove('open'));
    }
});

// Dropdown menü içindeki linklere tıklandığında dropdown'ları kapat
document.addEventListener('DOMContentLoaded', function() {
    const dropdownLinks = document.querySelectorAll('.dropdown-menu a');
    
    dropdownLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Dropdown'ları kapat
            const allDropdowns = document.querySelectorAll('.dropdown-menu');
            const allToggles = document.querySelectorAll('.dropdown-toggle');
            
            allDropdowns.forEach(dd => dd.classList.remove('open'));
            allToggles.forEach(dt => dt.classList.remove('open'));
        });
    });
});
