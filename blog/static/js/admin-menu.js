// Admin Menü Dinamikliği - Gelişmiş Script
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('nav a[data-menu]');
    
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
