class ThemePreviewer:
    @staticmethod
    def generate_theme_preview(theme):
        """Generate SVG preview for a theme"""
        def rgb_dict_to_string(rgb_dict):
            r = int(rgb_dict['red'] * 255)
            g = int(rgb_dict['green'] * 255)
            b = int(rgb_dict['blue'] * 255)
            return f"rgb({r},{g},{b})"
        
        background = rgb_dict_to_string(theme['background_color'])
        primary = rgb_dict_to_string(theme['primary_color'])
        secondary = rgb_dict_to_string(theme.get('secondary_color', theme['primary_color']))
        accent = rgb_dict_to_string(theme.get('accent_color', theme['primary_color']))
        
        gradient = ""
        if 'gradient_color' in theme:
            gradient_color = rgb_dict_to_string(theme['gradient_color'])
            gradient = f"""
                <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{background};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{gradient_color};stop-opacity:1" />
                    </linearGradient>
                </defs>
                <rect width="200" height="150" fill="url(#grad)" />
            """
        else:
            gradient = f'<rect width="200" height="150" fill="{background}" />'
        
        return f"""
        <svg viewBox="0 0 200 150" xmlns="http://www.w3.org/2000/svg">
            {gradient}
            
            <!-- Title bar -->
            <rect x="20" y="20" width="160" height="30" fill="{primary}" opacity="0.9" />
            
            <!-- Content blocks -->
            <rect x="20" y="60" width="70" height="70" fill="{secondary}" opacity="0.7" />
            <rect x="100" y="60" width="80" height="70" fill="{accent}" opacity="0.7" />
            
            <!-- Text lines representation -->
            <rect x="30" y="25" width="80" height="4" fill="white" opacity="0.9" />
            <rect x="30" y="70" width="50" height="2" fill="white" opacity="0.8" />
            <rect x="30" y="80" width="40" height="2" fill="white" opacity="0.8" />
            <rect x="110" y="70" width="60" height="2" fill="white" opacity="0.8" />
            <rect x="110" y="80" width="50" height="2" fill="white" opacity="0.8" />
        </svg>
        """