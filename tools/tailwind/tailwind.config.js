/* Cấu hình Tailwind cho trang đăng nhập — trích nguyên từ khối `tailwind.config` đang nhúng trong
 * templates/_dang_nhap_moi.html để CSS build ra giống hệt bản chạy bằng CDN. */
module.exports = Object.assign({
  content: ['../../templates/_dang_nhap_moi.html', '../../templates/login.html', '../../templates/khach_dang_nhap.html'],
}, {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: { sans: ['Be Vietnam Pro', 'sans-serif'] },
                    colors: {
                        brand: { 50: '#f0fdfa', 100: '#ccfbf1', 500: '#14b8a6', 600: '#0d9488', 700: '#0f766e', 800: '#115e59', 900: '#134e4a' }
                    },
                    keyframes: {
                        twinkle: { '0%, 100%': { opacity: '0.2', transform: 'scale(0.8)' }, '50%': { opacity: '1', transform: 'scale(1.2)' } },
                        bounceSlow: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-6px)' } },
                        floatElevate: { '0%, 100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-8px)' } },
                        dustFloat: { '0%': { transform: 'translate(0, 0)', opacity: '0.2' }, '50%': { opacity: '0.7' }, '100%': { transform: 'translate(25px, -35px)', opacity: '0' } }
                    },
                    animation: {
                        twinkle: 'twinkle 3s ease-in-out infinite',
                        bounceSlow: 'bounceSlow 2.5s ease-in-out infinite',
                        floatElevate: 'floatElevate 6s ease-in-out infinite',
                        dustFloat: 'dustFloat 4s linear infinite'
                    }
                }
            }
        });
