/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/features/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Haven 温暖配色系统
        haven: {
          bg: '#FBF7F0',       // 暖白米 - 页面背景
          card: '#FFFFFF',     // 纯白 - 卡片/输入框
          primary: '#E8A87C',  // 柔和橘 - 主强调
          secondary: '#C38D9E',// 柔粉紫 - 完成态/次要强调
          text: '#3D3D3D',     // 主文字
          muted: '#8B8B8B',    // 辅助文字
          success: '#85B79D',  // 薄荷绿 - 成功态
        },
      },
      fontFamily: {
        sans: ['"PingFang SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '16px',
        'xl': '12px',
      },
    },
  },
  plugins: [],
};
